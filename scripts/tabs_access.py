"""Private archive access: signed sessions and explicitly trusted network paths."""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import threading
import time
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
from urllib.request import urlopen

_attempts = {}
_lock = threading.Lock()
_viewer = None


def config():
    try:
        return json.loads(Path(os.environ.get('TABS_ACCESS_CONFIG', '/home/vex/tabs-host/access.json')).read_text())
    except (OSError, ValueError):
        return None


def trusted_network(handler, settings):
    peer = handler.client_address[0]
    proxies = settings.get('trusted_proxies', [])
    # Never mistake the public reverse proxy's tailnet address for an end user.
    if peer in proxies:
        client = handler.headers.get('X-Real-IP', '')
        return client in settings.get('home_ips', []) or any_ip(client, settings.get('home_networks', []))
    try:
        address = ipaddress.ip_address(peer)
        if address.is_loopback and handler.headers.get('Tailscale-User-Login'):
            return True  # Identity headers are trusted only from local tailscale serve.
        # Deployment binds the published port to the Tailscale IP only.
        if any_ip(peer, settings.get('tailnet_networks', [])):
            return True
    except ValueError:
        return False
    return peer in settings.get('home_ips', []) or any_ip(peer, settings.get('home_networks', []))


def any_ip(value, networks):
    try:
        return any(ipaddress.ip_address(value) in ipaddress.ip_network(n) for n in networks)
    except ValueError:
        return False


def signature(body, settings):
    return hmac.new(bytes.fromhex(settings['session_key']), body.encode(), hashlib.sha256).hexdigest()


def accounts(settings):
    """Keep the original account and its sessions valid when adding named users."""
    users = dict(settings.get('users', {}))
    if settings.get('username'):
        users.setdefault(settings['username'], settings)
    return users


def password_matches(password, account):
    if account.get('algorithm') == 'bcrypt':
        import bcrypt
        return bcrypt.checkpw(password.encode(), account['password_hash'].encode())
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(account['salt']), 260000).hex()
    return hmac.compare_digest(digest, account['password_hash'])


def principal(handler):
    """Only a verified signed account session identifies personal state."""
    settings = config()
    if not settings:
        return None
    try:
        cookies = SimpleCookie(handler.headers.get('Cookie', ''))
        body, digest = cookies['rt_tabs_session'].value.rsplit('.', 1)
        username, expiry = base64.urlsafe_b64decode(body + '=' * (-len(body) % 4)).decode().split('|')
        if username in accounts(settings) and time.time() < int(expiry) and hmac.compare_digest(signature(body, settings), digest):
            return username
    except (ValueError, KeyError, TypeError, CookieError, UnicodeError):
        pass
    return None


def authorized(handler):
    settings = config()
    return bool(settings and (principal(handler) is not None or trusted_network(handler, settings)))


def login(handler):
    settings = config()
    if not settings:
        return handler.send_json(503, {'error': 'Private access is not configured.'})
    origin = handler.headers.get('Origin')
    if origin and origin not in settings.get('origins', []):
        return handler.send_json(403, {'error': 'Origin is not allowed.'})
    now = time.monotonic()
    # Throttle by peer. The reverse proxy shares a bucket; this is deliberate.
    peer = handler.client_address[0]
    with _lock:
        recent = [t for t in _attempts.get(peer, []) if now - t < 60]
        if len(recent) >= 12:
            return handler.send_json(429, {'error': 'Try again in a minute.'})
        if len(_attempts) > 1000:
            _attempts.clear()
        _attempts[peer] = recent + [now]
    try:
        length = int(handler.headers.get('Content-Length', '0'))
        if not 0 < length <= 2048:
            raise ValueError()
        data = json.loads(handler.rfile.read(length))
        username, password = data.get('username', ''), data.get('password', '')
        if not isinstance(username, str) or not isinstance(password, str) or len(password) > 512:
            raise ValueError()
        account = accounts(settings).get(username)
        # Unknown users still perform password work, without accepting a fallback account.
        valid = password_matches(password, account or settings) and account is not None
    except (ValueError, TypeError, AttributeError, KeyError):
        valid = False
    if not valid:
        return handler.send_json(401, {'error': 'Incorrect username or password.'})
    body = base64.urlsafe_b64encode((username + '|' + str(int(time.time()) + 2592000)).encode()).decode().rstrip('=')
    token = body + '.' + signature(body, settings)
    payload = b'{"authenticated":true}'
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('Content-Length', str(len(payload)))
    handler.send_header('Set-Cookie', 'rt_tabs_session=' + token + '; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax')
    handler.end_headers()
    handler.wfile.write(payload)


def serve_private_viewer(handler):
    global _viewer
    try:
        if not _viewer or time.monotonic() - _viewer[0] > 60:
            with urlopen('https://retroterminal.net/tabs/', timeout=15) as response:
                html = response.read(1024 * 1024).decode()
            html = html.replace('<head>', '<head><base href="https://retroterminal.net/">', 1)
            # Same-origin archive access when entered through the tailnet endpoint.
            html = html.replace('"https://tabs.retroterminal.net', '"')
            _viewer = (time.monotonic(), html.encode())
        data = _viewer[1]
        handler.send_response(200)
        handler.send_header('Content-Type', 'text/html; charset=utf-8')
        handler.send_header('Cache-Control', 'private, no-store')
        handler.send_header('Content-Length', str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)
    except OSError:
        handler.send_json(502, {'error': 'Unable to load the player. Try again.'})

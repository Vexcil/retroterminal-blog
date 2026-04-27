# Tabs Hosting

This keeps the tab viewer UI in the GitHub/Jekyll site while moving the archive and generated index onto this server.

## Layout

- `retroterminal.net/tabs/`: existing Jekyll viewer page
- `tabs.retroterminal.net/data/tabs.json`: hosted index JSON
- `tabs.retroterminal.net/files/...`: hosted tab files
- this server: archive copy, JSON generation, lightweight tabs host service on port `4080`
- `vex-pi`: nginx reverse proxy for the public subdomain

## What Changed

- `tabs.md` now prefers `https://tabs.retroterminal.net/data/tabs.json`
- if the subdomain is unavailable, it falls back to the in-repo `assets/data/tabs.json`
- the header `Tabs` link is now configurable with `tabs_nav_url`
- `build_tab_index.py` can build either local or hosted URLs
- `scripts/tabs_host_server.py` serves `/data/tabs.json` and `/files/...` from this server
- uploads to `https://tabs.retroterminal.net/upload` are accepted and auto-indexed

## Local Paths

- archive copy: `/home/vex/tabs-archive`
- hosted JSON: `/home/vex/tabs-host/data/tabs.json`
- repo: `/home/vex/retroterminal-blog`
- local tabs host: `http://THIS-SERVER:4080`

## Initial Seed

Before The-MainFrame comes online, you can seed the hosted JSON from the repo copy:

```bash
cd /home/vex/retroterminal-blog
TABS_SOURCE_DIR=/home/vex/retroterminal-blog/assets/tabs ./scripts/build_tabs_host.sh
```

If you want to start using a dedicated local archive immediately:

```bash
mkdir -p /home/vex/tabs-archive
rsync -a /home/vex/retroterminal-blog/assets/tabs/ /home/vex/tabs-archive/
cd /home/vex/retroterminal-blog
./scripts/build_tabs_host.sh
```

## MainFrame Sync

1. Copy the example env file:

```bash
cp /home/vex/retroterminal-blog/deploy/tabs-sync.env.example /home/vex/retroterminal-blog/deploy/tabs-sync.env
```

2. Set `MAINFRAME_TABS_PATH` once The-MainFrame is online and you know the working rsync path.

3. Run:

```bash
cd /home/vex/retroterminal-blog
./scripts/sync_tabs_from_mainframe.sh
```

That will:

- pull the archive from The-MainFrame into `/home/vex/tabs-archive`
- rebuild `/home/vex/tabs-host/data/tabs.json`

## Local Host Service

Install the service on this server:

```bash
sudo cp /home/vex/retroterminal-blog/deploy/tabs-host.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tabs-host.service
sudo systemctl status tabs-host.service
```

Quick manual test without systemd:

```bash
cd /home/vex/retroterminal-blog
python3 ./scripts/tabs_host_server.py --host 0.0.0.0 --port 4080
```

## Uploads

- upload endpoint: `POST /upload`
- accepted extensions: `.gp`, `.gp3`, `.gp4`, `.gp5`, `.gpx`, `.musicxml`, `.xml`, `.capx`
- max upload size: `25 MB`
- files are stored under `/home/vex/tabs-archive/uploads`
- the index is rebuilt automatically after a successful upload

Validation is intentionally basic but strict enough to reject obvious junk:

- Guitar Pro binary files must match an expected header signature
- zip-based formats must be valid zip containers
- XML-based formats must parse as XML and may not contain `DOCTYPE` or `ENTITY`

Auth is not enabled yet. If you want to lock this down later, nginx basic auth is the simplest next step.

## nginx On `vex-pi`

Install `deploy/tabs.retroterminal.net.nginx.conf` on `vex-pi`. It reverse proxies to this server at `100.112.11.1:4080`, which matches the existing `vex-ser` Tailscale host entry. If you want to use LAN instead, replace that address before installing the config.

Suggested steps on `vex-pi`:

```bash
sudo cp tabs.retroterminal.net.nginx.conf /etc/nginx/sites-available/tabs.retroterminal.net.conf
sudo ln -s /etc/nginx/sites-available/tabs.retroterminal.net.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d tabs.retroterminal.net
sudo nginx -t
sudo systemctl reload nginx
```

## Optional Nav Switch

Right now the Jekyll nav still points at `/tabs/`.

If you want the header to point to the subdomain later, change in `_config.yml`:

```yml
tabs_nav_url: https://tabs.retroterminal.net/
```

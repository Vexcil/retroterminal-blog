"""Loopback-only bridge for Tailscale Serve to the archive host."""
import select
import socket
import socketserver

class Bridge(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            with socket.create_connection(('100.65.160.97',4081), timeout=15) as upstream:
                self.request.settimeout(30)
                upstream.settimeout(30)
                sockets=[self.request,upstream]
                while True:
                    ready,_,_=select.select(sockets,[],[],60)
                    if not ready:
                        return
                    for source in ready:
                        data=source.recv(65536)
                        if not data:
                            return
                        (upstream if source is self.request else self.request).sendall(data)
        except (OSError,TimeoutError):
            return

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True

if __name__=='__main__':
    with Server(('127.0.0.1',4082),Bridge) as server:
        server.serve_forever()

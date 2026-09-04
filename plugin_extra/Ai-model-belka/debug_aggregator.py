"""Local HTTP log aggregator for Ai-model-belka debugging."""

import json
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = 8765


def local_ipv4_addresses():
    addresses = set()
    hostname = socket.gethostname()
    for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, socket.AF_INET):
        if family == socket.AF_INET:
            addresses.add(sockaddr[0])
    addresses.discard("127.0.0.1")
    return sorted(addresses)


class LogHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/log":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error(400, "Expected UTF-8 JSON")
            return

        received_at = datetime.now(timezone.utc).isoformat()
        print(json.dumps({"received_at": received_at, **payload}, ensure_ascii=False), flush=True)
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        return


def main():
    addresses = local_ipv4_addresses()
    server = ThreadingHTTPServer((HOST, PORT), LogHandler)
    print(f"Log aggregator listening on 0.0.0.0:{PORT}", flush=True)
    if addresses:
        print("Set plugin URL to one of:", flush=True)
        for address in addresses:
            print(f"  http://{address}:{PORT}/log", flush=True)
    else:
        print(f"Set plugin URL to http://127.0.0.1:{PORT}/log", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping log aggregator.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

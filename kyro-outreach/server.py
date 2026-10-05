from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

PUBLIC_DIR = Path(__file__).resolve().parent / "public"


class handler(BaseHTTPRequestHandler):
    """Small, dependency-free HTTP handler for local use and Vercel Functions."""

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path in {"/health", "/api/health"}:
            body = json.dumps({"status": "ok", "service": "kyro-outreach"}).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        if path == "/":
            target = PUBLIC_DIR / "index.html"
        else:
            requested = (PUBLIC_DIR / path.lstrip("/")).resolve()
            if PUBLIC_DIR not in requested.parents:
                self._send(404, b"Not found", "text/plain; charset=utf-8")
                return
            target = requested

        if not target.is_file():
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return

        content_type, _ = mimetypes.guess_type(target.name)
        content_type = content_type or "application/octet-stream"
        self._send(200, target.read_bytes(), f"{content_type}; charset=utf-8")

    def do_HEAD(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            target = PUBLIC_DIR / "index.html"
        else:
            target = (PUBLIC_DIR / path.lstrip("/")).resolve()

        if not target.is_file() or PUBLIC_DIR not in target.parents:
            self.send_response(404)
            self.end_headers()
            return

        content_type, _ = mimetypes.guess_type(target.name)
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(target.stat().st_size))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000
    server = HTTPServer((host, port), handler)
    print(f"Kyro Outreach listening on http://{host}:{port}")
    server.serve_forever()

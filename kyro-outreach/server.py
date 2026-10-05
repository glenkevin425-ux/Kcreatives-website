from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

PUBLIC_DIR = Path(__file__).resolve().parent / "public"

class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path: str) -> None:
        if path == "/":
            target = PUBLIC_DIR / "index.html"
        else:
            target = (PUBLIC_DIR / path.lstrip("/")).resolve()
        if PUBLIC_DIR not in target.parents and target != PUBLIC_DIR / "index.html":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        if not target.is_file():
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        content_type, _ = mimetypes.guess_type(target.name)
        self._send(200, target.read_bytes(), f"{content_type or 'application/octet-stream'}; charset=utf-8")

    def _api(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send(200, json.dumps({"status":"ok","service":"kyro-outreach","version":"1.0"}).encode(), "application/json; charset=utf-8")
            return True
        return False

    def do_GET(self):
        if self._api():
            return
        self._static(urlparse(self.path).path)

    def do_HEAD(self):
        path = urlparse(self.path).path
        target = PUBLIC_DIR / "index.html" if path == "/" else (PUBLIC_DIR / path.lstrip("/")).resolve()
        if not target.is_file() or PUBLIC_DIR not in target.parents:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", f"{mimetypes.guess_type(target.name)[0] or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(target.stat().st_size))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), handler).serve_forever()

from http.server import BaseHTTPRequestHandler
from api_utils import send

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        send(self, 200, {"status": "ok", "service": "kyro-outreach", "version": "1.0"})

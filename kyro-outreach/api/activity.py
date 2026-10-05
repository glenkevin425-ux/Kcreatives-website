from http.server import BaseHTTPRequestHandler
from api_utils import body, get_db, rows, send

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = get_db()
        try:
            send(self, 200, {"items": rows(db, "SELECT * FROM activity ORDER BY id DESC LIMIT 50")})
        finally:
            db.close()

    def do_POST(self):
        data = body(self)
        message = str(data.get("message", "")).strip()
        if not message:
            send(self, 400, {"error": "Activity message is required"})
            return
        db = get_db()
        try:
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", (str(data.get("kind","Note")), message))
            db.commit()
            send(self, 201, {"ok": True})
        finally:
            db.close()

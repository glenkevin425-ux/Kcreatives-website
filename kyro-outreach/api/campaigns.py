from http.server import BaseHTTPRequestHandler
from api_utils import body, get_db, rows, send

VALID = {"Draft", "Active", "Paused", "Completed"}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = get_db()
        try:
            send(self, 200, {"items": rows(db, "SELECT * FROM campaigns ORDER BY id DESC")})
        finally:
            db.close()

    def do_POST(self):
        data = body(self)
        name = str(data.get("name", "")).strip()
        if not name:
            send(self, 400, {"error": "Campaign name is required"})
            return
        status = str(data.get("status", "Draft")).strip()
        if status not in VALID:
            status = "Draft"
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO campaigns(name,status,channel,goal) VALUES(?,?,?,?)",
                (name, status, str(data.get("channel","Email")).strip(), str(data.get("goal","")).strip())
            )
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", ("Campaign created", name))
            db.commit()
            send(self, 201, dict(db.execute("SELECT * FROM campaigns WHERE id=?", (cur.lastrowid,)).fetchone()))
        finally:
            db.close()

    def do_PATCH(self):
        try:
            campaign_id = int(self.path.rstrip("/").split("/")[-1])
        except ValueError:
            send(self, 400, {"error": "Invalid campaign id"})
            return
        data = body(self)
        db = get_db()
        try:
            existing = db.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
            if not existing:
                send(self, 404, {"error": "Campaign not found"})
                return
            updates = []
            values = []
            for key in ("name","status","channel","goal"):
                if key in data:
                    if key == "status" and data[key] not in VALID:
                        send(self, 400, {"error": "Invalid status"})
                        return
                    updates.append(f"{key}=?")
                    values.append(str(data[key]).strip())
            if not updates:
                send(self, 400, {"error": "No changes supplied"})
                return
            values.append(campaign_id)
            db.execute(f"UPDATE campaigns SET {','.join(updates)} WHERE id=?", values)
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", ("Campaign updated", str(data.get("name", existing["name"]))))
            db.commit()
            send(self, 200, dict(db.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()))
        finally:
            db.close()

    def do_DELETE(self):
        try:
            campaign_id = int(self.path.rstrip("/").split("/")[-1])
        except ValueError:
            send(self, 400, {"error": "Invalid campaign id"})
            return
        db = get_db()
        try:
            row = db.execute("SELECT name FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
            if not row:
                send(self, 404, {"error": "Campaign not found"})
                return
            db.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", ("Campaign removed", row["name"]))
            db.commit()
            send(self, 200, {"ok": True})
        finally:
            db.close()

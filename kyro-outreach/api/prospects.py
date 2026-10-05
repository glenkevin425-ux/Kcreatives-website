from http.server import BaseHTTPRequestHandler
from api_utils import body, get_db, rows, send, method_not_allowed

VALID = {"New", "Draft", "Approved", "Replied", "Interested", "Not Interested", "Do Not Contact"}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = get_db()
        try:
            send(self, 200, {"items": rows(db, "SELECT * FROM prospects ORDER BY id DESC")})
        finally:
            db.close()

    def do_POST(self):
        data = body(self)
        name = str(data.get("name", "")).strip()
        company = str(data.get("company", "")).strip()
        if not name or not company:
            send(self, 400, {"error": "Name and company are required"})
            return
        status = str(data.get("status", "New")).strip()
        if status not in VALID:
            status = "New"
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO prospects(name,company,email,channel,status,campaign,note) VALUES(?,?,?,?,?,?,?)",
                (name, company, str(data.get("email","")).strip(), str(data.get("channel","Email")).strip(),
                 status, str(data.get("campaign","Unassigned")).strip(), str(data.get("note","")).strip())
            )
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", ("Prospect added", f"{name} · {company}"))
            db.commit()
            item = dict(db.execute("SELECT * FROM prospects WHERE id=?", (cur.lastrowid,)).fetchone())
            send(self, 201, item)
        finally:
            db.close()

    def do_PATCH(self):
        try:
            prospect_id = int(self.path.rstrip("/").split("/")[-1])
        except ValueError:
            send(self, 400, {"error": "Invalid prospect id"})
            return
        data = body(self)
        db = get_db()
        try:
            existing = db.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,)).fetchone()
            if not existing:
                send(self, 404, {"error": "Prospect not found"})
                return
            fields = ["name","company","email","channel","status","campaign","note"]
            values = [str(data[k]).strip() for k in fields if k in data]
            names = [k for k in fields if k in data]
            if "status" in data and data["status"] not in VALID:
                send(self, 400, {"error": "Invalid status"})
                return
            if not names:
                send(self, 400, {"error": "No changes supplied"})
                return
            assignments = ",".join(f"{k}=?" for k in names)
            values += [prospect_id]
            db.execute(f"UPDATE prospects SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", ("Prospect updated", str(data.get("name", existing["name"]))))
            db.commit()
            send(self, 200, dict(db.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,)).fetchone()))
        finally:
            db.close()

    def do_DELETE(self):
        try:
            prospect_id = int(self.path.rstrip("/").split("/")[-1])
        except ValueError:
            send(self, 400, {"error": "Invalid prospect id"})
            return
        db = get_db()
        try:
            row = db.execute("SELECT name FROM prospects WHERE id=?", (prospect_id,)).fetchone()
            if not row:
                send(self, 404, {"error": "Prospect not found"})
                return
            db.execute("DELETE FROM prospects WHERE id=?", (prospect_id,))
            db.execute("INSERT INTO activity(kind,message) VALUES(?,?)", ("Prospect removed", row["name"]))
            db.commit()
            send(self, 200, {"ok": True})
        finally:
            db.close()

    def do_PUT(self):
        return self.do_PATCH()

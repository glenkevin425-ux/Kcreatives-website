from http.server import BaseHTTPRequestHandler
from api_utils import get_db, rows, send

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = get_db()
        try:
            prospects = rows(db, "SELECT status, COUNT(*) AS count FROM prospects GROUP BY status")
            campaigns = rows(db, "SELECT status, COUNT(*) AS count FROM campaigns GROUP BY status")
            recent = rows(db, "SELECT id, kind, message, created_at FROM activity ORDER BY id DESC LIMIT 8")
            total = db.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]
            approved = db.execute("SELECT COUNT(*) FROM prospects WHERE status='Approved'").fetchone()[0]
            replies = db.execute("SELECT COUNT(*) FROM prospects WHERE status IN ('Replied','Interested')").fetchone()[0]
            active_campaigns = db.execute("SELECT COUNT(*) FROM campaigns WHERE status='Active'").fetchone()[0]
            send(self, 200, {
                "metrics": {
                    "prospects": total,
                    "approved": approved,
                    "replies": replies,
                    "activeCampaigns": active_campaigns
                },
                "prospectStatuses": prospects,
                "campaignStatuses": campaigns,
                "activity": recent
            })
        finally:
            db.close()

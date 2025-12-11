from models import db
from datetime import datetime
class User(db.Model):
    __tablename__ = "tbl_users"

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    picture = db.Column(db.Text)
    role = db.Column(db.String(50), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
from models import db

class InstrumentClosingPrice(db.Model):
    __tablename__ = "tbl_instruments_closing_price"

    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(50), nullable=False)
    instrument = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    closing_date = db.Column("closing_date", db.Date, nullable=False)
    update_time = db.Column("update_time", db.DateTime, nullable=False)
from models import db

class Currency(db.Model):
    __tablename__ = "tbl_currencies"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)

class CoinPrice(db.Model):
    __tablename__ = "tbl_coin_prices"

    id = db.Column(db.Integer, primary_key=True)
    coin_currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    quote_currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    price = db.Column(db.Float, nullable=False)
    datetime_update = db.Column("date_time_update", db.DateTime, nullable=False)
    coin_currency = db.relationship('Currency', foreign_keys=[coin_currency_id])
    quote_currency = db.relationship('Currency', foreign_keys=[quote_currency_id])
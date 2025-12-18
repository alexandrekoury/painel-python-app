from models import db

class Exchange(db.Model):
    __tablename__="tbl_exchanges"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.String(255))
    tbl_exchangescol = db.Column(db.String(45))
    update_datetime = db.Column(db.DateTime)

class Strategy(db.Model):
    __tablename__="tbl_strategies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.String(255))
    update_datetime = db.Column(db.DateTime)

class ExchangeBalance(db.Model):
    __tablename__="tbl_balances_history"
    id = db.Column(db.Integer, primary_key=True)
    update_datetime = db.Column(db.DateTime)
    balance = db.Column(db.Float)
    exchange_id = db.Column(db.Integer, db.ForeignKey('tbl_exchanges.id'))
    strategy_id = db.Column(db.Integer, db.ForeignKey('tbl_strategies.id'))
    currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    exchange = db.relationship('Exchange', foreign_keys=[exchange_id])
    currency = db.relationship('Currency', foreign_keys=[currency_id])
    strategy = db.relationship('Strategy', foreign_keys=[strategy_id])

class CryptoTransaction(db.Model):
    __tablename__="tbl_crypto_transactions"
    id = db.Column(db.Integer, primary_key=True)
    effective_date = db.Column(db.DateTime)
    investor_id = db.Column(db.Integer, db.ForeignKey('tbl_investors.id'))
    currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    amount = db.Column(db.Float)
    price = db.Column(db.Float)
    update_datetime = db.Column(db.DateTime)
    investor = db.relationship('Investor', foreign_keys=[investor_id])
    currency = db.relationship('Currency', foreign_keys=[currency_id])

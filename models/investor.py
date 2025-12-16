from models import db

class Investor(db.Model):
    __tablename__="tbl_investors"
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(30))
    username = db.Column(db.String(50))


class InvestorTransaction(db.Model):
    __tablename__ = "tbl_investor_transactions"

    id = db.Column(db.Integer, primary_key=True)
    effective_datetime = db.Column(db.DateTime)
    received_datetime = db.Column(db.DateTime)
    transaction_type = db.Column(db.Enum('red_cash', 'red_kind', 'dep_cash', 'dep_kind', name='transaction_type'))
    cash_amount = db.Column(db.Float)
    kind_amount = db.Column(db.Float)
    transaction_nav = db.Column(db.Float)
    investor_id = db.Column(db.Integer, db.ForeignKey('tbl_investors.id'))
    cash_currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    kind_currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    investor = db.relationship('Investor', backref=db.backref('transactions', lazy=True))
    cash_currency = db.relationship('Currency', foreign_keys=[cash_currency_id])
    kind_currency = db.relationship('Currency', foreign_keys=[kind_currency_id])
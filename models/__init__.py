from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.investor import Investor, InvestorTransaction
from models.currency import Currency, CoinPrice
from models.exchange import Exchange, Strategy, ExchangeBalance
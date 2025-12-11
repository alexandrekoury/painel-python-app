from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.investor import Investor
from models.currency import Currency
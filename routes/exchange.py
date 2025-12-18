from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db
from models.exchange import Exchange, Strategy, ExchangeBalance
from models.currency import Currency, CoinPrice
from decorators.auth import login_required, admin_required
from datetime import datetime
from sqlalchemy import select, func

exchange_bp = Blueprint('exchange', __name__, url_prefix='/exchange')
limiter = Limiter(key_func=get_remote_address)

@exchange_bp.route('/balances', methods=['GET'])
@login_required
@admin_required
def list_balances():
    query = ExchangeBalance.query

    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(func.date(ExchangeBalance.update_datetime) >= start_dt)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(func.date(ExchangeBalance.update_datetime) <= end_dt)
        except ValueError:
            pass
    limit = request.args.get('limit', type=int)
    
    if limit is not None:
        balances = query.order_by(func.date(ExchangeBalance.update_datetime).desc()).limit(limit)
    else:
        balances = query.order_by(func.date(ExchangeBalance.update_datetime).desc()).limit(50)

    return render_template('exchange/balances.html', balances=balances, start_date=start_date, end_date=end_date, limit=limit)

@exchange_bp.route('/balance/edit/<int:balance_id>', methods=['GET'])
@login_required
@admin_required
def edit_balance(balance_id):
    balance = ExchangeBalance.query.get_or_404(balance_id)
    return render_template('exchange/edit_balance.html', balance=balance)

@exchange_bp.route('/balance/update/<int:balance_id>', methods=['POST'])
@login_required
@admin_required
def update_balance(balance_id):
    balance = ExchangeBalance.query.get_or_404(balance_id)
    balance.balance = request.form['balance']
    balance.update_datetime = request.form['update_datetime']
    db.session.commit()
    return redirect(url_for('exchange.list_balances'))

@exchange_bp.route('/balances/consolidated', methods=['GET'])
@login_required
@admin_required
def get_consolidated_balances():
    query = (select(func.date(ExchangeBalance.update_datetime).label('date'), 
                   func.sum(ExchangeBalance.balance).label('total_balance'), 
                   func.first_value(Currency.code).over(partition_by=func.date(ExchangeBalance.update_datetime)).label('currency'))
                    .join(Currency, ExchangeBalance.currency_id == Currency.id))

    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.where(func.date(ExchangeBalance.update_datetime) >= start_dt)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.where(func.date(ExchangeBalance.update_datetime) <= end_dt)
        except ValueError:
            pass

    query = query.group_by(func.date(ExchangeBalance.update_datetime)).order_by(func.date(ExchangeBalance.update_datetime).desc())

    limit = request.args.get('limit', type=int)
    if limit is not None and limit <= 1000:
        query = query.limit(limit)
    else:
        query = query.limit(100)

    results = db.session.execute(query).fetchall()
    return render_template('exchange/consolidated.html', results=results, start_date=start_date, end_date=end_date, limit=limit)
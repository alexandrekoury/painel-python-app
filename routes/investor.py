from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db
from models.investor import Investor, InvestorTransaction
from models.currency import Currency
from decorators.auth import login_required, admin_required
from datetime import datetime
from sqlalchemy import func

investor_bp = Blueprint('investor', __name__, url_prefix='/investor')
limiter = Limiter(key_func=get_remote_address)

@investor_bp.route('/', methods=['GET'])
@login_required
@admin_required
def list_investors():
    investors = Investor.query.all()
    return render_template('investor/investors.html', investors=investors)

@investor_bp.route('/create', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def create_investor():
    alias = request.form['alias']
    username = request.form['username']
    new_investor = Investor(alias=alias, username=username)
    db.session.add(new_investor)
    db.session.commit()
    return redirect(url_for('investor.list_investors'))

@investor_bp.route('/edit/<int:investor_id>', methods=['GET'])
@login_required
@admin_required
def edit_investor(investor_id):
    investor = Investor.query.get_or_404(investor_id)
    return render_template('investor/edit.html', investor=investor)

@investor_bp.route('/update/<int:investor_id>', methods=['POST'])
@login_required
@admin_required
def update_investor(investor_id):
    investor = Investor.query.get_or_404(investor_id)
    investor.alias = request.form['alias']
    investor.username = request.form['username']
    db.session.commit()
    return redirect(url_for('investor.list_investors'))

@investor_bp.route('/delete/<int:investor_id>', methods=['POST'])
@login_required
@admin_required
def delete_investor(investor_id):
    investor = Investor.query.get_or_404(investor_id)
    db.session.delete(investor)
    db.session.commit()
    return redirect(url_for('investor.list_investors'))

@investor_bp.route('/transactions/create', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def create_transaction():
    effective_datetime = request.form['effective_datetime']
    received_datetime = request.form['received_datetime']
    transaction_type = request.form['transaction_type']
    cash_amount = request.form.get('cash_amount', type=float)
    kind_amount = request.form.get('kind_amount', type=float)
    transaction_nav = request.form.get('transaction_nav', type=float)
    investor_id = request.form.get('investor_id', type=int)
    cash_currency_id = request.form.get('cash_currency_id', type=int)
    kind_currency_id = request.form.get('kind_currency_id', type=int)
    
    new_transaction = InvestorTransaction(
        effective_datetime=effective_datetime,
        received_datetime=received_datetime,
        transaction_type=transaction_type,
        cash_amount=cash_amount,
        kind_amount=kind_amount,
        transaction_nav=transaction_nav,
        investor_id=investor_id,
        cash_currency_id=cash_currency_id,
        kind_currency_id=kind_currency_id
    )
    db.session.add(new_transaction)
    db.session.commit()
    return redirect(url_for('investor.list_transactions'))

@investor_bp.route('/transactions/new', methods=['GET'])
@login_required
@admin_required
def new_transaction():
    investors = Investor.query.all()
    currencies = Currency.query.all()
    return render_template('investor/create_transaction.html', investors=investors, currencies=currencies)

@investor_bp.route('/transactions/edit/<int:transaction_id>', methods=['GET'])
@login_required
@admin_required
def edit_transaction(transaction_id):
    transaction = InvestorTransaction.query.get_or_404(transaction_id)
    investors = Investor.query.all()
    currencies = Currency.query.all()
    return render_template('investor/edit_transaction.html', transaction=transaction, investors=investors, currencies=currencies)

@investor_bp.route('/transactions/update/<int:transaction_id>', methods=['POST'])
@login_required
@admin_required
def update_transaction(transaction_id):
    transaction = InvestorTransaction.query.get_or_404(transaction_id)
    transaction.effective_datetime = request.form['effective_datetime']
    transaction.received_datetime = request.form['received_datetime']
    transaction.transaction_type = request.form['transaction_type']
    transaction.cash_amount = request.form.get('cash_amount', type=float)
    transaction.kind_amount = request.form.get('kind_amount', type=float)
    transaction.transaction_nav = request.form.get('transaction_nav', type=float)
    transaction.investor_id = request.form.get('investor_id', type=int)
    transaction.cash_currency_id = request.form.get('cash_currency_id', type=int)
    transaction.kind_currency_id = request.form.get('kind_currency_id', type=int)
    db.session.commit()
    return redirect(url_for('investor.list_transactions'))

@investor_bp.route('/transactions', methods=['GET'])
@login_required
@admin_required
def list_transactions():
    query = InvestorTransaction.query

    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(func.date(InvestorTransaction.effective_datetime) >= start_dt)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(func.date(InvestorTransaction.effective_datetime) <= end_dt)
        except ValueError:
            pass
    
    transactions = query.order_by(func.date(InvestorTransaction.effective_datetime).desc())

    limit = request.args.get('limit', type=int)
    if limit is not None:
        query = query.limit(limit)
    else:
        query = query.limit(50)

    return render_template('investor/transactions.html', transactions=transactions, start_date=start_date, end_date=end_date, limit=limit)

@investor_bp.route('/transactions/delete/<int:transaction_id>', methods=['POST'])
@login_required
@admin_required
def delete_transaction(transaction_id):
    transaction = InvestorTransaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('investor.list_transactions'))
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db
from models.investor import Investor, InvestorTransaction
from decorators.auth import login_required, admin_required

investor_bp = Blueprint('investor', __name__, url_prefix='/investor')
limiter = Limiter(key_func=get_remote_address)

@investor_bp.route('/', methods=['GET'])
@login_required
@admin_required
def list_investors():
    investors = Investor.query.all()
    user = session.get('user')
    return render_template('investor/investors.html', investors=investors, user=user)

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
    user = session.get('user')
    return render_template('investor/edit.html', investor=investor, user=user)

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

@investor_bp.route('/transactions', methods=['GET'])
@login_required
@admin_required
def list_transactions():
    transactions = InvestorTransaction.query.all()
    user = session.get('user')
    return render_template('investor/transactions.html', transactions=transactions, user=user)

@investor_bp.route('/transactions/delete/<int:transaction_id>', methods=['POST'])
@login_required
@admin_required
def delete_transaction(transaction_id):
    transaction = InvestorTransaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('investor.list_transactions'))
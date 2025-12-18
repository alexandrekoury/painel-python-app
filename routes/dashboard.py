from decorators.auth import login_required, admin_required
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import db
from models.exchange import ExchangeBalance, CryptoTransaction
from models.investor import InvestorTransaction
from models.currency import CoinPrice
from sqlalchemy import func
from datetime import datetime, timedelta
import requests

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/', methods=['GET'])
@login_required
@admin_required
def index():

    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    default_start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    default_end_date = (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d')
    
    if start_date_param:
        start_date = start_date_param
    else:
        start_date = default_start_date
    
    if end_date_param:
        end_date = end_date_param
    else:
        end_date = default_end_date
    
    balance_difference = calculate_balance_difference(start_date=start_date, end_date=end_date)[0].json
    investor_transactions_data = calculate_investor_transactions(start_date=start_date, end_date=end_date)
    transactions_difference = investor_transactions_data[0].json
    investor_transactions = investor_transactions_data[1]
    crypto_variation = calculate_crypto_variation(start_date=start_date, end_date=end_date)[0].json
    total_profit = balance_difference['balance_difference']- transactions_difference['transactions_difference'] - crypto_variation['total_variation']
    data = {
        'balance_difference': balance_difference,
        'transactions_difference': transactions_difference,
        'investor_transactions': investor_transactions,
        'crypto_variation': crypto_variation,
        'total_profit': total_profit
    }

    return render_template('dashboard/index.html', data=data, start_date=start_date, end_date=end_date)

def calculate_investor_transactions(start_date: str, end_date: str):

    start_transactions_sum = db.session.query(func.sum(InvestorTransaction.cash_amount)).filter(
        func.date(InvestorTransaction.effective_datetime) <= start_date
    ).scalar() or 0.0
    
    end_transactions_sum = db.session.query(func.sum(InvestorTransaction.cash_amount)).filter(
        func.date(InvestorTransaction.effective_datetime) <= end_date
    ).scalar() or 0.0

    transactions = db.session.query(InvestorTransaction).filter(
        func.date(InvestorTransaction.effective_datetime) >= start_date,
        func.date(InvestorTransaction.effective_datetime) <= end_date
    ).all()
    
    transactions_difference = end_transactions_sum - start_transactions_sum
   
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'start_transactions_sum': float(start_transactions_sum),
        'end_transactions_sum': float(end_transactions_sum),
        'transactions_difference': float(transactions_difference)
    }), transactions, 200
    
def calculate_balance_difference(start_date: str, end_date: str):

    start_balance_sum = db.session.query(func.sum(ExchangeBalance.balance)).filter(
        func.date(ExchangeBalance.update_datetime) == start_date
    ).scalar() or 0.0
    
    end_balance_sum = db.session.query(func.sum(ExchangeBalance.balance)).filter(
        func.date(ExchangeBalance.update_datetime) == end_date
    ).scalar() or 0.0
    
    balance_difference = end_balance_sum - start_balance_sum
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'start_balance_sum': float(start_balance_sum),
        'end_balance_sum': float(end_balance_sum),
        'balance_difference': float(balance_difference)
    }), 200

def calculate_crypto_variation(start_date: str, end_date: str):
    """
    Calculate the value variation of crypto holdings between two dates.
    Returns the total variation in value based on price changes.
    """
    from sqlalchemy import and_
    from models.currency import Currency
    
    # Get total crypto amounts per currency (cumulative up to end_date)
    crypto_amounts = db.session.query(
        CryptoTransaction.currency_id,
        func.sum(CryptoTransaction.amount).label('total_amount')
    ).filter(
        func.date(CryptoTransaction.effective_date) <= end_date
    ).group_by(CryptoTransaction.currency_id).all()
    
    total_variation = 0.0
    variations_by_currency = []
    
    for currency_id, total_amount in crypto_amounts:
        if total_amount is None or total_amount == 0:
            continue
            
        # Get price at start_date (most recent price on or before start_date)
        start_price = db.session.query(CoinPrice.price).filter(
            and_(
                CoinPrice.coin_currency_id == currency_id,
                func.date(CoinPrice.datetime_update) == start_date
            )
        ).order_by(CoinPrice.datetime_update.desc()).scalar() or 0.0
        
        # Get price at end_date (most recent price on end_date)
        end_price = db.session.query(CoinPrice.price).filter(
            and_(
                CoinPrice.coin_currency_id == currency_id,
                func.date(CoinPrice.datetime_update) == end_date
            )
        ).order_by(CoinPrice.datetime_update.desc()).scalar() or 0.0
        
        # Calculate value variation for this currency
        start_value = float(total_amount) * float(start_price)
        end_value = float(total_amount) * float(end_price)
        currency_variation = end_value - start_value
        
        total_variation += currency_variation
        
        # Get currency code for display
        currency = db.session.query(Currency).filter(Currency.id == currency_id).first()
        currency_code = currency.code if currency else f"Currency_{currency_id}"
        
        variations_by_currency.append({
            'currency_id': currency_id,
            'currency_code': currency_code,
            'amount': float(total_amount),
            'start_price': float(start_price),
            'end_price': float(end_price),
            'start_value': start_value,
            'end_value': end_value,
            'variation': currency_variation
        })
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'total_variation': float(total_variation),
        'variations_by_currency': variations_by_currency
    }), 200

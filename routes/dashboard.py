from decorators.auth import login_required, admin_required
from flask import Blueprint, render_template, request, jsonify
from models import db
from models.exchange import ExchangeBalance, CryptoTransaction
from models.investor import InvestorTransaction
from models.currency import CoinPrice, Currency
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy import and_
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

def _get_coin_price(currency_id: int, target_date: str = None, max_date: str = None, order_desc: bool = False) -> float:
    """
    Helper function to fetch coin price for a specific currency and date.
    
    Args:
        currency_id: The currency ID to fetch price for
        target_date: Exact date to match
        max_date: Maximum date (inclusive) to search up to
        order_desc: If True, get most recent price on or before date
    
    Returns:
        The price as float, or 0.0 if not found
    """
    query = db.session.query(CoinPrice.price).filter(
        CoinPrice.coin_currency_id == currency_id
    )
    
    if target_date:
        query = query.filter(func.date(CoinPrice.datetime_update) == target_date)
    elif max_date:
        query = query.filter(func.date(CoinPrice.datetime_update) <= max_date)
    
    if order_desc:
        query = query.order_by(CoinPrice.datetime_update.desc()).limit(1)
    
    result = query.scalar()
    return float(result) if result else 0.0


def _calculate_initial_state(currency_id: int, start_date: str) -> tuple:
    """
    Calculate holdings amount and cost basis before start_date using average cost method.
    
    Returns:
        Tuple of (amounts_before, cost_basis_before, avg_price_start)
    """
    
    
    total_amount = db.session.query(func.sum(CryptoTransaction.amount)).filter(
        func.date(CryptoTransaction.effective_date) < start_date,
        CryptoTransaction.currency_id == currency_id
    ).scalar() or 0.0
    
    cost_basis = 0.0
    avg_price = 0.0
    amount = 0.0

    if total_amount > 0:
        transactions_before = db.session.query(CryptoTransaction).filter(
        func.date(CryptoTransaction.effective_date) < start_date,
        CryptoTransaction.currency_id == currency_id
    ).order_by(CryptoTransaction.effective_date).all()
        
        for tx in transactions_before:
            if tx.amount > 0:
                # Buy: update cost basis
                cost_basis += tx.amount * tx.price
                amount += tx.amount
            else:
                # Sell: reduce cost basis proportionally
                if amount > 0:
                    cost_basis = cost_basis * (1 + tx.amount / amount)
                    amount += tx.amount
                    if amount <= 0:
                        cost_basis = 0.0
                        amount = 0.0
    
       # avg_price = (cost_basis / amount) if amount > 0 else 0.0
    return amount, cost_basis


def calculate_crypto_variation(start_date: str, end_date: str):
    """
    Calculate the value variation of crypto holdings between two dates.
    Accounts for additions and removals using average cost method.
    """
    
    currencies = db.session.query(Currency).all()
    variations_by_currency = []
    total_variation = 0.0
    
    for currency in currencies:
        if currency.code in ('USD', 'BRL'):
            continue  # Skip fiat currencies
        
        print(currency.code)
        
        # Fetch data for this currency
        transactions_in_period = db.session.query(CryptoTransaction).filter(
            func.date(CryptoTransaction.effective_date) >= start_date,
            func.date(CryptoTransaction.effective_date) <= end_date,
            CryptoTransaction.currency_id == currency.id
        ).all()
        
        # Calculate initial state before start_date
        amounts_before_start_date, cost_basis_before = _calculate_initial_state(
            currency.id, start_date
        )
        print(f"amount before: {amounts_before_start_date}")
        
        # Get prices for the period
        start_price_previous = _get_coin_price(currency.id, target_date=start_date)
        print(f"start price previous: {start_price_previous}")
        end_price = _get_coin_price(currency.id, target_date=end_date)
        
        # Calculate variation on holdings that existed before the period
        variation_previous = float(amounts_before_start_date) * (float(end_price) - float(start_price_previous))
        print(f"  Variation previous holdings: {variation_previous}")
        
        # Process transactions during the period
        currency_total_variation = variation_previous
        holdings_data = []
        total_held = amounts_before_start_date
        current_avg_price = start_price_previous if amounts_before_start_date > 0 else 0.0
        current_cost_basis = cost_basis_before if amounts_before_start_date > 0 else 0.0
        
        for tx in transactions_in_period:
            print(f"Transaction: {tx.id} {tx.effective_date} {tx.amount} {tx.price}")
            tx_date_str = tx.effective_date.strftime('%Y-%m-%d') if hasattr(tx.effective_date, 'strftime') else str(tx.effective_date)
            
            # Update holdings and average price
            total_held += tx.amount
            
            if tx.amount > 0:
                # Buy: update average price and cost basis
                new_total_amount = amounts_before_start_date + total_held
                current_cost_basis += tx.amount * tx.price
                current_avg_price = current_cost_basis / new_total_amount if new_total_amount > 0 else 0.0
            else:
                # Sell: reduce cost basis proportionally, reset if holdings reach zero
                if total_held <= 0:
                    current_avg_price = 0.0
                    current_cost_basis = 0.0
                else:
                    current_cost_basis = current_cost_basis * (1 + tx.amount / (amounts_before_start_date + total_held - tx.amount))
            
            # Calculate variation for this transaction
            measurement_start = max(start_date, tx_date_str)
            
            if measurement_start <= end_date and total_held > 0:
                # Get price at measurement start
                price_at_measurement_start = (
                    _get_coin_price(currency.id, max_date=measurement_start, order_desc=True)
                    if measurement_start < start_date
                    else tx.price
                )
                
                # Calculate variation: amount × (end_price - price_when_held)
                tx_variation = float(tx.amount) * (float(end_price) - float(price_at_measurement_start))
                print(f"  Variation for this tx: {tx_variation}")
                currency_total_variation += tx_variation
                print(f"  Total variation so far for currency: {currency_total_variation}")
                
                holdings_data.append({
                    'transaction_date': tx_date_str,
                    'amount': float(tx.amount),
                    'transaction_price': float(tx.price),
                    'measurement_start': measurement_start,
                    'price_at_measurement_start': float(price_at_measurement_start),
                    'price_at_end': float(end_price),
                    'variation': tx_variation,
                    'avg_price_after_tx': float(current_avg_price)
                })
        
        print(f"  Variation with previous holdings: {currency_total_variation}")
        total_variation += currency_total_variation
        
        variations_by_currency.append({
            'currency_id': currency.id,
            'currency_code': currency.code,
            'amount': float(total_held),
            'start_price': float(current_avg_price),
            'end_price': float(end_price),
            'variation': currency_total_variation,
            'holdings_details': holdings_data
        })
    
    print(f"Total variation overall: {total_variation}")
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'total_variation': float(total_variation),
        'variations_by_currency': variations_by_currency
    }), 200
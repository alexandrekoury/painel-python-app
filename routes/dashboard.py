from decorators.auth import login_required, admin_required
from flask import Blueprint, render_template, request, jsonify, current_app
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
    
    start_date = start_date_param or default_start_date
    end_date = end_date_param or default_end_date
    
    return render_template('dashboard/index.html', start_date=start_date, end_date=end_date)


@dashboard_bp.route('/api/balance', methods=['GET'])
@login_required
@admin_required
def api_balance():
    """Fetch balance difference data as JSON"""
    try:
        start_date = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d'))
        
        data = calculate_balance_difference(start_date=start_date, end_date=end_date)[0].json
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'data': None}), 500


@dashboard_bp.route('/api/transactions', methods=['GET'])
@login_required
@admin_required
def api_transactions():
    """Fetch investor transactions data as JSON"""
    try:
        start_date = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d'))
        
        transactions_diff, investor_transactions, _ = calculate_investor_transactions(
            start_date=start_date, 
            end_date=end_date
        )
        transactions_data = transactions_diff.json
        
        # Serialize investor transactions
        serialized_transactions = []
        for tx in investor_transactions:
            serialized_transactions.append({
                'id': tx.id,
                'effective_datetime': str(tx.effective_datetime),
                'transaction_type': tx.transaction_type,
                'cash_amount': float(tx.cash_amount),
                'cash_currency_code': tx.cash_currency.code if tx.cash_currency else None,
                'kind_amount': float(tx.kind_amount) if tx.kind_amount else None,
                'kind_currency_code': tx.kind_currency.code if tx.kind_currency else None,
                'investor_alias': tx.investor.alias if tx.investor else None,
                'transaction_nav': float(tx.transaction_nav) if tx.transaction_nav else None
            })
        
        transactions_data['investor_transactions'] = serialized_transactions
        return jsonify({'success': True, 'data': transactions_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'data': None}), 500


@dashboard_bp.route('/api/crypto-variation', methods=['GET'])
@login_required
@admin_required
def api_crypto_variation():
    """Fetch crypto variation data as JSON"""
    try:
        start_date = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d'))
        
        data = calculate_crypto_variation(start_date=start_date, end_date=end_date)[0].json
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'data': None}), 500

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

def _get_coin_price(currency_id: int, target_date: str = None, max_date: str = None, order_desc: bool = False, price_cache: dict = None) -> float:
    """
    Helper function to fetch coin price for a specific currency and date.
    Uses local cache to avoid redundant DB queries.
    
    Args:
        currency_id: The currency ID to fetch price for
        target_date: Exact date to match
        max_date: Maximum date (inclusive) to search up to
        order_desc: If True, get most recent price on or before date
        price_cache: Optional dict to cache results during calculation
    
    Returns:
        The price as float, or 0.0 if not found
    """
    if price_cache is None:
        price_cache = {}
    
    # Create cache key
    cache_key = f"{currency_id}_{target_date or max_date}_{order_desc}"
    if cache_key in price_cache:
        return price_cache[cache_key]
    
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
    price = float(result) if result else 0.0
    price_cache[cache_key] = price
    return price


def _calculate_initial_state(currency_id: int, start_date: str, price_cache: dict = None) -> tuple:
    """
    Calculate holdings amount and cost basis before start_date using average cost method.
    
    Returns:
        Tuple of (amounts_before, cost_basis_before)
    """
    
    total_amount = db.session.query(func.sum(CryptoTransaction.amount)).filter(
        func.date(CryptoTransaction.effective_date) < start_date,
        CryptoTransaction.currency_id == currency_id
    ).scalar() or 0.0
    
    cost_basis = 0.0
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
    
    return amount, cost_basis


def calculate_crypto_variation(start_date: str, end_date: str):
    """
    Calculate the value variation of crypto holdings between two dates.
    Accounts for additions and removals using average cost method.
    Optimized with price caching to reduce DB queries.
    """
    
    # Initialize price cache for this entire calculation
    price_cache = {}
    
    currencies = db.session.query(Currency).filter(
        Currency.code.notin_(['USD', 'BRL'])  # Filter fiat currencies at DB level
    ).all()
    
    variations_by_currency = []
    total_variation = 0.0
    
    for currency in currencies:
        # Fetch data for this currency
        transactions_in_period = db.session.query(CryptoTransaction).filter(
            func.date(CryptoTransaction.effective_date) >= start_date,
            func.date(CryptoTransaction.effective_date) <= end_date,
            CryptoTransaction.currency_id == currency.id
        ).all()
        
        # Calculate initial state before start_date
        amounts_before_start_date, cost_basis_before = _calculate_initial_state(
            currency.id, start_date, price_cache
        )
        
        # Get prices for the period with caching
        start_price_previous = _get_coin_price(currency.id, target_date=start_date, price_cache=price_cache)
        end_price = _get_coin_price(currency.id, target_date=end_date, price_cache=price_cache)
        
        # Skip if no holdings before and no transactions during period
        if amounts_before_start_date == 0 and len(transactions_in_period) == 0:
            continue
        
        # Calculate variation on holdings that existed before the period
        variation_previous = float(amounts_before_start_date) * (float(end_price) - float(start_price_previous))
            
        # Process transactions during the period
        currency_total_variation = variation_previous
        holdings_data = []
        total_held = amounts_before_start_date
        current_avg_price = start_price_previous if amounts_before_start_date > 0 else 0.0
        current_cost_basis = cost_basis_before if amounts_before_start_date > 0 else 0.0
        
        for tx in transactions_in_period:
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
                # Get price at measurement start with caching
                price_at_measurement_start = (
                    _get_coin_price(currency.id, max_date=measurement_start, order_desc=True, price_cache=price_cache)
                    if measurement_start < start_date
                    else tx.price
                )
                
                # Calculate variation: amount × (end_price - price_when_held)
                tx_variation = float(tx.amount) * (float(end_price) - float(price_at_measurement_start))
                currency_total_variation += tx_variation
                
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
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'total_variation': float(total_variation),
        'variations_by_currency': variations_by_currency
    }), 200
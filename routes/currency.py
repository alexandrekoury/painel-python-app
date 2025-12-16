from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db
from models.currency import Currency, CoinPrice
from decorators.auth import login_required, admin_required
from datetime import datetime
from sqlalchemy import func

currency_bp = Blueprint('currency', __name__, url_prefix='/currency')
limiter = Limiter(key_func=get_remote_address)

# Currency CRUD Operations

@currency_bp.route('/currencies', methods=['GET'])
@login_required
@admin_required
def list_currencies():
    currencies = Currency.query.all()
    return render_template('currency/currencies.html', currencies=currencies)

@currency_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_currency():
    code = request.form.get('code')
    name = request.form.get('name')   
    currency = Currency(code=code, name=name)
    db.session.add(currency)
    db.session.commit()
    return redirect(url_for('currency.list_currencies'))

@currency_bp.route('/edit/<int:currency_id>', methods=['GET'])
@login_required
@admin_required
def edit_currency_form(currency_id):
    currency = Currency.query.get_or_404(currency_id)
    return render_template('currency/edit.html', currency=currency)

@currency_bp.route('/update/<int:currency_id>', methods=['POST'])
@login_required
@admin_required
def edit_currency(currency_id):
    currency = Currency.query.get_or_404(currency_id)
    currency.code = request.form.get('code', currency.code)
    currency.name = request.form.get('name', currency.name)
    db.session.commit()
    return redirect(url_for('currency.list_currencies'))

@currency_bp.route('/delete/<int:currency_id>', methods=['POST'])
@login_required
@admin_required
def delete_currency(currency_id):
    currency = Currency.query.get_or_404(currency_id)
    db.session.delete(currency)
    db.session.commit()
    return redirect(url_for('currency.list_currencies'))

# CoinPrice Read and Update Operations

@currency_bp.route('/prices', methods=['GET'])
@login_required
@admin_required
def list_coin_prices():
    query = CoinPrice.query

    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(func.date(CoinPrice.datetime_update) >= start_dt)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(func.date(CoinPrice.datetime_update) <= end_dt)
        except ValueError:
            pass

    coin_prices = query.order_by(CoinPrice.datetime_update.desc())

    limit = request.args.get('limit', type=int)
    if limit is not None:
        coin_prices = coin_prices.limit(limit)
    else:
        coin_prices = coin_prices.limit(50)

    coin_prices = coin_prices.all()
    return render_template('currency/prices.html', coin_prices=coin_prices, start_date=start_date, end_date=end_date, limit=limit)

@currency_bp.route('/price/edit/<int:price_id>', methods=['GET'])
@login_required
@admin_required
def edit_coin_price_form(price_id):
    coin_price = CoinPrice.query.get_or_404(price_id)
    currencies = Currency.query.all()
    return render_template('currency/edit_price.html', coin_price=coin_price, currencies=currencies)

@currency_bp.route('/price/update/<int:price_id>', methods=['POST'])
@login_required
@admin_required
def edit_coin_price(price_id):
    coin_price = CoinPrice.query.get_or_404(price_id)
    coin_price.coin_currency_id = request.form.get('coin_currency_id', coin_price.coin_currency_id)
    coin_price.quote_currency_id = request.form.get('quote_currency_id', coin_price.quote_currency_id)
    coin_price.price = request.form.get('price', coin_price.price)
    coin_price.datetime_update = request.form.get('datetime_update', coin_price.datetime_update)
    db.session.commit()
    return redirect(url_for('currency.list_coin_prices'))

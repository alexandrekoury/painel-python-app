from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db
from models.instrument import InstrumentClosingPrice
from decorators.auth import login_required, admin_required
from datetime import datetime
from sqlalchemy import func

instrument_bp = Blueprint('instrument', __name__, url_prefix='/instrument')
limiter = Limiter(key_func=get_remote_address)

# Instrument Closing Prices

@instrument_bp.route('/closing_prices', methods=['GET'])
@login_required
@admin_required
def list_instrument_closing_prices():
    query = InstrumentClosingPrice.query

    start_date = request.args.get('start_date')
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InstrumentClosingPrice.closing_date >= start_dt)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(InstrumentClosingPrice.closing_date <= end_dt)
        except ValueError:
            pass
    
    instrument = request.args.get('instrument')
    if instrument:
        try:
            query = query.filter(InstrumentClosingPrice.instrument.ilike(f"%{instrument}%"))
        except ValueError:
            pass

    instrument_closing_prices = query.order_by(InstrumentClosingPrice.closing_date.desc())
    limit = request.args.get('limit', type=int)
    if limit is not None:
        instrument_closing_prices = instrument_closing_prices.limit(limit)
    else:
        instrument_closing_prices = instrument_closing_prices.limit(50)

    instrument_closing_prices = instrument_closing_prices.all()
    return render_template('instrument/closing_prices.html', instrument_closing_prices=instrument_closing_prices, start_date=start_date, end_date=end_date, limit=limit)

@instrument_bp.route('/closing_price/edit/<int:closing_price_id>', methods=['GET'])
@login_required
@admin_required
def edit_closing_price_form(closing_price_id):
    closing_price = InstrumentClosingPrice.query.get_or_404(closing_price_id)
    currencies = InstrumentClosingPrice.query.all()
    return render_template('instrument/edit_closing_price.html', closing_price=closing_price, currencies=currencies)

@instrument_bp.route('/closing_price/update/<int:closing_price_id>', methods=['POST'])
@login_required
@admin_required
def edit_closing_price(closing_price_id):
    closing_price = InstrumentClosingPrice.query.get_or_404(closing_price_id)
    closing_price.price = request.form.get('price', closing_price.price)
    closing_price.instrument = request.form.get('instrument', closing_price.instrument)
    closing_price.exchange = request.form.get('exchange', closing_price.exchange)
    closing_price.closing_date = request.form.get('closing_date', closing_price.closing_date)
    closing_price.update_time = request.form.get('update_time', closing_price.update_time)
    db.session.commit()
    return redirect(url_for('instrument.list_instrument_closing_prices'))
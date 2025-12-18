from flask import Blueprint, render_template, redirect, url_for
from decorators.auth import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
@login_required
def index():
    return redirect(url_for('dashboard.index'))

@main_bp.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html")
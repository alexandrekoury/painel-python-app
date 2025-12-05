from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from functools import wraps
from datetime import datetime
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----- OAuth Google -----
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v2/",
    userinfo_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url=f'https://accounts.google.com/.well-known/openid-configuration'
)


# ------------ Model ------------ #
class Investor(db.Model):
    __tablename__="tbl_investors"
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(30))
    username = db.Column(db.String(50))

class User(db.Model):
    __tablename__ = "tbl_users"

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    picture = db.Column(db.Text)
    role = db.Column(db.String(50), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InvestorTransaction(db.Model):
    __tablename__ = "tbl_investor_transactions"

    id = db.Column(db.Integer, primary_key=True)
    effective_datetime = db.Column(db.DateTime)
    received_datetime = db.Column(db.DateTime)
    transaction_type = db.Enum('red_cash', 'red_kind', 'dep_cash', 'dep_kind')
    cash_amount = db.Column(db.Float)
    kind_amount = db.Column(db.Float)
    transaction_nav = db.Column(db.Float)
    investor_id = db.Column(db.Integer, db.ForeignKey('tbl_investors.id'))
    cash_currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    kind_currency_id = db.Column(db.Integer, db.ForeignKey('tbl_currencies.id'))
    investor = db.relationship('Investor', backref=db.backref('transactions', lazy=True))
    cash_currency = db.relationship('Currency', foreign_keys=[cash_currency_id])
    kind_currency = db.relationship('Currency', foreign_keys=[kind_currency_id])
    
class Currency(db.Model):
    __tablename__ = "tbl_currencies"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)

# ----- Proteção de rotas -----
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session["user"].get("role") != "admin":
            return redirect(url_for("unauthorized"))
        return f(*args, **kwargs)
    return decorated_function


# ======== Rotas de Autenticação Google ===========

@app.route("/login")
def login():
    redirect_uri = url_for("auth_google", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/google")
def auth_google():
    token = google.authorize_access_token()
    userinfo = google.get("userinfo").json()
    print(userinfo)
    google_id = userinfo.get("id")
    
    user = User.query.filter_by(google_id=google_id).first()
    
    if user is None:
        user = User(
            google_id=google_id,
            email=userinfo["email"],
            name=userinfo["name"],
            picture=userinfo.get("picture")
        )
        db.session.add(user)
        db.session.commit()
    else:
        user.name = userinfo["name"]
        user.picture = userinfo.get("picture")
        db.session.commit()

    session["user"] = {
        "id": user.id,
        "google_id": user.google_id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture,
        "role": user.role
    }

    return redirect("/")

@app.route("/logout")
@login_required
def logout():
    session.pop("user", None)
    return redirect("/")

# ------------ Rotas ------------ #

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html")

@app.route('/investors')
@login_required
@admin_required
def investors():
    investors = Investor.query.all()
    user = session.get('user')
    return render_template('investors.html', investors=investors, user=user)


@app.route('/investor_transactions')
@login_required
@admin_required
def investor_transactions():
    transactions = InvestorTransaction.query.all()
    user = session.get('user')
    return render_template('investor_transactions.html', transactions=transactions, user=user)

@app.route('/create', methods=['POST'])
@login_required
@admin_required
def create():
    name = request.form['alias']
    username = request.form['username']
    new_investor = Investor(alias=name, username=username)
    db.session.add(new_investor)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:investor_id>')
@login_required
@admin_required
def edit(investor_id):
    investor = Investor.query.get_or_404(investor_id)
    user = session.get('user')
    return render_template('edit_investor.html', investor=investor, user=user)

@app.route('/update/<int:investor_id>', methods=['POST'])
@login_required
@admin_required
def update(investor_id):
    investor = Investor.query.get_or_404(investor_id)
    investor.name = request.form['name']
    investor.description = request.form['description']
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:investor_id>')
@login_required
@admin_required
def delete(investor_id):
    investor = Investor.query.get_or_404(investor_id)
    db.session.delete(investor)
    db.session.commit()
    return redirect(url_for('index'))

# --- Inicia o servidor localmente --- #
if __name__ == '__main__':
    app.run(debug=True)

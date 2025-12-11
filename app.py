from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, ENV_TYPE
from models import db
from routes import register_blueprints
from routes.auth import init_oauth

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET

# Session security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Initialize extensions
db.init_app(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
oauth = init_oauth(app)

# Register blueprints
register_blueprints(app)

if __name__ == "__main__":
    app.run(debug=True if ENV_TYPE == "dev" else False)
from flask import Blueprint, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
from flask_limiter.util import get_remote_address
from models import db
from models.user import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def init_oauth(app):
    oauth = OAuth(app)
    global google
    google = oauth.register(
        name="google",
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        api_base_url="https://www.googleapis.com/oauth2/v2/",
        userinfo_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
        client_kwargs={"scope": "openid email profile"},
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
    )
    return oauth

@auth_bp.route("/login")
def login():
    # Check if user is already logged in
    if "user" in session:
        return redirect(url_for("main.index"))
    return render_template("login.html")

@auth_bp.route("/login/google")
def login_google():
    redirect_uri = url_for("auth.auth_google", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route("/auth/google")
def auth_google():
    token = google.authorize_access_token()
    userinfo = google.get("userinfo").json()
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

    session.permanent = True
    session["user"] = {
        "id": user.id,
        "google_id": user.google_id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture,
        "role": user.role
    }

    return redirect(url_for("main.index"))

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))
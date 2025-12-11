from routes.auth import auth_bp
from routes.investor import investor_bp
from routes.main import main_bp
from routes.exchange import exchange_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(investor_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(exchange_bp)
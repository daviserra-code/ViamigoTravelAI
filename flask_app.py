from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Configure session to be permanent
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=7)  # Session lasts 7 days
app.config['SESSION_PERMANENT'] = True
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
    }

    # Initialize database
    db = SQLAlchemy(app)
else:
    # Fallback for development without database
    db = None
    logging.warning("No DATABASE_URL found, running without database")

# Initialize Flask-Login
if db:
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = '/auth/login'
    login_manager.login_message = 'Effettua il login per accedere a questa pagina.'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(user_id)

# Defer table creation to avoid circular imports
def create_tables():
    if db:
        with app.app_context():
            try:
                import models  # noqa: F401
                db.create_all()
                logging.info("Database tables created")
            except Exception as e:
                logging.error(f"Error creating tables: {e}")
    else:
        logging.warning("Skipping table creation - no database configured")

from detail_handler import detail_bp

# Register blueprints
app.register_blueprint(detail_bp)
from dashboard_routes import dashboard_bp
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, jsonify
from datetime import timedelta
from ai_companion_routes import ai_companion_bp
from detail_handler import detail_bp
from admin_routes import admin_bp
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get(
    "SESSION_SECRET", "dev-secret-key-change-in-production-very-long-secure-key-12345")

# Configure session - NO Flask-Session, use default Flask sessions (client-side signed cookies)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_NAME'] = 'viamigo_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = None  # Most permissive - allow all
# Set to True in production with HTTPS
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_DOMAIN'] = None  # Same domain only

# TEMPORARILY DISABLE ProxyFix to test if it's blocking session cookies
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Remember cookie configuration
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = None
app.config['REMEMBER_COOKIE_SECURE'] = False

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

    # Unauthorized handler for debugging
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request
        print(f"[DEBUG] Unauthorized access attempt")
        print(
            f"[DEBUG] current_user.is_authenticated: {current_user.is_authenticated}")
        print(f"[DEBUG] Request path: {request.path}")
        print(f"[DEBUG] Session contents: {dict(session)}")
        return jsonify({'error': 'Unauthorized - login required'}), 401

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        print(f"[DEBUG] load_user called with user_id: {user_id}")
        user = User.query.get(user_id)
        if user:
            print(f"[DEBUG] load_user found user: {user.email}")
        else:
            print(f"[DEBUG] load_user - user not found for id: {user_id}")
        return user

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


# Register blueprints
app.register_blueprint(detail_bp)
app.register_blueprint(ai_companion_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)  # Admin routes for cache population


# Debug middleware to log session info on every request
@app.before_request
def log_request_info():
    from flask import request
    if request.path in ['/dashboard', '/auth/login', '/auth/check-session']:
        print(f"\n[DEBUG] === Request to {request.path} ===")
        print(f"[DEBUG] Method: {request.method}")
        print(f"[DEBUG] Cookies: {request.cookies}")
        print(f"[DEBUG] Session before request: {dict(session)}")
        if current_user.is_authenticated:
            print(
                f"[DEBUG] current_user: {current_user.email} (authenticated)")
        else:
            print(f"[DEBUG] current_user: Not authenticated")
        print(f"[DEBUG] === End request info ===\n")


@app.after_request
def log_response_info(response):
    from flask import request
    if request.path in ['/dashboard', '/auth/login', '/auth/check-session']:
        print(f"\n[DEBUG] === Response for {request.path} ===")
        print(f"[DEBUG] Status: {response.status}")
        # Get ALL headers, not just Set-Cookie
        all_headers = list(response.headers)
        print(f"[DEBUG] All headers: {all_headers}")
        set_cookie_headers = response.headers.getlist('Set-Cookie')
        if set_cookie_headers:
            print(f"[DEBUG] Set-Cookie headers ({len(set_cookie_headers)}):")
            for cookie in set_cookie_headers:
                print(f"[DEBUG]   - {cookie[:150]}...")
        else:
            print(f"[DEBUG] NO Set-Cookie headers!")
        print(f"[DEBUG] Session after request: {dict(session)}")
        print(f"[DEBUG] Session modified: {session.modified}")

        # MANUALLY SAVE SESSION if modified
        if session.modified:
            print(f"[DEBUG] Session was modified - forcing Flask to save it...")
            from flask import current_app
            session_interface = current_app.session_interface
            print(f"[DEBUG] Session interface: {session_interface}")
            print(
                f"[DEBUG] Should set cookie: {session_interface.should_set_cookie(current_app, session)}")

            # FORCE save the session manually
            session_interface.save_session(current_app, session, response)
            print(f"[DEBUG] save_session() called manually")

            # Check if cookie was added
            new_cookies = response.headers.getlist('Set-Cookie')
            if new_cookies:
                print(
                    f"[DEBUG] ✅ Set-Cookie added: {len(new_cookies)} cookies")
                for c in new_cookies:
                    print(f"[DEBUG]   Cookie: {c[:150]}...")
            else:
                print(f"[DEBUG] ❌ STILL no cookies after manual save!")

        print(f"[DEBUG] === End response info ===\n")
    return response

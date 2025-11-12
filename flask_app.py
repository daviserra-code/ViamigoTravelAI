from ai_advanced_features import ai_advanced_bp
from advanced_routes import advanced_bp
from ux_routes import ux_bp
from dashboard_routes import dashboard_bp
from data_intelligence import data_intelligence_bp
from analytics_routes import analytics_dashboard_bp
from role_based_access import role_based_access_bp, role_manager
from comprehensive_attractions_api import comprehensive_attractions_bp
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, jsonify
from datetime import timedelta
from ai_companion_routes import ai_companion_bp
from detail_handler import detail_bp
from admin_routes import admin_bp
from performance_monitor import performance_bp, performance_monitor
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

# Database configuration - FORCE LOAD .env if DATABASE_URL missing
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Force reload .env file
    load_dotenv(override=True)
    database_url = os.environ.get("DATABASE_URL")

if not database_url:
    # HARDCODE as fallback to stop this recurring issue
    database_url = "postgresql://neondb_owner:npg_r9e2PGORqsAx@ep-ancient-morning-a6us6om6.us-west-2.aws.neon.tech/neondb?sslmode=require"
    print("🔧 Using hardcoded DATABASE_URL as fallback")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
        "connect_args": {
            "connect_timeout": 10,  # 10 second timeout
            "options": "-c statement_timeout=30000"  # 30 second statement timeout
        }
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
                logging.info("Attempting to create database tables...")
                import models  # noqa: F401
                db.create_all()
                logging.info("✅ Database tables created successfully")
            except Exception as e:
                logging.error(f"❌ Error creating tables: {e}")
                logging.error(f"   Exception type: {type(e).__name__}")
                import traceback
                logging.error(traceback.format_exc())
    else:
        logging.warning("⚠️  Skipping table creation - no database configured")


# NOTE: All blueprint registrations are handled in run.py
# Don't register blueprints here to avoid duplicate registration errors
# The following blueprints are registered in run.py:
# - auth_bp, create_profile_bp, pure_instant_bp, advanced_bp, image_routes_bp, demo_bp
# The following blueprints are registered in flask_app.py itself (keep these):
# - detail_bp, ai_companion_bp, dashboard_bp, admin_bp, performance_bp, ux_bp,
#   ai_advanced_bp, data_intelligence_bp, analytics_dashboard_bp, role_based_access_bp,
#   comprehensive_attractions_bp

# Register blueprints that are NOT in run.py
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


# Register performance monitoring blueprint
app.register_blueprint(performance_bp, url_prefix='/api')

# Register UX enhancement routes
app.register_blueprint(ux_bp)

# Register AI advanced features
app.register_blueprint(ai_advanced_bp)

# NOTE: advanced_bp is registered in run.py - don't register here

# Register data intelligence analytics
app.register_blueprint(data_intelligence_bp)

# Register analytics dashboard routes
app.register_blueprint(analytics_dashboard_bp)

# Register role-based access control
app.register_blueprint(role_based_access_bp)

# Register comprehensive attractions API
app.register_blueprint(comprehensive_attractions_bp)

# Import and register main routes for planner and core functionality
try:
    # NOTE: Temporarily commenting out routes.py due to duplicate route conflicts
    # import routes  # This should register the main routes
    logging.info("✅ Main routes import skipped (avoiding duplicates)")
except ImportError as e:
    logging.warning(f"❌ Main routes not available: {e}")

# NOTE: All main routes (/, /planner, etc.) are defined in routes.py
# Don't add them here to avoid endpoint collisions

# Add logout route if not in auth blueprint
try:
    logout_exists = any('/logout' in str(rule)
                        for rule in app.url_map.iter_rules())
    if not logout_exists:
        @app.route('/logout')
        @app.route('/auth/logout')
        def logout():
            """Logout user and redirect"""
            from flask import redirect, session
            from flask_login import logout_user

            # Clear session
            session.clear()

            # Logout user if using Flask-Login
            try:
                logout_user()
            except:
                pass

            return redirect('/auth/login')
except Exception as e:
    logging.warning(f"Logout route issue: {e}")

# NOTE: All API routes (/api/routes/*, etc.) are defined in routes.py
# Don't add them here to avoid endpoint collisions

# Register enhanced images API - simplified version
try:
    from simple_enhanced_images import enhanced_images_bp
    app.register_blueprint(enhanced_images_bp)
    logging.info("✅ Simple Enhanced images API registered successfully")
except ImportError as e:
    logging.warning(f"❌ Enhanced images API not available: {e}")
    # Create fallback enhanced images route directly in main app

    @app.route('/api/images/classify', methods=['POST'])
    def enhanced_images_fallback():
        from flask import request, jsonify
        try:
            data = request.get_json()
            title = data.get('title', '')
            context = data.get('context', '')

            # Use HARDCODED system first for reliability - FIX WRONG THUMBNAILS
            from simple_enhanced_images import classify_attraction_simple, get_enhanced_image

            # Try hardcoded classification first
            classification = classify_attraction_simple(title, context)

            if classification.get('confidence', 0) >= 0.8:
                # Use hardcoded system
                image_url = get_enhanced_image(
                    title, classification.get('city', 'roma'))
                return jsonify({
                    "classification": classification,
                    "image": {
                        "confidence": classification.get('confidence', 0.8),
                        "url": image_url
                    },
                    "success": True,
                    "source": "hardcoded"
                })
            else:
                # Fallback to intelligent classifier
                from intelligent_image_classifier import classify_image_intelligent
                result = classify_image_intelligent(title, context)

                return jsonify({
                    "classification": result.get('classification', {}),
                    "image": {
                        "confidence": result.get('classification', {}).get('confidence', 0.5),
                        "url": result.get('image_url', 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=800')
                    },
                    "success": result.get('success', True),
                    "source": result.get('source', 'intelligent'),
                    "coordinates": result.get('coordinates'),
                    "wikidata_id": result.get('wikidata_id')
                })

        except Exception as e:
            logging.error(f"❌ Image classification error: {e}")
            # Fallback to basic response
            return jsonify({
                "classification": {"attraction": title, "city": "Unknown", "confidence": 0.3},
                "image": {"confidence": 0.3, "url": "https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=800"},
                "success": True,
                "source": "fallback",
                "error": str(e)
            })

        logging.info("✅ Enhanced images fallback route registered")

# Root route is defined in routes.py (with authentication logic)
# Don't define it here to avoid endpoint collision


# Import main routes after all app setup is complete (to avoid circular imports)
if __name__ == '__main__':
    # Create tables before starting
    create_tables()
    app.run(host='0.0.0.0', port=5000, debug=False)

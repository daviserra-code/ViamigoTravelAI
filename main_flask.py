from flask_app import app, create_tables
import routes  # noqa: F401

# Registra blueprint autenticazione
from auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# Registra blueprint dashboard
from dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp)

# Registra blueprint creazione profilo
from create_profile_routes import create_profile_bp
app.register_blueprint(create_profile_bp)

if __name__ == "__main__":
    # Create tables after all imports are complete
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)
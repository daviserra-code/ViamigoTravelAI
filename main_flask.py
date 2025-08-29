from flask_app import app, create_tables
import routes  # noqa: F401
import advanced_routes  # Nuove funzionalità innovative

# Registra blueprint autenticazione
from auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# Registra blueprint dashboard
from dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp)

# Registra blueprint creazione profilo
from create_profile_routes import create_profile_bp
app.register_blueprint(create_profile_bp)

# Registra blueprint lightning routes (instant response + background AI)
from lightning_routes import lightning_bp
app.register_blueprint(lightning_bp)

# Replit OAuth già registrato in routes.py

if __name__ == "__main__":
    # Create tables after all imports are complete
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)
from flask_app import app, create_tables
import routes  # noqa: F401

# Registra blueprint autenticazione
from auth_routes import auth_bp
app.register_blueprint(auth_bp)

# Registra blueprint dashboard
from dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    # Create tables after all imports are complete
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)
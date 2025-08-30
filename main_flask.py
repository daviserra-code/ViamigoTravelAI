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

# Registra blueprint pure instant routes (true dynamic instant)
from pure_instant_routes import pure_instant_bp
app.register_blueprint(pure_instant_bp)

# Registra blueprint AI companion routes (genuine AI features)
from ai_companion_routes import ai_companion_bp
app.register_blueprint(ai_companion_bp)

# Registra blueprint advanced routes
from advanced_routes import advanced_bp
app.register_blueprint(advanced_bp)
print("🚀 Advanced Routes caricato - Piano B, Scoperte Intelligenti, Diario AI attivi!")

# Replit OAuth già registrato in routes.py

if __name__ == "__main__":
    # Create tables after all imports are complete
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)
"""
🔧 RUN.PY INTEGRATION GUIDE
How to integrate the enhanced scraping system into run.py
"""

# ============================================================
# STEP 1: Add imports at the top of run.py
# ============================================================

import atexit
from enhanced_integration import (
    create_enhanced_scraping_system,
    register_enhanced_routes
)


# ============================================================
# STEP 2: Initialize the enhanced scraping system
# ============================================================

# After creating the Flask app and database
# Find the section that looks like:
#
# app = Flask(__name__)
# db = SQLAlchemy(app)
#
# Then add:

scraping_system = create_enhanced_scraping_system(app, db.session)


# ============================================================
# STEP 3: Register enhanced admin routes
# ============================================================

# After registering other blueprints/routes
# Find sections like:
#
# app.register_blueprint(auth_routes)
# app.register_blueprint(dashboard_routes)
#
# Then add:

register_enhanced_routes(app, scraping_system)


# ============================================================
# STEP 4: Graceful shutdown on exit
# ============================================================

# At the end of run.py, before app.run() or similar:


@atexit.register
def shutdown_scraping_system():
    """Gracefully shutdown scheduler on exit"""
    if 'SCRAPING_SYSTEM' in app.config:
        app.config['SCRAPING_SYSTEM'].shutdown()


# ============================================================
# COMPLETE EXAMPLE - Full run.py Integration
# ============================================================

"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from enhanced_integration import create_enhanced_scraping_system, register_enhanced_routes
import atexit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'
db = SQLAlchemy(app)

# Import your existing routes
from auth_routes import auth_bp
from dashboard_routes import dashboard_bp
from ai_companion_routes import ai_bp

# Register existing routes
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(ai_bp)

# ✨ NEW: Initialize enhanced scraping system
scraping_system = create_enhanced_scraping_system(app, db.session)

# ✨ NEW: Register enhanced admin routes
register_enhanced_routes(app, scraping_system)

# ✨ NEW: Graceful shutdown
@atexit.register
def shutdown_scraping_system():
    if 'SCRAPING_SYSTEM' in app.config:
        app.config['SCRAPING_SYSTEM'].shutdown()

if __name__ == '__main__':
    app.run(debug=True, port=3000)
"""


# ============================================================
# STEP 5: Test the integration
# ============================================================

# 1. Start the server:
#    python run.py

# 2. Test the enhanced dashboard:
#    curl http://localhost:3000/api/admin/enhanced/dashboard

# 3. Trigger intelligent scraping:
#    curl -X POST http://localhost:3000/api/admin/enhanced/scrape \
#         -H "Content-Type: application/json" \
#         -d '{"strategy": "seasonal"}'

# 4. Check budget status:
#    curl http://localhost:3000/api/admin/enhanced/budget-status


# ============================================================
# OPTIONAL: CLI Usage (without Flask)
# ============================================================

# You can also run the enhanced scraping directly from CLI:

"""
python -c "
from enhanced_integration import cli_run_enhanced_scraping
cli_run_enhanced_scraping('comprehensive')
"
"""

# Or create a standalone script:

"""
# scrape.py
from enhanced_integration import cli_run_enhanced_scraping
import sys

strategy = sys.argv[1] if len(sys.argv) > 1 else 'comprehensive'
cli_run_enhanced_scraping(strategy)
"""

# Then run:
# python scrape.py seasonal
# python scrape.py cost_optimized


# ============================================================
# TROUBLESHOOTING
# ============================================================

# Issue 1: APScheduler not found
# Solution: pip install APScheduler==3.10.4

# Issue 2: Wikipedia API not found
# Solution: pip install wikipedia-api==0.7.2

# Issue 3: Scheduler not starting
# Solution: Check logs for errors, ensure db.session is valid

# Issue 4: Budget alerts not working
# Solution: Verify analytics is recording Apify calls correctly

# Issue 5: Import errors
# Solution: Ensure 'enhancements' directory exists and has __init__.py

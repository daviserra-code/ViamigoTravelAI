"""
INTEGRATION EXAMPLE for Proactive Scraping System
Add these changes to your existing files
"""

# ============================================================================
# 1. UPDATE requirements.txt or pyproject.toml
# ============================================================================

# Add to requirements.txt:
"""
APScheduler==3.10.4
"""

# Or add to pyproject.toml:
"""
[tool.uv.dependencies]
apscheduler = "^3.10.4"
"""


# ============================================================================
# 2. UPDATE run.py (or main.py)
# ============================================================================

from apscheduler.schedulers.background import BackgroundScheduler
from flask_app import app, db
from proactive_scraping import (
    schedule_proactive_scraping,
    register_proactive_routes,
    get_database_health_report
)
import logging
import click
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Schedule proactive scraping every 6 hours
scheduler.add_job(
    func=schedule_proactive_scraping,
    trigger="interval",
    hours=6,
    id='proactive_scraping_job',
    replace_existing=True
)

logger.info("✅ Proactive scraping scheduler initialized")

# Optional: Run once on startup to warm cache


@app.before_first_request
def warm_cache_on_startup():
    """Warm cache when app starts"""
    try:
        logger.info("🔥 Warming cache on startup...")
        from proactive_scraping import ProactiveScrapingManager

        manager = ProactiveScrapingManager()
        result = manager.run_proactive_scraping(
            max_scrapes=3, prioritize_users=True)

        logger.info(
            f"✅ Startup cache warming: {result['successful']}/{result['total_attempted']}")
    except Exception as e:
        logger.error(f"❌ Startup cache warming failed: {e}")


# Register admin routes
register_proactive_routes(app)

# Add admin dashboard route


@app.route('/admin/scraping')
def admin_scraping_dashboard():
    """Admin dashboard for scraping management"""
    from flask import send_from_directory
    return send_from_directory('static', 'admin_scraping.html')


# Shutdown scheduler gracefully
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)


# ============================================================================
# 3. ADD HEALTH CHECK ENDPOINT (optional)
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint including scraping system status"""
    from flask import jsonify

    health = get_database_health_report()

    return jsonify({
        'status': 'ok',
        'database': health['status'],
        'scraping_system': 'active',
        'total_cities': health['stats'].get('total_cities', 0),
        'total_places': health['stats'].get('total_places', 0)
    })


# ============================================================================
# 4. UPDATE models.py (if needed - add indexes for performance)
# ============================================================================

# In PlaceCache model, add indexes:
"""
class PlaceCache(db.Model):
    __tablename__ = 'place_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), nullable=False, unique=True, index=True)
    place_name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), index=True)  # Add index
    country = db.Column(db.String(100))
    place_data = db.Column(db.Text)
    priority_level = db.Column(db.String(50), default='dynamic')
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Add index
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Add index
"""


# ============================================================================
# 5. CUSTOM SCHEDULER CONFIGURATIONS (advanced)
# ============================================================================

# Different schedules for different times:

# Peak hours (9 AM - 9 PM): Every 4 hours
scheduler.add_job(
    func=schedule_proactive_scraping,
    trigger="cron",
    hour='9-21/4',  # Every 4 hours between 9 AM and 9 PM
    id='peak_scraping'
)

# Off-peak hours: Every 8 hours
scheduler.add_job(
    func=schedule_proactive_scraping,
    trigger="cron",
    hour='0-8/8,22',  # Every 8 hours off-peak
    id='offpeak_scraping'
)

# Weekend intensive scraping
scheduler.add_job(
    func=lambda: schedule_proactive_scraping(),
    trigger="cron",
    day_of_week='sat,sun',
    hour='2',  # 2 AM on weekends
    id='weekend_scraping'
)


# ============================================================================
# 6. MONITORING AND ALERTS (optional)
# ============================================================================

def send_alert_email(subject, message):
    """Send alert email when issues detected"""
    # Implement email sending logic
    pass


def monitor_scraping_health():
    """Monitor scraping system health"""
    from proactive_scraping import get_database_health_report

    health = get_database_health_report()

    if health['status'] == 'needs_attention':
        send_alert_email(
            "Scraping System Alert",
            f"Database needs attention: {health['cities_needing_refresh']} cities need refresh"
        )

    if health['stats'].get('average_age_days', 0) > 90:
        send_alert_email(
            "Cache Aging Alert",
            f"Cache is aging: average {health['stats']['average_age_days']:.1f} days old"
        )


# Schedule health monitoring daily
scheduler.add_job(
    func=monitor_scraping_health,
    trigger="cron",
    hour=8,  # 8 AM daily
    id='health_monitoring'
)


# ============================================================================
# 7. CLI COMMANDS (optional - for manual control)
# ============================================================================


@click.group()
def scraping_cli():
    """Scraping management commands"""
    pass


@scraping_cli.command()
@click.option('--cities', default=5, help='Number of cities to scrape')
def scrape(cities):
    """Manually trigger scraping"""
    from proactive_scraping import ProactiveScrapingManager

    manager = ProactiveScrapingManager()
    result = manager.run_proactive_scraping(max_scrapes=cities)

    click.echo(
        f"✅ Scraped {result['successful']}/{result['total_attempted']} cities")


@scraping_cli.command()
def status():
    """Show scraping system status"""
    from proactive_scraping import get_database_health_report

    health = get_database_health_report()

    click.echo(f"Status: {health['status']}")
    click.echo(f"Total cities: {health['stats'].get('total_cities', 0)}")
    click.echo(f"Total places: {health['stats'].get('total_places', 0)}")
    click.echo(
        f"Average age: {health['stats'].get('average_age_days', 0):.1f} days")

    if health['recommendations']:
        click.echo("\nRecommendations:")
        for rec in health['recommendations']:
            click.echo(f"  - {rec}")


if __name__ == '__main__':
    scraping_cli()


# ============================================================================
# 8. USAGE EXAMPLES
# ============================================================================

# Run from command line:
"""
# Install dependencies
pip install apscheduler

# Manual scraping
python integration_example.py scrape --cities 10

# Check status
python integration_example.py status

# Start the app (with automatic scraping)
python run.py
"""

# Access the admin dashboard:
"""
http://localhost:3000/admin/scraping
"""

# API calls:
"""
# Get status
curl http://localhost:3000/admin/scraping/status

# Trigger scraping
curl -X POST http://localhost:3000/admin/scraping/run \
  -H "Content-Type: application/json" \
  -d '{"max_scrapes": 10, "prioritize_users": true}'

# Get coverage
curl http://localhost:3000/admin/scraping/coverage
"""


# ============================================================================
# 9. ENVIRONMENT VARIABLES (add to .env)
# ============================================================================

"""
# Scraping Configuration
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_HOURS=6
SCRAPING_MAX_PER_RUN=5
SCRAPING_PRIORITIZE_USERS=true

# Cache Configuration
CACHE_DURATION_POPULAR_DAYS=1
CACHE_DURATION_MEDIUM_DAYS=7
CACHE_DURATION_RARE_DAYS=30
"""


# ============================================================================
# 10. DATABASE MIGRATION (if you added indexes)
# ============================================================================

"""
# Create migration
flask db migrate -m "Add indexes to PlaceCache for better performance"

# Apply migration
flask db upgrade
"""

"""
🚀 COMPREHENSIVE ENHANCEMENT INTEGRATION
Master integration file for all enhancement modules
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class EnhancedProactiveScrapingSystem:
    """
    Complete proactive scraping system with all enhancements integrated
    """
    
    def __init__(self, db_session, apify_client=None):
        self.db = db_session
        self.apify = apify_client
        
        # Initialize all enhancement modules
        self._init_modules()
        
        # Scheduler for background tasks
        self.scheduler = None
        
        logger.info("🚀 Enhanced Proactive Scraping System initialized")
    
    def _init_modules(self):
        """Initialize all enhancement modules"""
        from enhancements.seasonal_intelligence import SeasonalIntelligence, EventBasedIntelligence
        from enhancements.ml_predictions import UserBehaviorAnalyzer, CollaborativeFiltering
        from enhancements.analytics import CacheAnalytics, CostMonitor, QualityValidator
        from enhancements.multi_source import MultiSourceAggregator, DataEnrichmentPipeline
        from enhancements.geographic_clustering import GeographicClusterer, BatchScrapingOptimizer
        from proactive_scraping import ProactiveScrapingManager
        
        # Core scraping
        self.scraping_manager = ProactiveScrapingManager(self.db, self.apify)
        
        # Intelligence modules
        self.seasonal = SeasonalIntelligence()
        self.events = EventBasedIntelligence()
        self.behavior_analyzer = UserBehaviorAnalyzer(self.db)
        self.collaborative = CollaborativeFiltering(self.db)
        
        # Analytics
        self.analytics = CacheAnalytics(self.db)
        self.cost_monitor = CostMonitor(monthly_budget_usd=50.0)
        self.quality_validator = QualityValidator()
        
        # Data enrichment
        self.multi_source = MultiSourceAggregator(self.db, self.apify)
        self.enrichment = DataEnrichmentPipeline(self.db)
        
        # Geographic optimization
        self.geo_clusterer = GeographicClusterer()
        self.batch_optimizer = BatchScrapingOptimizer(self.geo_clusterer)
    
    def run_intelligent_scraping(self, strategy: str = 'comprehensive') -> Dict:
        """
        Run intelligent scraping with all enhancements
        
        Strategies:
        - 'comprehensive': All intelligence sources
        - 'seasonal': Focus on seasonal/events
        - 'ml_driven': Focus on ML predictions
        - 'cost_optimized': Minimize costs with clustering
        - 'emergency': Only critical gaps
        
        Returns:
            Scraping results and statistics
        """
        logger.info(f"🎯 Running intelligent scraping: {strategy}")
        
        # Check budget first
        if self.cost_monitor.should_throttle_scraping(self.analytics):
            logger.warning("⛔ Scraping throttled due to budget constraints")
            return {'status': 'throttled', 'reason': 'budget_exceeded'}
        
        results = {
            'strategy': strategy,
            'started_at': datetime.now(),
            'cities_scraped': [],
            'sources_used': [],
            'cost_usd': 0.0,
            'errors': []
        }
        
        # Gather scraping priorities from all sources
        priorities = self._gather_priorities(strategy)
        
        # Optimize scraping order
        optimized_tasks = self._optimize_tasks(priorities, strategy)
        
        # Execute scraping
        for task in optimized_tasks[:20]:  # Limit to top 20 tasks
            try:
                success = self._execute_scraping_task(task)
                if success:
                    results['cities_scraped'].append(task['city'])
                    results['cost_usd'] += 0.02  # Estimate
                    self.analytics.record_apify_call(task['city'])
            except Exception as e:
                logger.error(f"❌ Error scraping {task['city']}: {e}")
                results['errors'].append({'city': task['city'], 'error': str(e)})
        
        results['completed_at'] = datetime.now()
        results['duration_seconds'] = (results['completed_at'] - results['started_at']).total_seconds()
        
        logger.info(f"✅ Scraping complete: {len(results['cities_scraped'])} cities, ${results['cost_usd']:.2f}")
        return results
    
    def _gather_priorities(self, strategy: str) -> List[Dict]:
        """Gather scraping priorities from all intelligence sources"""
        priorities = []
        
        # Source 1: Seasonal intelligence
        if strategy in ['comprehensive', 'seasonal']:
            seasonal_cities = self.seasonal.get_upcoming_season_cities()
            for city, country, category, boost, cache_days in seasonal_cities:
                priorities.append({
                    'city': city,
                    'country': country,
                    'category': 'tourist_attraction',
                    'priority_score': boost * 10,
                    'source': 'seasonal',
                    'reason': f'Seasonal: {category}'
                })
        
        # Source 2: Events
        if strategy in ['comprehensive', 'seasonal']:
            event_cities = self.events.get_event_cities_to_scrape()
            for city, country, event_name, boost in event_cities:
                priorities.append({
                    'city': city,
                    'country': country,
                    'category': 'tourist_attraction',
                    'priority_score': boost * 12,
                    'source': 'events',
                    'reason': f'Event: {event_name}'
                })
        
        # Source 3: ML predictions
        if strategy in ['comprehensive', 'ml_driven']:
            from enhancements.ml_predictions import get_ml_based_scraping_priorities
            ml_priorities = get_ml_based_scraping_priorities(self.db)
            for ml_city in ml_priorities[:10]:
                priorities.append({
                    'city': ml_city['city'],
                    'country': 'IT',  # Assume Italy
                    'category': 'tourist_attraction',
                    'priority_score': ml_city['priority_score'] * 8,
                    'source': 'ml_prediction',
                    'reason': ', '.join(ml_city['reasons'][:2])
                })
        
        # Source 4: Database gaps
        if strategy in ['comprehensive', 'emergency']:
            gap_cities = self.scraping_manager.get_cities_needing_refresh()
            for city_data in gap_cities[:15]:
                priorities.append({
                    'city': city_data['city'],
                    'country': city_data.get('country', 'IT'),
                    'category': 'tourist_attraction',
                    'priority_score': 6,  # Medium priority
                    'source': 'database_gap',
                    'reason': city_data['reason']
                })
        
        # Source 5: User behavior patterns
        if strategy in ['comprehensive', 'ml_driven']:
            # Analyze recent user searches
            user_cities = self.scraping_manager.get_user_requested_cities(days_lookback=7)
            for city_data in user_cities[:10]:
                priorities.append({
                    'city': city_data['city'],
                    'country': 'IT',
                    'category': 'tourist_attraction',
                    'priority_score': city_data['request_count'] * 2,
                    'source': 'user_demand',
                    'reason': f"Requested {city_data['request_count']} times"
                })
        
        logger.info(f"📊 Gathered {len(priorities)} priorities from {len(set(p['source'] for p in priorities))} sources")
        return priorities
    
    def _optimize_tasks(self, priorities: List[Dict], strategy: str) -> List[Dict]:
        """Optimize task order and grouping"""
        
        # Remove duplicates, keeping highest priority
        city_best = {}
        for p in priorities:
            city = p['city']
            if city not in city_best or p['priority_score'] > city_best[city]['priority_score']:
                city_best[city] = p
        
        unique_priorities = list(city_best.values())
        
        # Apply geographic clustering if cost-optimized
        if strategy == 'cost_optimized':
            cities = [p['city'] for p in unique_priorities]
            clusters = self.geo_clusterer.create_scraping_clusters(cities, max_cluster_radius=100)
            
            # Reorder by cluster
            clustered_tasks = []
            for cluster in clusters:
                for city in cluster['cities']:
                    task = next((p for p in unique_priorities if p['city'] == city), None)
                    if task:
                        clustered_tasks.append(task)
            
            return clustered_tasks
        
        # Otherwise just sort by priority
        unique_priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        return unique_priorities
    
    def _execute_scraping_task(self, task: Dict) -> bool:
        """Execute a single scraping task"""
        city = task['city']
        category = task['category']
        
        # Check if data quality validation passes
        existing_data = self.scraping_manager._get_cached_places(city, category)
        if existing_data:
            validation = self.quality_validator.validate_city_coverage(city, existing_data)
            if validation['passed'] and validation['quality_score'] > 70:
                logger.info(f"✓ {city} has good quality data, skipping")
                self.analytics.record_cache_hit(city, category)
                return True
        
        # Execute scraping
        success = self.scraping_manager.scrape_and_cache_city(
            city=city,
            country=task.get('country', 'IT'),
            category=category
        )
        
        if success:
            self.analytics.record_cache_miss(city, category)
        
        return success
    
    def get_comprehensive_dashboard_data(self) -> Dict:
        """Get all data for admin dashboard"""
        from enhancements.analytics import create_analytics_dashboard_data
        
        dashboard = create_analytics_dashboard_data(self.db)
        
        # Add enhancement-specific data
        dashboard['intelligence'] = {
            'seasonal_cities': len(self.seasonal.get_upcoming_season_cities()),
            'active_events': len(self.events.get_active_events()),
            'ml_predictions': 'Available',
            'geographic_clusters': 'Enabled'
        }
        
        # Add cost monitoring
        budget_status = self.cost_monitor.check_budget_status(self.analytics)
        dashboard['budget_status'] = budget_status
        
        # Add quality metrics
        coverage = self.scraping_manager.get_coverage_stats()
        dashboard['coverage'] = coverage
        
        return dashboard
    
    def setup_scheduler(self):
        """Setup APScheduler for automated scraping"""
        self.scheduler = BackgroundScheduler()
        
        # Job 1: Daily comprehensive scraping (2 AM)
        self.scheduler.add_job(
            func=lambda: self.run_intelligent_scraping('comprehensive'),
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_comprehensive_scraping',
            name='Daily Comprehensive Scraping',
            replace_existing=True
        )
        
        # Job 2: Hourly emergency gaps (every hour)
        self.scheduler.add_job(
            func=lambda: self.run_intelligent_scraping('emergency'),
            trigger=CronTrigger(minute=0),
            id='hourly_emergency_scraping',
            name='Hourly Emergency Gap Filling',
            replace_existing=True
        )
        
        # Job 3: Weekly cost-optimized batch (Sunday 3 AM)
        self.scheduler.add_job(
            func=lambda: self.run_intelligent_scraping('cost_optimized'),
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='weekly_batch_scraping',
            name='Weekly Cost-Optimized Batch',
            replace_existing=True
        )
        
        # Job 4: Budget monitoring (every 6 hours)
        self.scheduler.add_job(
            func=self._monitor_budget_alerts,
            trigger=CronTrigger(hour='*/6'),
            id='budget_monitoring',
            name='Budget Monitoring',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("⏰ Scheduler started with 4 automated jobs")
    
    def _monitor_budget_alerts(self):
        """Monitor budget and send alerts"""
        budget_status = self.cost_monitor.check_budget_status(self.analytics)
        
        if budget_status['alert_level'] == 'critical':
            logger.error(f"🚨 BUDGET CRITICAL: {budget_status['budget_used_percent']:.1f}% used!")
            # TODO: Send email/Slack alert
        elif budget_status['alert_level'] == 'warning':
            logger.warning(f"⚠️ Budget warning: {budget_status['budget_used_percent']:.1f}% used")
    
    def shutdown(self):
        """Gracefully shutdown scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler shut down")


# Flask integration functions

def create_enhanced_scraping_system(app, db_session):
    """
    Create and integrate enhanced scraping system with Flask app
    
    Usage:
        from enhanced_integration import create_enhanced_scraping_system
        scraping_system = create_enhanced_scraping_system(app, db.session)
    """
    from apify_client import ApifyClient
    import os
    
    apify_client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    system = EnhancedProactiveScrapingSystem(db_session, apify_client)
    
    # Setup scheduler
    system.setup_scheduler()
    
    # Store in app context
    app.config['SCRAPING_SYSTEM'] = system
    
    logger.info("✅ Enhanced scraping system integrated with Flask app")
    return system


def register_enhanced_routes(app, scraping_system):
    """
    Register enhanced admin routes
    
    Usage:
        from enhanced_integration import register_enhanced_routes
        register_enhanced_routes(app, scraping_system)
    """
    from flask import jsonify, request
    
    @app.route('/api/admin/enhanced/dashboard')
    def enhanced_dashboard():
        """Get comprehensive dashboard data"""
        data = scraping_system.get_comprehensive_dashboard_data()
        return jsonify(data)
    
    @app.route('/api/admin/enhanced/scrape', methods=['POST'])
    def run_enhanced_scraping():
        """Trigger intelligent scraping"""
        strategy = request.json.get('strategy', 'comprehensive')
        results = scraping_system.run_intelligent_scraping(strategy)
        return jsonify(results)
    
    @app.route('/api/admin/enhanced/seasonal-cities')
    def get_seasonal_cities():
        """Get seasonal city priorities"""
        cities = scraping_system.seasonal.get_upcoming_season_cities()
        return jsonify({
            'cities': [
                {
                    'city': city,
                    'country': country,
                    'category': category,
                    'priority_boost': boost,
                    'cache_duration_days': cache_days
                }
                for city, country, category, boost, cache_days in cities
            ]
        })
    
    @app.route('/api/admin/enhanced/ml-predictions')
    def get_ml_predictions():
        """Get ML-based destination predictions"""
        from enhancements.ml_predictions import get_ml_based_scraping_priorities
        predictions = get_ml_based_scraping_priorities(scraping_system.db)
        return jsonify({'predictions': predictions[:20]})
    
    @app.route('/api/admin/enhanced/budget-status')
    def get_budget_status():
        """Get current budget status"""
        status = scraping_system.cost_monitor.check_budget_status(scraping_system.analytics)
        return jsonify(status)
    
    @app.route('/api/admin/enhanced/geographic-clusters')
    def get_geographic_clusters():
        """Get geographic clustering plan"""
        cities = request.args.get('cities', 'Roma,Milano,Firenze,Venezia,Napoli').split(',')
        plan = scraping_system.geo_clusterer.create_scraping_clusters(cities)
        return jsonify({'clusters': plan})
    
    logger.info("✅ Enhanced admin routes registered")


# CLI integration

def cli_run_enhanced_scraping(strategy: str = 'comprehensive'):
    """
    CLI command to run enhanced scraping
    
    Usage:
        python -c "from enhanced_integration import cli_run_enhanced_scraping; cli_run_enhanced_scraping('seasonal')"
    """
    from models import db
    from apify_client import ApifyClient
    import os
    
    apify_client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    system = EnhancedProactiveScrapingSystem(db.session, apify_client)
    
    results = system.run_intelligent_scraping(strategy)
    
    print(f"\n{'='*60}")
    print(f"🚀 ENHANCED SCRAPING RESULTS")
    print(f"{'='*60}")
    print(f"Strategy: {results['strategy']}")
    print(f"Cities scraped: {len(results['cities_scraped'])}")
    print(f"Cost: ${results['cost_usd']:.2f}")
    print(f"Duration: {results['duration_seconds']:.1f}s")
    print(f"Errors: {len(results['errors'])}")
    print(f"{'='*60}\n")
    
    return results

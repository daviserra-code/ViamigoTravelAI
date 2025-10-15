"""
📊 REAL-TIME ANALYTICS AND MONITORING
Tracks cache performance, costs, and system health
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CacheAnalytics:
    """Tracks cache hit rates and performance metrics"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.metrics = defaultdict(int)
        self.hourly_stats = defaultdict(lambda: {'hits': 0, 'misses': 0, 'apify_calls': 0})
    
    def record_cache_hit(self, city: str, category: str):
        """Record a cache hit"""
        self.metrics['total_cache_hits'] += 1
        hour_key = datetime.now().strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['hits'] += 1
        
        logger.debug(f"✅ Cache hit: {city} - {category}")
    
    def record_cache_miss(self, city: str, category: str):
        """Record a cache miss (triggered Apify call)"""
        self.metrics['total_cache_misses'] += 1
        hour_key = datetime.now().strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['misses'] += 1
        
        logger.debug(f"❌ Cache miss: {city} - {category}")
    
    def record_apify_call(self, city: str, cost_usd: float = 0.02):
        """Record an Apify API call with cost"""
        self.metrics['total_apify_calls'] += 1
        self.metrics['total_cost_usd'] += cost_usd
        hour_key = datetime.now().strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['apify_calls'] += 1
        
        logger.info(f"💰 Apify call: {city} - ${cost_usd:.4f}")
    
    def get_cache_hit_rate(self, hours_lookback: int = 24) -> float:
        """Calculate cache hit rate for last N hours"""
        total_hits = sum(
            stats['hits'] 
            for hour, stats in self.hourly_stats.items()
        )
        total_requests = total_hits + sum(
            stats['misses'] 
            for hour, stats in self.hourly_stats.items()
        )
        
        if total_requests == 0:
            return 0.0
        
        return (total_hits / total_requests) * 100
    
    def get_cost_summary(self, days_lookback: int = 7) -> Dict:
        """Get cost summary and projections"""
        from models import PlaceCache
        
        cutoff = datetime.now() - timedelta(days=days_lookback)
        
        # Count cache entries created in period
        new_caches = self.db.query(PlaceCache).filter(
            PlaceCache.cached_at >= cutoff
        ).count()
        
        # Estimate cost (assuming $0.02 per Apify call)
        estimated_cost = new_caches * 0.02
        daily_avg = estimated_cost / days_lookback
        monthly_projection = daily_avg * 30
        
        # Calculate savings vs. no cache
        total_cache_hits = self.metrics['total_cache_hits']
        saved_cost = total_cache_hits * 0.02
        
        return {
            'period_days': days_lookback,
            'apify_calls': new_caches,
            'actual_cost_usd': estimated_cost,
            'daily_avg_usd': daily_avg,
            'monthly_projection_usd': monthly_projection,
            'cache_hits': total_cache_hits,
            'estimated_savings_usd': saved_cost,
            'cache_hit_rate_percent': self.get_cache_hit_rate(),
            'roi_percent': (saved_cost / estimated_cost * 100) if estimated_cost > 0 else 0
        }
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        from models import PlaceCache
        from sqlalchemy import func
        
        # Database statistics
        total_cached_places = self.db.query(func.count(PlaceCache.id)).scalar()
        unique_cities = self.db.query(func.count(func.distinct(PlaceCache.city))).scalar()
        
        # Freshness analysis
        now = datetime.now()
        fresh_count = self.db.query(PlaceCache).filter(
            PlaceCache.cached_at >= now - timedelta(days=7)
        ).count()
        
        stale_count = self.db.query(PlaceCache).filter(
            PlaceCache.cached_at < now - timedelta(days=30)
        ).count()
        
        return {
            'total_cached_places': total_cached_places,
            'unique_cities': unique_cities,
            'fresh_caches_7d': fresh_count,
            'stale_caches_30d': stale_count,
            'cache_hit_rate_percent': self.get_cache_hit_rate(),
            'total_cache_hits': self.metrics['total_cache_hits'],
            'total_cache_misses': self.metrics['total_cache_misses'],
            'total_apify_calls': self.metrics['total_apify_calls'],
            'freshness_score': (fresh_count / total_cached_places * 100) if total_cached_places > 0 else 0
        }


class CostMonitor:
    """Monitors and alerts on Apify costs"""
    
    def __init__(self, monthly_budget_usd: float = 50.0):
        self.monthly_budget = monthly_budget_usd
        self.alert_threshold = 0.8  # Alert at 80% of budget
    
    def check_budget_status(self, analytics: CacheAnalytics) -> Dict:
        """Check current spending vs. budget"""
        cost_summary = analytics.get_cost_summary(days_lookback=30)
        
        current_spend = cost_summary['actual_cost_usd']
        projected_spend = cost_summary['monthly_projection_usd']
        
        budget_used_percent = (current_spend / self.monthly_budget) * 100
        projected_budget_percent = (projected_spend / self.monthly_budget) * 100
        
        status = {
            'monthly_budget_usd': self.monthly_budget,
            'current_spend_usd': current_spend,
            'projected_monthly_usd': projected_spend,
            'budget_used_percent': budget_used_percent,
            'projected_budget_percent': projected_budget_percent,
            'days_until_budget_exceeded': None,
            'alert_level': 'ok'
        }
        
        # Calculate days until budget exceeded
        daily_avg = cost_summary['daily_avg_usd']
        if daily_avg > 0:
            remaining_budget = self.monthly_budget - current_spend
            days_remaining = remaining_budget / daily_avg
            status['days_until_budget_exceeded'] = int(days_remaining)
        
        # Set alert level
        if budget_used_percent >= 100:
            status['alert_level'] = 'critical'
        elif budget_used_percent >= self.alert_threshold * 100:
            status['alert_level'] = 'warning'
        elif projected_budget_percent > 100:
            status['alert_level'] = 'watch'
        
        return status
    
    def should_throttle_scraping(self, analytics: CacheAnalytics) -> bool:
        """Determine if scraping should be throttled to save costs"""
        budget_status = self.check_budget_status(analytics)
        
        # Throttle if over budget or will exceed in <3 days
        if budget_status['alert_level'] == 'critical':
            logger.warning("🚨 BUDGET EXCEEDED - Throttling scraping!")
            return True
        
        if budget_status['days_until_budget_exceeded'] and budget_status['days_until_budget_exceeded'] < 3:
            logger.warning(f"⚠️ Budget will be exceeded in {budget_status['days_until_budget_exceeded']} days - Throttling!")
            return True
        
        return False


class QualityValidator:
    """Validates quality of scraped data"""
    
    def __init__(self):
        self.validation_rules = {
            'min_places_per_city': 10,
            'max_places_per_city': 200,
            'min_rating': 0.0,
            'max_rating': 5.0,
            'required_fields': ['name', 'address', 'rating']
        }
    
    def validate_place_data(self, place_data: Dict) -> Dict:
        """
        Validate a single place entry
        
        Returns:
            {'valid': bool, 'errors': [], 'warnings': []}
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.validation_rules['required_fields']:
            if field not in place_data or not place_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate rating
        if 'rating' in place_data:
            rating = place_data['rating']
            if rating < self.validation_rules['min_rating'] or rating > self.validation_rules['max_rating']:
                warnings.append(f"Rating {rating} outside expected range [0-5]")
        
        # Check for suspicious data
        if 'name' in place_data:
            name = place_data['name']
            if len(name) < 2:
                warnings.append("Unusually short name")
            if name.lower() in ['n/a', 'null', 'undefined', 'test']:
                errors.append("Suspicious placeholder name")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_city_coverage(self, city: str, places: List[Dict]) -> Dict:
        """
        Validate overall coverage quality for a city
        
        Returns:
            {'quality_score': float, 'issues': []}
        """
        issues = []
        score = 100.0
        
        # Check place count
        count = len(places)
        if count < self.validation_rules['min_places_per_city']:
            issues.append(f"Low coverage: only {count} places")
            score -= 30
        elif count > self.validation_rules['max_places_per_city']:
            issues.append(f"Excessive results: {count} places (possible spam)")
            score -= 10
        
        # Check data quality
        valid_places = 0
        for place in places:
            validation = self.validate_place_data(place)
            if validation['valid']:
                valid_places += 1
        
        validity_ratio = valid_places / count if count > 0 else 0
        if validity_ratio < 0.8:
            issues.append(f"Low data quality: only {validity_ratio*100:.1f}% valid")
            score -= 20
        
        # Check rating distribution (should have variety)
        if 'rating' in places[0] if places else {}:
            ratings = [p.get('rating', 0) for p in places]
            unique_ratings = len(set(ratings))
            if unique_ratings < 3:
                issues.append("Suspicious rating uniformity")
                score -= 15
        
        return {
            'city': city,
            'quality_score': max(0, score),
            'total_places': count,
            'valid_places': valid_places,
            'validity_percent': validity_ratio * 100,
            'issues': issues,
            'passed': score >= 60
        }


# Integration functions

def create_analytics_dashboard_data(db_session) -> Dict:
    """
    Generate comprehensive analytics data for dashboard
    
    Returns:
        Dict with all metrics for visualization
    """
    analytics = CacheAnalytics(db_session)
    monitor = CostMonitor(monthly_budget_usd=50.0)
    
    performance = analytics.get_performance_stats()
    costs = analytics.get_cost_summary(days_lookback=30)
    budget = monitor.check_budget_status(analytics)
    
    return {
        'performance': performance,
        'costs': costs,
        'budget': budget,
        'timestamp': datetime.now().isoformat(),
        'cache_health': {
            'hit_rate': performance['cache_hit_rate_percent'],
            'freshness': performance['freshness_score'],
            'coverage': performance['unique_cities']
        },
        'alerts': []
    }


def monitor_and_alert(db_session, alert_callback=None):
    """
    Monitor system and trigger alerts if needed
    
    Args:
        alert_callback: Function to call with alert messages
    """
    analytics = CacheAnalytics(db_session)
    monitor = CostMonitor(monthly_budget_usd=50.0)
    
    budget_status = monitor.check_budget_status(analytics)
    
    if budget_status['alert_level'] == 'critical':
        msg = f"🚨 CRITICAL: Budget exceeded! Spent ${budget_status['current_spend_usd']:.2f} of ${budget_status['monthly_budget_usd']:.2f}"
        logger.error(msg)
        if alert_callback:
            alert_callback(msg, level='critical')
    
    elif budget_status['alert_level'] == 'warning':
        msg = f"⚠️ WARNING: {budget_status['budget_used_percent']:.1f}% of budget used"
        logger.warning(msg)
        if alert_callback:
            alert_callback(msg, level='warning')
    
    # Check cache health
    perf = analytics.get_performance_stats()
    if perf['freshness_score'] < 50:
        msg = f"⚠️ Cache freshness low: {perf['freshness_score']:.1f}%"
        logger.warning(msg)
        if alert_callback:
            alert_callback(msg, level='info')

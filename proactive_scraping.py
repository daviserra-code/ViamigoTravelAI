"""
🚀 PROACTIVE SCRAPING SYSTEM
Intelligent background scraping to build a rich local database
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from apify_integration import ApifyTravelIntegration
from models import db, PlaceCache, User
from sqlalchemy import func, and_
import logging

logger = logging.getLogger(__name__)


class ProactiveScrapingManager:
    """Manages intelligent background scraping to build local database"""
    
    def __init__(self):
        self.apify = ApifyTravelIntegration()
        self.popular_cities = [
            # Italy
            ('Roma', 'IT'), ('Milano', 'IT'), ('Venezia', 'IT'), ('Firenze', 'IT'),
            ('Napoli', 'IT'), ('Torino', 'IT'), ('Bologna', 'IT'), ('Genova', 'IT'),
            ('Verona', 'IT'), ('Palermo', 'IT'),
            # Europe
            ('London', 'UK'), ('Paris', 'FR'), ('Barcelona', 'ES'), ('Madrid', 'ES'),
            ('Berlin', 'DE'), ('Amsterdam', 'NL'), ('Prague', 'CZ'), ('Vienna', 'AT'),
            # World
            ('New York', 'US'), ('Tokyo', 'JP'), ('Dubai', 'AE'), ('Singapore', 'SG'),
        ]
        self.categories = ['tourist_attraction', 'restaurant']
        
    def get_cities_needing_refresh(self, max_age_days: int = 30) -> List[tuple]:
        """Find cities that need data refresh based on age or missing data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Get cities with old or missing cache
            needs_refresh = []
            
            for city, country in self.popular_cities:
                for category in self.categories:
                    cache_key = f"{city.lower()}_{category}"
                    cached = PlaceCache.query.filter_by(cache_key=cache_key).first()
                    
                    if not cached:
                        # No cache at all - high priority
                        needs_refresh.append((city, country, category, 'missing', None))
                    elif cached.created_at < cutoff_date:
                        # Cache is old
                        age_days = (datetime.now() - cached.created_at).days
                        needs_refresh.append((city, country, category, 'old', age_days))
                    else:
                        # Check if data is insufficient
                        place_data = json.loads(cached.place_data) if cached.place_data else []
                        if isinstance(place_data, list) and len(place_data) < 5:
                            needs_refresh.append((city, country, category, 'insufficient', len(place_data)))
            
            # Sort by priority: missing > insufficient > old
            priority_order = {'missing': 0, 'insufficient': 1, 'old': 2}
            needs_refresh.sort(key=lambda x: priority_order.get(x[3], 999))
            
            logger.info(f"📊 Found {len(needs_refresh)} city-category pairs needing refresh")
            return needs_refresh
            
        except Exception as e:
            logger.error(f"❌ Error getting cities needing refresh: {e}")
            return []
    
    def get_user_requested_cities(self, days: int = 7) -> List[tuple]:
        """Analyze user search patterns to find frequently requested cities"""
        try:
            # This would analyze user search history - for now return most accessed cities
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get most accessed cities from cache
            popular = db.session.query(
                PlaceCache.city,
                PlaceCache.country,
                func.sum(PlaceCache.access_count).label('total_access'),
                func.max(PlaceCache.last_accessed).label('last_access')
            ).group_by(
                PlaceCache.city,
                PlaceCache.country
            ).order_by(
                func.sum(PlaceCache.access_count).desc()
            ).limit(20).all()
            
            user_cities = []
            for city, country, access_count, last_access in popular:
                if city and access_count > 5:  # At least 5 accesses
                    user_cities.append((city.capitalize(), country or 'IT', access_count))
            
            logger.info(f"📈 Found {len(user_cities)} frequently requested cities")
            return user_cities
            
        except Exception as e:
            logger.error(f"❌ Error analyzing user requests: {e}")
            return []
    
    def scrape_and_cache_city(self, city: str, country: str, category: str) -> bool:
        """Scrape a city and cache results"""
        try:
            if not self.apify.is_available():
                logger.warning(f"⚠️ Apify not available for {city}")
                return False
            
            logger.info(f"🔍 Scraping {city}, {country} - {category}")
            
            # Use Apify to get fresh data
            places = self.apify.search_google_maps_places(city, category, max_results=15)
            
            if places and len(places) > 0:
                # Cache the results
                self.apify.cache_places(city, category, places)
                logger.info(f"✅ Cached {len(places)} places for {city} - {category}")
                return True
            else:
                logger.warning(f"⚠️ No places found for {city} - {category}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error scraping {city}: {e}")
            return False
    
    def run_proactive_scraping(self, max_scrapes: int = 10, prioritize_users: bool = True):
        """
        Run proactive scraping session
        
        Args:
            max_scrapes: Maximum number of city-category pairs to scrape
            prioritize_users: If True, prioritize cities users have requested
        """
        try:
            logger.info("🚀 Starting proactive scraping session")
            
            scraped_count = 0
            success_count = 0
            
            # Strategy 1: User-driven scraping
            if prioritize_users:
                user_cities = self.get_user_requested_cities(days=14)
                for city, country, access_count in user_cities[:max_scrapes // 2]:
                    for category in self.categories:
                        if scraped_count >= max_scrapes // 2:
                            break
                        
                        cache_key = f"{city.lower()}_{category}"
                        cached = PlaceCache.query.filter_by(cache_key=cache_key).first()
                        
                        # Only scrape if missing or very old
                        if not cached or (datetime.now() - cached.created_at).days > 60:
                            if self.scrape_and_cache_city(city, country, category):
                                success_count += 1
                            scraped_count += 1
            
            # Strategy 2: Fill gaps in popular cities
            needs_refresh = self.get_cities_needing_refresh(max_age_days=90)
            for city, country, category, reason, detail in needs_refresh[:max_scrapes - scraped_count]:
                if scraped_count >= max_scrapes:
                    break
                
                if self.scrape_and_cache_city(city, country, category):
                    success_count += 1
                scraped_count += 1
            
            logger.info(f"✅ Proactive scraping complete: {success_count}/{scraped_count} successful")
            return {
                'total_attempted': scraped_count,
                'successful': success_count,
                'failed': scraped_count - success_count
            }
            
        except Exception as e:
            logger.error(f"❌ Proactive scraping error: {e}")
            return {'error': str(e)}
    
    def get_coverage_stats(self) -> Dict:
        """Get statistics about database coverage"""
        try:
            stats = {
                'total_cities': 0,
                'total_places': 0,
                'coverage_by_city': {},
                'oldest_cache': None,
                'newest_cache': None,
                'average_age_days': 0
            }
            
            # Count unique cities
            cities = db.session.query(PlaceCache.city).distinct().all()
            stats['total_cities'] = len(cities)
            
            # Get age statistics
            all_cache = PlaceCache.query.all()
            if all_cache:
                ages = [(datetime.now() - c.created_at).days for c in all_cache]
                stats['average_age_days'] = sum(ages) / len(ages)
                stats['oldest_cache'] = max(ages)
                stats['newest_cache'] = min(ages)
            
            # Count places per city
            for city_tuple in cities:
                city = city_tuple[0]
                if city:
                    cache_entries = PlaceCache.query.filter_by(city=city).all()
                    total_places = 0
                    for entry in cache_entries:
                        place_data = json.loads(entry.place_data) if entry.place_data else []
                        if isinstance(place_data, list):
                            total_places += len(place_data)
                    
                    stats['coverage_by_city'][city] = {
                        'places': total_places,
                        'categories': len(cache_entries)
                    }
                    stats['total_places'] += total_places
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting coverage stats: {e}")
            return {}


class SmartCacheWarmer:
    """Intelligent cache warming based on patterns"""
    
    def __init__(self):
        self.apify = ApifyTravelIntegration()
    
    def warm_cache_for_upcoming_trips(self):
        """Pre-cache data for cities users are likely to visit"""
        # This could analyze:
        # - Seasonal patterns (summer: coastal cities, winter: mountain cities)
        # - User browsing patterns
        # - Popular travel periods
        pass
    
    def predictive_scraping(self):
        """Use ML to predict which cities will be requested next"""
        # Future enhancement: ML model to predict user behavior
        pass


# Utility functions for integration

def schedule_proactive_scraping():
    """
    Function to be called by a scheduler (e.g., APScheduler, Celery)
    """
    try:
        manager = ProactiveScrapingManager()
        result = manager.run_proactive_scraping(max_scrapes=5, prioritize_users=True)
        logger.info(f"📊 Scheduled scraping result: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Scheduled scraping failed: {e}")
        return None


def get_database_health_report() -> Dict:
    """Generate a health report of the local database"""
    try:
        manager = ProactiveScrapingManager()
        stats = manager.get_coverage_stats()
        
        needs_refresh = manager.get_cities_needing_refresh(max_age_days=30)
        
        health = {
            'status': 'healthy' if len(needs_refresh) < 10 else 'needs_attention',
            'stats': stats,
            'cities_needing_refresh': len(needs_refresh),
            'recommendations': []
        }
        
        if len(needs_refresh) > 20:
            health['recommendations'].append('Consider running proactive scraping')
        
        if stats.get('average_age_days', 0) > 60:
            health['recommendations'].append('Cache is getting old, schedule refresh')
        
        return health
        
    except Exception as e:
        logger.error(f"❌ Error generating health report: {e}")
        return {'status': 'error', 'message': str(e)}


# Flask route integration examples

def register_proactive_routes(app):
    """Register proactive scraping routes with Flask app"""
    
    @app.route('/admin/scraping/status')
    def scraping_status():
        """Get current scraping/cache status"""
        from flask import jsonify
        health = get_database_health_report()
        return jsonify(health)
    
    @app.route('/admin/scraping/run', methods=['POST'])
    def run_scraping():
        """Manually trigger proactive scraping"""
        from flask import jsonify, request
        
        max_scrapes = request.json.get('max_scrapes', 5)
        prioritize_users = request.json.get('prioritize_users', True)
        
        manager = ProactiveScrapingManager()
        result = manager.run_proactive_scraping(
            max_scrapes=max_scrapes,
            prioritize_users=prioritize_users
        )
        
        return jsonify(result)
    
    @app.route('/admin/scraping/coverage')
    def coverage_stats():
        """Get detailed coverage statistics"""
        from flask import jsonify
        
        manager = ProactiveScrapingManager()
        stats = manager.get_coverage_stats()
        
        return jsonify(stats)

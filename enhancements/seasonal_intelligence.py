"""
🌞 SEASONAL INTELLIGENCE SYSTEM
Automatically adjusts scraping priorities based on seasons and travel patterns
"""
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class SeasonalIntelligence:
    """Manages seasonal travel patterns and predictions"""

    def __init__(self):
        self.seasonal_patterns = self._init_seasonal_patterns()

    def _init_seasonal_patterns(self) -> Dict:
        """Initialize seasonal travel patterns"""
        return {
            # Summer destinations (June, July, August)
            'summer': {
                'months': [6, 7, 8],
                'cities': [
                    ('Sardegna', 'IT', 'beach'),
                    ('Sicilia', 'IT', 'beach'),
                    ('Amalfi Coast', 'IT', 'coastal'),
                    ('Cinque Terre', 'IT', 'coastal'),
                    ('Portofino', 'IT', 'coastal'),
                    ('Capri', 'IT', 'island'),
                    ('Barcelona', 'ES', 'beach'),
                    ('Ibiza', 'ES', 'island'),
                    ('Santorini', 'GR', 'island'),
                    ('Mykonos', 'GR', 'island'),
                ],
                'priority_boost': 1.5,
                'cache_duration_days': 14  # Shorter cache for high season
            },

            # Winter destinations (December, January, February)
            'winter': {
                'months': [12, 1, 2],
                'cities': [
                    ('Cortina d\'Ampezzo', 'IT', 'ski'),
                    ('Val d\'Aosta', 'IT', 'ski'),
                    ('Dolomites', 'IT', 'ski'),
                    ('Madonna di Campiglio', 'IT', 'ski'),
                    ('Courmayeur', 'IT', 'ski'),
                    ('Chamonix', 'FR', 'ski'),
                    ('Zermatt', 'CH', 'ski'),
                    ('St. Moritz', 'CH', 'ski'),
                ],
                'priority_boost': 1.5,
                'cache_duration_days': 21
            },

            # Spring destinations (March, April, May)
            'spring': {
                'months': [3, 4, 5],
                'cities': [
                    ('Firenze', 'IT', 'cultural'),
                    ('Roma', 'IT', 'cultural'),
                    ('Venezia', 'IT', 'cultural'),
                    ('Paris', 'FR', 'cultural'),
                    ('Amsterdam', 'NL', 'cultural'),
                    ('Kyoto', 'JP', 'cultural'),
                    ('Washington DC', 'US', 'cultural'),
                ],
                'priority_boost': 1.3,
                'cache_duration_days': 30
            },

            # Fall destinations (September, October, November)
            'fall': {
                'months': [9, 10, 11],
                'cities': [
                    ('Toscana', 'IT', 'wine'),
                    ('Piemonte', 'IT', 'wine'),
                    ('Chianti', 'IT', 'wine'),
                    ('Bordeaux', 'FR', 'wine'),
                    ('Napa Valley', 'US', 'wine'),
                    ('New England', 'US', 'foliage'),
                ],
                'priority_boost': 1.2,
                'cache_duration_days': 30
            },

            # Year-round major cities
            'year_round': {
                'months': list(range(1, 13)),
                'cities': [
                    ('London', 'UK', 'urban'),
                    ('New York', 'US', 'urban'),
                    ('Tokyo', 'JP', 'urban'),
                    ('Dubai', 'AE', 'urban'),
                    ('Singapore', 'SG', 'urban'),
                ],
                'priority_boost': 1.0,
                'cache_duration_days': 7
            }
        }

    def get_current_season(self) -> str:
        """Determine current season based on month"""
        current_month = datetime.now().month

        for season, data in self.seasonal_patterns.items():
            if current_month in data['months']:
                return season

        return 'year_round'

    def get_seasonal_cities(self, months_ahead: int = 1) -> List[Tuple]:
        """
        Get cities to prioritize for upcoming season

        Args:
            months_ahead: How many months ahead to predict (default: 1)

        Returns:
            List of (city, country, category, priority_boost)
        """
        current_month = datetime.now().month
        target_month = (current_month + months_ahead - 1) % 12 + 1

        seasonal_cities = []

        for season, data in self.seasonal_patterns.items():
            if target_month in data['months']:
                for city, country, category in data['cities']:
                    seasonal_cities.append((
                        city,
                        country,
                        category,
                        data['priority_boost'],
                        data['cache_duration_days']
                    ))

        # Sort by priority boost (higher first)
        seasonal_cities.sort(key=lambda x: x[3], reverse=True)

        logger.info(
            f"🌞 Found {len(seasonal_cities)} seasonal cities for month {target_month}")
        return seasonal_cities

    def get_upcoming_season_cities(self) -> List[Tuple]:
        """Get cities for the next 3 months"""
        cities = set()

        for months_ahead in range(1, 4):
            for city_data in self.get_seasonal_cities(months_ahead):
                cities.add(city_data)

        return list(cities)

    def should_boost_priority(self, city: str) -> Tuple[bool, float]:
        """
        Check if a city should get priority boost based on season

        Returns:
            (should_boost, boost_multiplier)
        """
        current_season = self.get_current_season()

        if current_season in self.seasonal_patterns:
            season_data = self.seasonal_patterns[current_season]

            for seasonal_city, country, category in season_data['cities']:
                if city.lower() in seasonal_city.lower() or seasonal_city.lower() in city.lower():
                    return True, season_data['priority_boost']

        return False, 1.0

    def get_cache_duration_for_city(self, city: str) -> int:
        """Get recommended cache duration based on seasonality"""
        current_season = self.get_current_season()

        if current_season in self.seasonal_patterns:
            season_data = self.seasonal_patterns[current_season]

            for seasonal_city, country, category in season_data['cities']:
                if city.lower() in seasonal_city.lower() or seasonal_city.lower() in city.lower():
                    return season_data['cache_duration_days']

        return 30  # Default cache duration


class EventBasedIntelligence:
    """Manages event-driven scraping priorities"""

    def __init__(self):
        self.upcoming_events = self._init_events()

    def _init_events(self) -> List[Dict]:
        """Initialize known major events"""
        return [
            {
                'name': 'Carnevale di Venezia',
                'city': 'Venezia',
                'country': 'IT',
                'months': [2],
                'priority_boost': 2.0,
                'scrape_ahead_days': 60
            },
            {
                'name': 'Festival di Sanremo',
                'city': 'Sanremo',
                'country': 'IT',
                'months': [2],
                'priority_boost': 1.8,
                'scrape_ahead_days': 45
            },
            {
                'name': 'Milano Design Week',
                'city': 'Milano',
                'country': 'IT',
                'months': [4],
                'priority_boost': 1.7,
                'scrape_ahead_days': 60
            },
            {
                'name': 'Biennale di Venezia',
                'city': 'Venezia',
                'country': 'IT',
                'months': [5, 6, 7, 8, 9, 10, 11],
                'priority_boost': 1.5,
                'scrape_ahead_days': 90
            },
            {
                'name': 'Palio di Siena',
                'city': 'Siena',
                'country': 'IT',
                'months': [7, 8],
                'priority_boost': 1.9,
                'scrape_ahead_days': 60
            },
            {
                'name': 'Venice Film Festival',
                'city': 'Venezia',
                'country': 'IT',
                'months': [8, 9],
                'priority_boost': 1.8,
                'scrape_ahead_days': 75
            },
        ]

    def get_active_events(self, months_ahead: int = 2) -> List[Dict]:
        """Get events happening in the next N months"""
        current_month = datetime.now().month
        target_months = [(current_month + i - 1) %
                         12 + 1 for i in range(months_ahead + 1)]

        active = []
        for event in self.upcoming_events:
            if any(month in event['months'] for month in target_months):
                active.append(event)

        return active

    def get_event_cities_to_scrape(self) -> List[Tuple]:
        """Get cities that should be scraped due to upcoming events"""
        active_events = self.get_active_events(months_ahead=2)

        cities = []
        for event in active_events:
            cities.append((
                event['city'],
                event['country'],
                event['name'],
                event['priority_boost']
            ))

        logger.info(f"🎭 Found {len(cities)} cities with upcoming events")
        return cities


# Integration helper functions

def get_seasonal_scraping_priorities() -> List[Dict]:
    """
    Get comprehensive seasonal scraping priorities

    Returns:
        List of cities with priority scores
    """
    seasonal = SeasonalIntelligence()
    events = EventBasedIntelligence()

    priorities = []

    # Add seasonal cities
    for city, country, category, boost, cache_days in seasonal.get_upcoming_season_cities():
        priorities.append({
            'city': city,
            'country': country,
            'reason': f'Seasonal: {category}',
            'priority_score': boost,
            'cache_duration_days': cache_days
        })

    # Add event-driven cities
    for city, country, event_name, boost in events.get_event_cities_to_scrape():
        priorities.append({
            'city': city,
            'country': country,
            'reason': f'Event: {event_name}',
            'priority_score': boost,
            'cache_duration_days': 14  # Short cache for events
        })

    # Sort by priority score
    priorities.sort(key=lambda x: x['priority_score'], reverse=True)

    return priorities


def integrate_seasonal_intelligence_with_scraping(scraping_manager):
    """
    Integrate seasonal intelligence with ProactiveScrapingManager

    Usage:
        from seasonal_intelligence import integrate_seasonal_intelligence_with_scraping
        manager = ProactiveScrapingManager()
        integrate_seasonal_intelligence_with_scraping(manager)
    """
    seasonal = SeasonalIntelligence()

    # Get seasonal cities
    seasonal_cities = seasonal.get_upcoming_season_cities()

    # Add to scraping queue with higher priority
    for city, country, category, boost, cache_days in seasonal_cities[:10]:
        try:
            for cat in ['tourist_attraction', 'restaurant']:
                success = scraping_manager.scrape_and_cache_city(
                    city, country, cat)
                if success:
                    logger.info(f"✅ Seasonal scraping: {city} - {cat}")
        except Exception as e:
            logger.error(f"❌ Seasonal scraping error for {city}: {e}")

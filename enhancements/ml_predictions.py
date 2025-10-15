"""
🤖 ML-BASED PREDICTION SYSTEM
Uses machine learning to predict user travel patterns and preferences
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns to predict future destinations"""

    def __init__(self, db_session):
        self.db = db_session
        self.user_profiles = defaultdict(dict)

    def analyze_user_search_patterns(self, user_id: int, days_lookback: int = 90) -> Dict:
        """
        Analyze user's search and access patterns

        Returns:
            Dict with user profile insights
        """
        from models import User, TravelJournal, PlaceCache
        from sqlalchemy import func

        cutoff_date = datetime.now() - timedelta(days=days_lookback)

        # Get user's journal entries
        journals = self.db.query(TravelJournal).filter(
            TravelJournal.user_id == user_id,
            TravelJournal.created_at >= cutoff_date
        ).all()

        # Analyze patterns
        cities_visited = Counter()
        categories_preferred = Counter()
        planning_lead_times = []
        weekend_warrior = 0
        total_trips = len(journals)

        for journal in journals:
            # Extract city from destination
            if journal.destination:
                cities_visited[journal.destination] += 1

            # Check if weekend trip (simplified)
            if journal.created_at.weekday() >= 5:  # Saturday or Sunday
                weekend_warrior += 1

            # Calculate planning lead time (if travel_date exists)
            if hasattr(journal, 'travel_date') and journal.travel_date:
                lead_time = (journal.travel_date -
                             journal.created_at.date()).days
                planning_lead_times.append(lead_time)

        # Calculate metrics
        avg_lead_time = sum(planning_lead_times) / \
            len(planning_lead_times) if planning_lead_times else 30
        weekend_ratio = weekend_warrior / total_trips if total_trips > 0 else 0

        profile = {
            'user_id': user_id,
            'total_trips': total_trips,
            'favorite_cities': cities_visited.most_common(5),
            'avg_planning_lead_days': int(avg_lead_time),
            'weekend_warrior_score': weekend_ratio,
            'user_type': self._classify_user_type(avg_lead_time, weekend_ratio, total_trips),
            'analyzed_at': datetime.now()
        }

        self.user_profiles[user_id] = profile
        logger.info(f"📊 User {user_id} profile: {profile['user_type']}")

        return profile

    def _classify_user_type(self, lead_time: float, weekend_ratio: float, total_trips: int) -> str:
        """Classify user into behavioral segments"""

        if total_trips < 3:
            return 'new_explorer'

        if lead_time > 60:
            return 'advance_planner'
        elif lead_time < 7:
            return 'spontaneous_traveler'

        if weekend_ratio > 0.7:
            return 'weekend_warrior'

        if total_trips > 20:
            return 'frequent_traveler'

        return 'casual_planner'

    def predict_next_destinations(self, user_id: int, limit: int = 5) -> List[Tuple]:
        """
        Predict likely next destinations for a user

        Returns:
            List of (city, confidence_score, reason)
        """
        profile = self.user_profiles.get(user_id)
        if not profile:
            profile = self.analyze_user_search_patterns(user_id)

        predictions = []

        # Rule 1: Cities similar to favorites
        favorite_cities = [city for city, count in profile['favorite_cities']]
        if favorite_cities:
            similar_cities = self._find_similar_cities(favorite_cities)
            for city in similar_cities[:3]:
                predictions.append((
                    city,
                    0.75,
                    f"Similar to your favorite: {favorite_cities[0]}"
                ))

        # Rule 2: Seasonal recommendations based on user type
        seasonal_cities = self._get_seasonal_recommendations(
            profile['user_type'])
        for city in seasonal_cities[:2]:
            predictions.append((
                city,
                0.60,
                f"Perfect for {profile['user_type']}"
            ))

        # Rule 3: Trending destinations
        trending = self._get_trending_destinations()
        for city in trending[:2]:
            predictions.append((
                city,
                0.50,
                "Trending destination"
            ))

        # Sort by confidence and limit
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:limit]

    def _find_similar_cities(self, favorite_cities: List[str]) -> List[str]:
        """Find cities similar to user's favorites"""

        # City similarity matrix (simplified)
        similarity_map = {
            'Roma': ['Firenze', 'Napoli', 'Atene', 'Barcelona'],
            'Milano': ['Torino', 'Bologna', 'Geneva', 'Zurich'],
            'Venezia': ['Amsterdam', 'Bruges', 'Stockholm'],
            'Firenze': ['Roma', 'Siena', 'Pisa', 'Bologna'],
            'Napoli': ['Palermo', 'Bari', 'Sorrento'],
            'Torino': ['Milano', 'Lyon', 'Geneva'],
            'Bologna': ['Firenze', 'Modena', 'Parma'],
        }

        similar = []
        for city in favorite_cities:
            if city in similarity_map:
                similar.extend(similarity_map[city])

        # Remove duplicates and favorites
        return [c for c in dict.fromkeys(similar) if c not in favorite_cities]

    def _get_seasonal_recommendations(self, user_type: str) -> List[str]:
        """Get seasonal city recommendations based on user type"""

        current_month = datetime.now().month

        # Summer months
        if current_month in [6, 7, 8]:
            if user_type == 'weekend_warrior':
                return ['Sardegna', 'Cinque Terre', 'Portofino']
            elif user_type == 'advance_planner':
                return ['Amalfi Coast', 'Santorini', 'Mykonos']
            else:
                return ['Sicilia', 'Capri', 'Ibiza']

        # Winter months
        elif current_month in [12, 1, 2]:
            if user_type == 'spontaneous_traveler':
                return ['Cortina', 'Courmayeur', 'Val d\'Aosta']
            else:
                return ['Dolomites', 'Chamonix', 'Zermatt']

        # Spring/Fall
        else:
            return ['Firenze', 'Toscana', 'Piemonte']

    def _get_trending_destinations(self) -> List[str]:
        """Get trending destinations from database"""
        from models import PlaceCache
        from sqlalchemy import func

        # Get most cached cities in last 7 days
        cutoff = datetime.now() - timedelta(days=7)

        trending = self.db.query(
            PlaceCache.city,
            func.count(PlaceCache.id).label('cache_count')
        ).filter(
            PlaceCache.cached_at >= cutoff
        ).group_by(
            PlaceCache.city
        ).order_by(
            func.count(PlaceCache.id).desc()
        ).limit(10).all()

        return [city for city, count in trending]


class CollaborativeFiltering:
    """Simple collaborative filtering for destination recommendations"""

    def __init__(self, db_session):
        self.db = db_session

    def find_similar_users(self, user_id: int, limit: int = 10) -> List[int]:
        """Find users with similar travel patterns"""
        from models import TravelJournal
        from sqlalchemy import func

        # Get user's visited cities
        user_cities = self.db.query(TravelJournal.destination).filter(
            TravelJournal.user_id == user_id
        ).distinct().all()

        user_city_set = set(c[0] for c in user_cities if c[0])

        if not user_city_set:
            return []

        # Find other users who visited same cities
        similar_users = self.db.query(
            TravelJournal.user_id,
            func.count(TravelJournal.id).label('overlap_count')
        ).filter(
            TravelJournal.user_id != user_id,
            TravelJournal.destination.in_(user_city_set)
        ).group_by(
            TravelJournal.user_id
        ).order_by(
            func.count(TravelJournal.id).desc()
        ).limit(limit).all()

        return [u[0] for u in similar_users]

    def get_collaborative_recommendations(self, user_id: int, limit: int = 5) -> List[Tuple]:
        """
        Get destination recommendations based on similar users

        Returns:
            List of (city, score, reason)
        """
        from models import TravelJournal
        from sqlalchemy import func

        # Find similar users
        similar_user_ids = self.find_similar_users(user_id, limit=20)

        if not similar_user_ids:
            return []

        # Get user's already visited cities
        visited = self.db.query(TravelJournal.destination).filter(
            TravelJournal.user_id == user_id
        ).distinct().all()
        visited_cities = set(c[0] for c in visited if c[0])

        # Get destinations visited by similar users
        recommendations = self.db.query(
            TravelJournal.destination,
            func.count(TravelJournal.id).label('recommendation_score')
        ).filter(
            TravelJournal.user_id.in_(similar_user_ids),
            TravelJournal.destination.isnot(None),
            ~TravelJournal.destination.in_(visited_cities)
        ).group_by(
            TravelJournal.destination
        ).order_by(
            func.count(TravelJournal.id).desc()
        ).limit(limit).all()

        return [
            (city, score / len(similar_user_ids), "Liked by similar travelers")
            for city, score in recommendations
        ]


# Integration functions

def get_ml_based_scraping_priorities(db_session, user_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    Get ML-based scraping priorities based on user predictions

    Args:
        db_session: Database session
        user_ids: List of user IDs to analyze (None = all active users)

    Returns:
        List of cities to pre-cache with priority scores
    """
    from models import User

    analyzer = UserBehaviorAnalyzer(db_session)
    collaborative = CollaborativeFiltering(db_session)

    # Get active users if not specified
    if not user_ids:
        cutoff = datetime.now() - timedelta(days=30)
        from models import TravelJournal
        active_users = db_session.query(TravelJournal.user_id).filter(
            TravelJournal.created_at >= cutoff
        ).distinct().all()
        user_ids = [u[0] for u in active_users]

    # Aggregate predictions
    city_scores = defaultdict(float)
    city_reasons = defaultdict(list)

    for user_id in user_ids[:50]:  # Limit to 50 users for performance
        try:
            # Get behavior-based predictions
            predictions = analyzer.predict_next_destinations(user_id, limit=3)
            for city, score, reason in predictions:
                city_scores[city] += score
                city_reasons[city].append(reason)

            # Get collaborative predictions
            collab_recs = collaborative.get_collaborative_recommendations(
                user_id, limit=2)
            for city, score, reason in collab_recs:
                # Weight collaborative slightly lower
                city_scores[city] += score * 0.8
                city_reasons[city].append(reason)

        except Exception as e:
            logger.warning(f"⚠️ Error analyzing user {user_id}: {e}")

    # Format results
    priorities = []
    for city, total_score in city_scores.items():
        priorities.append({
            'city': city,
            'priority_score': total_score,
            'predicted_demand': len(city_reasons[city]),
            'reasons': list(set(city_reasons[city][:3])),
            'recommendation_type': 'ml_prediction'
        })

    # Sort by score
    priorities.sort(key=lambda x: x['priority_score'], reverse=True)

    logger.info(f"🤖 ML predictions: {len(priorities)} cities identified")
    return priorities

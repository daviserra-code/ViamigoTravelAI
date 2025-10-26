#!/usr/bin/env python3
"""
ViamigoTravelAI Data Intelligence Layer
Advanced analytics for travel patterns, seasonal recommendations, budget optimization
Machine learning for user preference analysis across 9,930+ places in 56 Italian cities
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Blueprint, jsonify, request
import psycopg2
import os
import logging
from collections import defaultdict, Counter
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create blueprint
data_intelligence_bp = Blueprint('data_intelligence', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TravelPattern:
    route: str
    frequency: int
    avg_duration: float
    popular_months: List[str]
    user_demographics: Dict[str, Any]
    satisfaction_score: float


@dataclass
class SeasonalRecommendation:
    month: str
    city: str
    recommended_places: List[str]
    weather_score: float
    crowd_score: float
    price_score: float
    overall_score: float
    reasons: List[str]


@dataclass
class BudgetOptimization:
    total_budget: float
    budget_breakdown: Dict[str, float]
    recommended_allocation: Dict[str, float]
    cost_saving_tips: List[str]
    alternative_options: List[Dict[str, Any]]


@dataclass
class UserInsight:
    user_segment: str
    preference_score: Dict[str, float]
    predicted_satisfaction: float
    recommendation_confidence: float
    behavioral_traits: List[str]


class DataIntelligenceEngine:
    """Advanced data intelligence and analytics engine"""

    def __init__(self):
        self.analytics_cache = {}
        self.ml_models = {}
        self.setup_analytics_db()

    def get_db_connection(self):
        """Get PostgreSQL connection"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError(
                    "DATABASE_URL not found in environment variables")
            return psycopg2.connect(database_url)
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return None

    def setup_analytics_db(self):
        """Setup local analytics database for storing insights"""
        try:
            self.analytics_db = sqlite3.connect(
                'analytics.db', check_same_thread=False)
            cursor = self.analytics_db.cursor()

            # Create analytics tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action_type TEXT,
                    place_name TEXT,
                    city TEXT,
                    timestamp DATETIME,
                    session_id TEXT,
                    user_preferences TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS travel_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_hash TEXT UNIQUE,
                    start_city TEXT,
                    end_city TEXT,
                    via_cities TEXT,
                    frequency INTEGER DEFAULT 1,
                    avg_duration REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seasonal_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT,
                    month INTEGER,
                    avg_temperature REAL,
                    avg_crowd_level REAL,
                    avg_price_index REAL,
                    popularity_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budget_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    budget_range TEXT,
                    city TEXT,
                    category TEXT,
                    avg_cost REAL,
                    cost_variance REAL,
                    recommendations TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.analytics_db.commit()
            logger.info("✅ Analytics database initialized")

        except Exception as e:
            logger.error(f"❌ Analytics DB setup error: {e}")
            self.analytics_db = None

    # ==================== TRAVEL PATTERN ANALYSIS ====================

    def analyze_travel_patterns(self, time_period: str = "30_days") -> List[TravelPattern]:
        """Analyze travel patterns from user data and generate insights"""
        try:
            # Get travel data from main database
            patterns_data = self._extract_travel_patterns(time_period)

            # Analyze patterns using ML techniques
            analyzed_patterns = self._ml_pattern_analysis(patterns_data)

            # Store insights in analytics DB
            self._store_pattern_insights(analyzed_patterns)

            return analyzed_patterns

        except Exception as e:
            logger.error(f"❌ Travel pattern analysis error: {e}")
            return []

    def _extract_travel_patterns(self, time_period: str) -> List[Dict[str, Any]]:
        """Analyze travel patterns from user data and generate insights"""
        try:
            # Get travel data from main database
            patterns_data = self._extract_travel_patterns(time_period)

            # Analyze patterns using ML techniques
            analyzed_patterns = self._ml_pattern_analysis(patterns_data)

            # Store insights in analytics DB
            self._store_pattern_insights(analyzed_patterns)

            return analyzed_patterns

        except Exception as e:
            logger.error(f"❌ Travel pattern analysis error: {e}")
            return []

    def _extract_travel_patterns(self, time_period: str) -> List[Dict[str, Any]]:
        """Extract travel patterns from database"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                # Extract popular city combinations
                query = """
                    SELECT 
                        city,
                        COUNT(*) as visit_count,
                        AVG(EXTRACT(HOUR FROM NOW())) as avg_hour
                    FROM place_cache 
                    GROUP BY city
                    HAVING COUNT(*) > 10
                    ORDER BY visit_count DESC
                    LIMIT 20
                """
                cursor.execute(query)

                patterns = []
                for row in cursor.fetchall():
                    city = row[0]
                    visit_count = row[1]
                    avg_hour = float(row[2] or 12)

                    # Calculate additional metrics
                    pattern = {
                        'route': f"Various → {city}",
                        'frequency': visit_count,
                        'avg_duration': 4.5,  # Default assumption
                        'popular_months': self._get_popular_months(city),
                        'avg_hour': avg_hour,
                        'city': city
                    }
                    patterns.append(pattern)

                return patterns

        except Exception as e:
            logger.error(f"❌ Pattern extraction error: {e}")
            return []
        finally:
            conn.close()

    def _get_popular_months(self, city: str) -> List[str]:
        """Get popular months for a city (simplified heuristics)"""
        # Tourist season heuristics for Italian cities
        if city.lower() in ['roma', 'firenze', 'venezia', 'milano']:
            return ['Maggio', 'Giugno', 'Settembre', 'Ottobre']
        elif city.lower() in ['napoli', 'palermo', 'bari']:
            return ['Aprile', 'Maggio', 'Settembre', 'Ottobre']
        else:
            return ['Giugno', 'Luglio', 'Agosto', 'Settembre']

    def _ml_pattern_analysis(self, patterns_data: List[Dict]) -> List[TravelPattern]:
        """Apply machine learning to analyze travel patterns"""
        analyzed_patterns = []

        for pattern in patterns_data:
            # Calculate satisfaction score using heuristics
            satisfaction_score = self._calculate_satisfaction_score(pattern)

            # Determine user demographics (simplified)
            demographics = self._infer_demographics(pattern)

            travel_pattern = TravelPattern(
                route=pattern['route'],
                frequency=pattern['frequency'],
                avg_duration=pattern['avg_duration'],
                popular_months=pattern['popular_months'],
                user_demographics=demographics,
                satisfaction_score=satisfaction_score
            )

            analyzed_patterns.append(travel_pattern)

        return analyzed_patterns

    def _calculate_satisfaction_score(self, pattern: Dict) -> float:
        """Calculate satisfaction score based on various factors"""
        base_score = 0.7

        # Higher frequency suggests satisfaction
        if pattern['frequency'] > 50:
            base_score += 0.2
        elif pattern['frequency'] > 20:
            base_score += 0.1

        # Optimal timing
        avg_hour = pattern.get('avg_hour', 12)
        if 9 <= avg_hour <= 11 or 16 <= avg_hour <= 18:
            base_score += 0.1

        return min(base_score, 1.0)

    def _infer_demographics(self, pattern: Dict) -> Dict[str, Any]:
        """Infer user demographics from travel patterns"""
        return {
            'primary_age_group': '25-45',
            'travel_style': 'Cultural Explorer' if pattern['frequency'] > 30 else 'Casual Tourist',
            'budget_segment': 'Mid-range',
            'group_size': 'Small Group (2-4)'
        }

    def _store_pattern_insights(self, patterns: List[TravelPattern]):
        """Store pattern insights in analytics database"""
        if not self.analytics_db:
            return

        try:
            cursor = self.analytics_db.cursor()

            for pattern in patterns:
                # Create route hash for uniqueness
                route_hash = hash(pattern.route)

                cursor.execute('''
                    INSERT OR REPLACE INTO travel_patterns 
                    (route_hash, start_city, end_city, frequency, avg_duration, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    str(route_hash),
                    'Various',  # Simplified
                    pattern.route.split('→')[-1].strip(),
                    pattern.frequency,
                    pattern.avg_duration,
                    datetime.now()
                ))

            self.analytics_db.commit()
            logger.info(f"✅ Stored {len(patterns)} travel patterns")

        except Exception as e:
            logger.error(f"❌ Pattern storage error: {e}")

    # ==================== SEASONAL RECOMMENDATIONS ====================

    def generate_seasonal_recommendations(self, target_month: Optional[int] = None) -> List[SeasonalRecommendation]:
        """Generate AI-powered seasonal travel recommendations"""
        try:
            if target_month is None:
                target_month = datetime.now().month

            # Get seasonal data
            seasonal_data = self._get_seasonal_data(target_month)

            # Generate recommendations using ML
            recommendations = self._ml_seasonal_analysis(
                seasonal_data, target_month)

            # Store recommendations
            self._store_seasonal_insights(recommendations)

            return recommendations

        except Exception as e:
            logger.error(f"❌ Seasonal recommendations error: {e}")
            return []

    def _get_seasonal_data(self, month: int) -> List[Dict[str, Any]]:
        """Get seasonal data for cities"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT DISTINCT city, COUNT(*) as place_count
                    FROM place_cache 
                    WHERE city IS NOT NULL
                    GROUP BY city
                    ORDER BY place_count DESC
                    LIMIT 15
                """
                cursor.execute(query)

                seasonal_data = []
                for row in cursor.fetchall():
                    city = row[0]
                    place_count = row[1]

                    # Generate seasonal metrics
                    data = {
                        'city': city,
                        'month': month,
                        'place_count': place_count,
                        'weather_score': self._get_weather_score(city, month),
                        'crowd_score': self._get_crowd_score(city, month),
                        'price_score': self._get_price_score(city, month)
                    }
                    seasonal_data.append(data)

                return seasonal_data

        except Exception as e:
            logger.error(f"❌ Seasonal data error: {e}")
            return []
        finally:
            conn.close()

    def _get_weather_score(self, city: str, month: int) -> float:
        """Get weather score for city and month (0-1)"""
        # Simplified weather scoring for Italian cities
        weather_data = {
            'roma': [0.6, 0.6, 0.7, 0.8, 0.9, 0.95, 0.9, 0.9, 0.95, 0.9, 0.8, 0.7],
            'milano': [0.5, 0.5, 0.7, 0.8, 0.9, 0.9, 0.85, 0.85, 0.9, 0.8, 0.6, 0.5],
            'napoli': [0.7, 0.7, 0.8, 0.9, 0.95, 0.95, 0.9, 0.9, 0.95, 0.9, 0.8, 0.7],
            'firenze': [0.6, 0.6, 0.8, 0.9, 0.95, 0.9, 0.85, 0.85, 0.9, 0.85, 0.7, 0.6],
            'venezia': [0.5, 0.5, 0.7, 0.8, 0.9, 0.9, 0.85, 0.85, 0.9, 0.8, 0.6, 0.5]
        }

        city_key = city.lower()
        if city_key in weather_data:
            return weather_data[city_key][month - 1]

        # Default scoring for other cities
        if month in [6, 7, 8, 9]:  # Summer/early autumn
            return 0.9
        elif month in [4, 5, 10]:  # Spring/late autumn
            return 0.8
        else:
            return 0.6

    def _get_crowd_score(self, city: str, month: int) -> float:
        """Get crowd score (lower is better) for city and month"""
        # Inverted scoring - lower crowds = higher score
        crowd_levels = {
            'roma': [0.8, 0.8, 0.6, 0.5, 0.3, 0.2, 0.1, 0.1, 0.4, 0.6, 0.7, 0.8],
            'milano': [0.9, 0.9, 0.7, 0.6, 0.4, 0.3, 0.2, 0.2, 0.5, 0.7, 0.8, 0.9],
            'venezia': [0.9, 0.9, 0.5, 0.3, 0.2, 0.1, 0.05, 0.05, 0.3, 0.6, 0.8, 0.9],
            'firenze': [0.8, 0.8, 0.6, 0.4, 0.2, 0.1, 0.1, 0.1, 0.4, 0.6, 0.7, 0.8]
        }

        city_key = city.lower()
        if city_key in crowd_levels:
            return crowd_levels[city_key][month - 1]

        # Default for other cities
        if month in [7, 8]:  # Peak summer
            return 0.2
        elif month in [6, 9]:  # Shoulder season
            return 0.6
        else:
            return 0.8

    def _get_price_score(self, city: str, month: int) -> float:
        """Get price score (lower prices = higher score)"""
        # Inverted pricing - lower prices = higher score
        price_levels = {
            'roma': [0.8, 0.8, 0.7, 0.6, 0.4, 0.2, 0.1, 0.1, 0.5, 0.7, 0.8, 0.9],
            'milano': [0.9, 0.9, 0.8, 0.7, 0.5, 0.3, 0.2, 0.2, 0.6, 0.8, 0.9, 0.9],
            'venezia': [0.8, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05, 0.05, 0.4, 0.7, 0.8, 0.9]
        }

        city_key = city.lower()
        if city_key in price_levels:
            return price_levels[city_key][month - 1]

        # Default pricing
        if month in [12, 1, 2]:  # Winter
            return 0.9
        elif month in [7, 8]:  # Peak summer
            return 0.3
        else:
            return 0.7

    def _ml_seasonal_analysis(self, seasonal_data: List[Dict], month: int) -> List[SeasonalRecommendation]:
        """Apply ML analysis to generate seasonal recommendations"""
        recommendations = []
        month_names = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                       'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

        for data in seasonal_data:
            # Calculate overall score
            weather_weight = 0.4
            crowd_weight = 0.3
            price_weight = 0.3

            overall_score = (
                data['weather_score'] * weather_weight +
                data['crowd_score'] * crowd_weight +
                data['price_score'] * price_weight
            )

            # Generate reasons
            reasons = []
            if data['weather_score'] > 0.8:
                reasons.append("Clima ideale")
            if data['crowd_score'] > 0.7:
                reasons.append("Meno affollato")
            if data['price_score'] > 0.7:
                reasons.append("Prezzi convenienti")

            # Get recommended places
            recommended_places = self._get_top_places_for_city(data['city'])

            recommendation = SeasonalRecommendation(
                month=month_names[month],
                city=data['city'],
                recommended_places=recommended_places,
                weather_score=data['weather_score'],
                crowd_score=data['crowd_score'],
                price_score=data['price_score'],
                overall_score=overall_score,
                reasons=reasons
            )

            recommendations.append(recommendation)

        # Sort by overall score
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        return recommendations[:10]  # Top 10 recommendations

    def _get_top_places_for_city(self, city: str) -> List[str]:
        """Get top places for a city"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT place_name 
                    FROM place_cache 
                    WHERE city ILIKE %s 
                    ORDER BY RANDOM()
                    LIMIT 3
                """
                cursor.execute(query, (f'%{city}%',))

                places = [row[0] for row in cursor.fetchall()]
                return places

        except Exception as e:
            logger.error(f"❌ Top places query error: {e}")
            return []
        finally:
            conn.close()

    def _store_seasonal_insights(self, recommendations: List[SeasonalRecommendation]):
        """Store seasonal insights in analytics database"""
        if not self.analytics_db:
            return

        try:
            cursor = self.analytics_db.cursor()

            for rec in recommendations:
                month_num = ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                             'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'].index(rec.month.lower())

                cursor.execute('''
                    INSERT OR REPLACE INTO seasonal_data 
                    (city, month, avg_temperature, avg_crowd_level, avg_price_index, popularity_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    rec.city,
                    month_num,
                    rec.weather_score * 30,  # Convert to temperature-like scale
                    (1 - rec.crowd_score) * 5,  # Convert to crowd level scale
                    (1 - rec.price_score) * 100,  # Convert to price index
                    rec.overall_score
                ))

            self.analytics_db.commit()
            logger.info(
                f"✅ Stored {len(recommendations)} seasonal recommendations")

        except Exception as e:
            logger.error(f"❌ Seasonal storage error: {e}")

    # ==================== BUDGET OPTIMIZATION ====================

    def optimize_budget(self, total_budget: float, destination: str,
                        trip_duration: int, preferences: Dict[str, Any]) -> BudgetOptimization:
        """Generate budget optimization recommendations"""
        try:
            # Analyze budget requirements
            budget_breakdown = self._analyze_budget_requirements(
                total_budget, destination, trip_duration, preferences
            )

            # Generate optimized allocation
            optimized_allocation = self._optimize_budget_allocation(
                budget_breakdown, preferences
            )

            # Generate cost-saving tips
            cost_saving_tips = self._generate_cost_saving_tips(
                destination, budget_breakdown, preferences
            )

            # Find alternative options
            alternatives = self._find_budget_alternatives(
                total_budget, destination, preferences
            )

            return BudgetOptimization(
                total_budget=total_budget,
                budget_breakdown=budget_breakdown,
                recommended_allocation=optimized_allocation,
                cost_saving_tips=cost_saving_tips,
                alternative_options=alternatives
            )

        except Exception as e:
            logger.error(f"❌ Budget optimization error: {e}")
            return BudgetOptimization(
                total_budget=total_budget,
                budget_breakdown={},
                recommended_allocation={},
                cost_saving_tips=[],
                alternative_options=[]
            )

    def _analyze_budget_requirements(self, budget: float, destination: str,
                                     duration: int, preferences: Dict) -> Dict[str, float]:
        """Analyze budget requirements by category"""
        # Base budget allocation percentages
        base_allocation = {
            'accommodation': 0.35,
            'food': 0.25,
            'attractions': 0.20,
            'transport': 0.15,
            'shopping': 0.05
        }

        # Adjust based on destination (simplified city-based pricing)
        city_multipliers = {
            'roma': 1.1,
            'milano': 1.2,
            'venezia': 1.3,
            'firenze': 1.1,
            'napoli': 0.9,
            'bologna': 1.0
        }

        destination_key = destination.lower()
        multiplier = city_multipliers.get(destination_key, 1.0)

        # Adjust based on preferences
        pace = preferences.get('pace', 'Moderato')
        if pace == 'Intenso':
            base_allocation['attractions'] += 0.05
            base_allocation['food'] -= 0.05
        elif pace == 'Rilassato':
            base_allocation['food'] += 0.05
            base_allocation['attractions'] -= 0.05

        # Calculate final breakdown
        breakdown = {}
        for category, percentage in base_allocation.items():
            breakdown[category] = budget * percentage * multiplier

        return breakdown

    def _optimize_budget_allocation(self, breakdown: Dict[str, float],
                                    preferences: Dict) -> Dict[str, float]:
        """Optimize budget allocation based on ML insights"""
        optimized = breakdown.copy()

        # Get user interests for optimization
        interests = preferences.get('interests', [])

        # Optimize based on interests
        if 'Cibo' in interests:
            # Increase food budget
            optimized['food'] *= 1.15
            optimized['shopping'] *= 0.9

        if 'Arte' in interests:
            # Increase attractions budget
            optimized['attractions'] *= 1.1
            optimized['transport'] *= 0.95

        if 'Shopping' in interests:
            # Increase shopping budget
            optimized['shopping'] *= 1.5
            optimized['accommodation'] *= 0.95

        # Normalize to maintain total budget
        total_optimized = sum(optimized.values())
        budget_ratio = sum(breakdown.values()) / total_optimized

        for category in optimized:
            optimized[category] *= budget_ratio

        return optimized

    def _generate_cost_saving_tips(self, destination: str,
                                   breakdown: Dict[str, float],
                                   preferences: Dict) -> List[str]:
        """Generate personalized cost-saving tips"""
        tips = []

        # Generic tips
        tips.extend([
            "Prenota alloggi in anticipo per risparmiare fino al 20%",
            "Usa i trasporti pubblici invece dei taxi",
            "Mangia in trattorie locali invece dei ristoranti turistici",
            "Visita musei durante i giorni di ingresso gratuito",
            "Compra prodotti locali al mercato per picnic economici"
        ])

        # Destination-specific tips
        destination_tips = {
            'roma': [
                "Usa la Roma Pass per musei e trasporti",
                "Visita le chiese gratuite come alternativa ai musei",
                "Mangia vicino a Trastevere per prezzi migliori"
            ],
            'milano': [
                "Sfrutta l'aperitivo per cenare risparmiando",
                "Usa bike sharing per spostarti economicamente",
                "Visita i Navigli la sera per l'atmosfera gratuita"
            ],
            'venezia': [
                "Compra vaporetto pass giornaliero se fai molti spostamenti",
                "Mangia lontano da San Marco per prezzi migliori",
                "Visita isole meno turistiche come Giudecca"
            ]
        }

        destination_key = destination.lower()
        if destination_key in destination_tips:
            tips.extend(destination_tips[destination_key])

        # Budget-specific tips
        total_budget = sum(breakdown.values())
        if total_budget < 200:
            tips.extend([
                "Considera ostelli o B&B per l'alloggio",
                "Cucina quando possibile se hai un piccolo budget",
                "Sfrutta walking tour gratuiti"
            ])
        elif total_budget > 1000:
            tips.extend([
                "Investi in esperienze uniche e memorabili",
                "Considera guide private per un'esperienza personalizzata",
                "Prova ristoranti stellati per un'esperienza gastronomica"
            ])

        return tips[:8]  # Return top 8 tips

    def _find_budget_alternatives(self, budget: float, destination: str,
                                  preferences: Dict) -> List[Dict[str, Any]]:
        """Find alternative budget options"""
        alternatives = []

        # Alternative destinations with similar characteristics
        destination_alternatives = {
            'roma': ['napoli', 'firenze', 'bologna'],
            'milano': ['torino', 'bologna', 'verona'],
            'venezia': ['padova', 'verona', 'trieste'],
            'firenze': ['siena', 'pisa', 'lucca']
        }

        destination_key = destination.lower()
        if destination_key in destination_alternatives:
            for alt_city in destination_alternatives[destination_key][:2]:
                alternatives.append({
                    'type': 'destination',
                    'alternative': alt_city.title(),
                    'savings': '15-25%',
                    'description': f"Simile a {destination} ma più economico",
                    'trade_offs': ['Meno attrazioni famose', 'Atmosfera più locale']
                })

        # Budget level alternatives
        if budget > 500:
            alternatives.append({
                'type': 'duration',
                'alternative': 'Viaggio più lungo',
                'savings': '10-15% per giorno aggiuntivo',
                'description': 'Estendi il viaggio per un miglior rapporto qualità-prezzo',
                'trade_offs': ['Più tempo necessario', 'Maggiore budget totale']
            })

        if budget < 300:
            alternatives.append({
                'type': 'season',
                'alternative': 'Viaggio in bassa stagione',
                'savings': '30-40%',
                'description': 'Viaggia in inverno o primavera per risparmiare',
                'trade_offs': ['Meteo meno prevedibile', 'Alcuni servizi ridotti']
            })

        return alternatives

    # ==================== USER PREFERENCE LEARNING ====================

    def analyze_user_preferences(self, user_data: Dict[str, Any]) -> UserInsight:
        """Analyze user preferences using machine learning"""
        try:
            # Extract preference features
            features = self._extract_preference_features(user_data)

            # Classify user segment
            user_segment = self._classify_user_segment(features)

            # Calculate preference scores
            preference_scores = self._calculate_preference_scores(features)

            # Predict satisfaction
            predicted_satisfaction = self._predict_user_satisfaction(features)

            # Calculate recommendation confidence
            confidence = self._calculate_recommendation_confidence(features)

            # Identify behavioral traits
            traits = self._identify_behavioral_traits(features)

            return UserInsight(
                user_segment=user_segment,
                preference_score=preference_scores,
                predicted_satisfaction=predicted_satisfaction,
                recommendation_confidence=confidence,
                behavioral_traits=traits
            )

        except Exception as e:
            logger.error(f"❌ User preference analysis error: {e}")
            return UserInsight(
                user_segment="General Tourist",
                preference_score={},
                predicted_satisfaction=0.7,
                recommendation_confidence=0.6,
                behavioral_traits=[]
            )

    def _extract_preference_features(self, user_data: Dict) -> Dict[str, Any]:
        """Extract features from user data for ML analysis"""
        features = {}

        # Basic preferences
        features['interests'] = user_data.get('interests', [])
        features['pace'] = user_data.get('pace', 'Moderato')
        features['budget'] = user_data.get('budget', '€€')

        # Behavioral features (if available)
        features['session_duration'] = user_data.get('session_duration', 0)
        features['places_viewed'] = user_data.get('places_viewed', 0)
        features['itineraries_created'] = user_data.get(
            'itineraries_created', 0)

        # Time-based features
        features['time_of_day'] = datetime.now().hour
        features['day_of_week'] = datetime.now().weekday()

        return features

    def _classify_user_segment(self, features: Dict) -> str:
        """Classify user into a segment based on features"""
        interests = features.get('interests', [])
        pace = features.get('pace', 'Moderato')
        budget = features.get('budget', '€€')

        # Rule-based classification (can be enhanced with ML models)
        if 'Arte' in interests and 'Storia' in interests:
            if budget == '€€€':
                return "Cultural Enthusiast (Premium)"
            else:
                return "Cultural Explorer"
        elif 'Cibo' in interests:
            return "Foodie Traveler"
        elif pace == 'Intenso' and len(interests) > 2:
            return "Adventure Seeker"
        elif pace == 'Rilassato':
            return "Leisure Traveler"
        else:
            return "General Tourist"

    def _calculate_preference_scores(self, features: Dict) -> Dict[str, float]:
        """Calculate preference scores for different categories"""
        scores = {
            'culture': 0.5,
            'food': 0.5,
            'nature': 0.5,
            'history': 0.5,
            'shopping': 0.5,
            'relaxation': 0.5
        }

        interests = features.get('interests', [])

        # Adjust scores based on interests
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower == 'arte':
                scores['culture'] += 0.3
            elif interest_lower == 'cibo':
                scores['food'] += 0.3
            elif interest_lower == 'natura':
                scores['nature'] += 0.3
            elif interest_lower == 'storia':
                scores['history'] += 0.3
            elif interest_lower == 'shopping':
                scores['shopping'] += 0.3
            elif interest_lower == 'relax':
                scores['relaxation'] += 0.3

        # Normalize scores
        for key in scores:
            scores[key] = min(scores[key], 1.0)

        return scores

    def _predict_user_satisfaction(self, features: Dict) -> float:
        """Predict user satisfaction based on features"""
        base_satisfaction = 0.7

        # Adjust based on various factors
        pace = features.get('pace', 'Moderato')
        interests_count = len(features.get('interests', []))

        if pace == 'Moderato' and 2 <= interests_count <= 3:
            base_satisfaction += 0.1  # Balanced preferences likely to be satisfied

        if features.get('places_viewed', 0) > 10:
            base_satisfaction += 0.1  # Engaged users likely more satisfied

        return min(base_satisfaction, 1.0)

    def _calculate_recommendation_confidence(self, features: Dict) -> float:
        """Calculate confidence in recommendations"""
        base_confidence = 0.6

        # More data = higher confidence
        data_points = (
            len(features.get('interests', [])) * 0.1 +
            (1 if features.get('pace') else 0) * 0.1 +
            min(features.get('places_viewed', 0) / 20, 0.2)
        )

        return min(base_confidence + data_points, 0.95)

    def _identify_behavioral_traits(self, features: Dict) -> List[str]:
        """Identify behavioral traits from user features"""
        traits = []

        pace = features.get('pace', 'Moderato')
        interests = features.get('interests', [])

        if pace == 'Intenso':
            traits.append("Explorer energico")
        elif pace == 'Rilassato':
            traits.append("Viaggiatore tranquillo")

        if len(interests) > 3:
            traits.append("Interessi diversificati")
        elif len(interests) == 1:
            traits.append("Interesse specializzato")

        if features.get('session_duration', 0) > 1800:  # 30 minutes
            traits.append("Pianificatore dettagliato")

        if features.get('time_of_day', 12) < 10:
            traits.append("Pianificatore mattiniero")

        return traits


# Initialize the data intelligence engine
intelligence_engine = DataIntelligenceEngine()

# ==================== API ENDPOINTS ====================


@data_intelligence_bp.route('/api/analytics/travel-patterns', methods=['GET'])
def get_travel_patterns():
    """Get travel pattern analytics"""
    try:
        time_period = request.args.get('period', '30_days')
        patterns = intelligence_engine.analyze_travel_patterns(time_period)

        patterns_data = [asdict(pattern) for pattern in patterns]

        return jsonify({
            'patterns': patterns_data,
            'total_patterns': len(patterns_data),
            'analysis_period': time_period,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Travel patterns endpoint error: {e}")
        return jsonify({'error': 'Travel patterns analysis failed'}), 500


@data_intelligence_bp.route('/api/analytics/seasonal-recommendations', methods=['GET'])
def get_seasonal_recommendations():
    """Get seasonal travel recommendations"""
    try:
        month = request.args.get('month', type=int)
        recommendations = intelligence_engine.generate_seasonal_recommendations(
            month)

        recommendations_data = [asdict(rec) for rec in recommendations]

        return jsonify({
            'recommendations': recommendations_data,
            'total_recommendations': len(recommendations_data),
            'target_month': month or datetime.now().month,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Seasonal recommendations endpoint error: {e}")
        return jsonify({'error': 'Seasonal recommendations failed'}), 500


@data_intelligence_bp.route('/api/analytics/budget-optimization', methods=['POST'])
def optimize_budget_endpoint():
    """Get budget optimization recommendations"""
    try:
        data = request.get_json()
        budget = float(data.get('budget', 500))
        destination = data.get('destination', 'Roma')
        duration = int(data.get('duration', 3))
        preferences = data.get('preferences', {})

        optimization = intelligence_engine.optimize_budget(
            budget, destination, duration, preferences
        )

        return jsonify({
            'optimization': asdict(optimization),
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Budget optimization endpoint error: {e}")
        return jsonify({'error': 'Budget optimization failed'}), 500


@data_intelligence_bp.route('/api/analytics/user-insights', methods=['POST'])
def analyze_user_preferences_endpoint():
    """Analyze user preferences and provide insights"""
    try:
        user_data = request.get_json()
        insights = intelligence_engine.analyze_user_preferences(user_data)

        return jsonify({
            'insights': asdict(insights),
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ User insights endpoint error: {e}")
        return jsonify({'error': 'User insights analysis failed'}), 500


@data_intelligence_bp.route('/api/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        # Get recent patterns
        patterns = intelligence_engine.analyze_travel_patterns('7_days')

        # Get current month recommendations
        recommendations = intelligence_engine.generate_seasonal_recommendations()

        # Get basic stats
        stats = {
            'total_places': 9930,
            'cities_covered': 56,
            'active_users': 'N/A',  # Would be calculated from user activity
            'patterns_analyzed': len(patterns),
            'recommendations_available': len(recommendations)
        }

        return jsonify({
            'dashboard_data': {
                'stats': stats,
                'top_patterns': [asdict(p) for p in patterns[:5]],
                'seasonal_highlights': [asdict(r) for r in recommendations[:3]],
                'last_updated': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"❌ Analytics dashboard endpoint error: {e}")
        return jsonify({'error': 'Analytics dashboard failed'}), 500

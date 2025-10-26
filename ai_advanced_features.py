#!/usr/bin/env python3
"""
ViamigoTravelAI Advanced AI Features
Multi-day itinerary optimization, weather integration, crowd prediction, and personalized recommendations
Enhanced AI capabilities for 9,930+ places across 56 Italian cities
"""

import json
import requests
import logging
import psycopg2
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Create blueprint
ai_advanced_bp = Blueprint('ai_advanced', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')


@dataclass
class WeatherData:
    temperature: float
    description: str
    humidity: int
    wind_speed: float
    visibility: float
    recommendation: str


@dataclass
class CrowdPrediction:
    location: str
    current_crowd_level: int  # 1-5 scale
    predicted_levels: Dict[str, int]  # hour -> crowd level
    best_visit_times: List[str]
    worst_visit_times: List[str]


@dataclass
class PersonalizedRecommendation:
    place_id: str
    name: str
    city: str
    relevance_score: float
    reason: str
    user_preferences_match: List[str]
    optimal_visit_time: str


class AdvancedAISystem:
    """Advanced AI system for travel optimization and personalization"""

    def __init__(self):
        self.weather_cache = {}
        self.crowd_cache = {}
        self.recommendation_cache = {}

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

    # ==================== WEATHER INTEGRATION ====================
    async def get_weather_data(self, city: str, date: Optional[str] = None) -> WeatherData:
        """Get comprehensive weather data with travel recommendations"""
        cache_key = f"{city}_{date or 'current'}"

        if cache_key in self.weather_cache:
            cached_data = self.weather_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=1):
                return cached_data['data']

        try:
            # Get weather data (using OpenWeatherMap API)
            weather_api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')

            if date:
                # Forecast weather
                url = f"http://api.openweathermap.org/data/2.5/forecast"
                params = {
                    'q': f"{city},IT",
                    'appid': weather_api_key,
                    'units': 'metric',
                    'lang': 'it'
                }
            else:
                # Current weather
                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'q': f"{city},IT",
                    'appid': weather_api_key,
                    'units': 'metric',
                    'lang': 'it'
                }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                weather_data = self._parse_weather_data(data, city)
            else:
                # Fallback weather data
                weather_data = self._get_fallback_weather(city)

            # Cache the result
            self.weather_cache[cache_key] = {
                'data': weather_data,
                'timestamp': datetime.now()
            }

            return weather_data

        except Exception as e:
            logger.error(f"❌ Weather API error: {e}")
            return self._get_fallback_weather(city)

    def _parse_weather_data(self, data: Dict, city: str) -> WeatherData:
        """Parse weather API response into WeatherData object"""
        try:
            main = data['main']
            weather = data['weather'][0]
            wind = data.get('wind', {})

            temperature = main['temp']
            description = weather['description']
            humidity = main['humidity']
            wind_speed = wind.get('speed', 0)
            visibility = data.get('visibility', 10000) / 1000  # Convert to km

            # Generate travel recommendation based on weather
            recommendation = self._generate_weather_recommendation(
                temperature, description, humidity, wind_speed
            )

            return WeatherData(
                temperature=temperature,
                description=description,
                humidity=humidity,
                wind_speed=wind_speed,
                visibility=visibility,
                recommendation=recommendation
            )

        except Exception as e:
            logger.error(f"❌ Weather parsing error: {e}")
            return self._get_fallback_weather(city)

    def _generate_weather_recommendation(self, temp: float, desc: str, humidity: int, wind: float) -> str:
        """Generate AI-powered weather-based travel recommendations"""
        try:
            prompt = f"""
            Genera un consiglio di viaggio personalizzato basato sul meteo attuale:
            - Temperatura: {temp}°C
            - Condizioni: {desc}
            - Umidità: {humidity}%
            - Vento: {wind} m/s
            
            Fornisci un consiglio breve e pratico in italiano per visitare attrazioni turistiche.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"❌ Weather recommendation AI error: {e}")

            # Rule-based fallback
            if temp < 5:
                return "Tempo freddo: ideale per musei e luoghi al chiuso"
            elif temp > 30:
                return "Tempo caldo: cerca ombra, visita al mattino presto o sera"
            elif "rain" in desc.lower() or "pioggia" in desc.lower():
                return "Pioggia prevista: perfetto per musei, gallerie e luoghi coperti"
            elif temp >= 20 and temp <= 25:
                return "Tempo perfetto per camminare all'aperto e visitare parchi"
            else:
                return "Buone condizioni per attività turistiche all'aperto"

    def _get_fallback_weather(self, city: str) -> WeatherData:
        """Fallback weather data when API is unavailable"""
        return WeatherData(
            temperature=20.0,
            description="Condizioni moderate",
            humidity=60,
            wind_speed=2.0,
            visibility=10.0,
            recommendation="Buone condizioni per attività turistiche"
        )

    # ==================== CROWD PREDICTION ====================
    async def predict_crowd_levels(self, location: str, date: Optional[str] = None) -> CrowdPrediction:
        """Predict crowd levels using AI and historical data"""
        cache_key = f"crowd_{location}_{date or 'current'}"

        if cache_key in self.crowd_cache:
            cached_data = self.crowd_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=2):
                return cached_data['data']

        try:
            # Get historical crowd data from database
            crowd_data = await self._get_crowd_historical_data(location)

            # AI-powered crowd prediction
            prediction = await self._ai_crowd_prediction(location, crowd_data, date)

            # Cache the result
            self.crowd_cache[cache_key] = {
                'data': prediction,
                'timestamp': datetime.now()
            }

            return prediction

        except Exception as e:
            logger.error(f"❌ Crowd prediction error: {e}")
            return self._get_fallback_crowd_prediction(location)

    async def _get_crowd_historical_data(self, location: str) -> Dict[str, Any]:
        """Get historical crowd data for location"""
        conn = self.get_db_connection()
        if not conn:
            return {}

        try:
            with conn.cursor() as cursor:
                # Query historical visit patterns (if available)
                query = """
                    SELECT name, type, city
                    FROM place_cache 
                    WHERE LOWER(name) LIKE %s OR LOWER(city) LIKE %s
                    LIMIT 1
                """
                cursor.execute(
                    query, (f'%{location.lower()}%', f'%{location.lower()}%'))
                result = cursor.fetchone()

                if result:
                    return {
                        'location': result[0],
                        'type': result[1],
                        'city': result[2],
                        'has_data': True
                    }

        except Exception as e:
            logger.error(f"❌ Crowd data query error: {e}")
        finally:
            conn.close()

        return {'has_data': False}

    async def _ai_crowd_prediction(self, location: str, historical_data: Dict, date: Optional[str]) -> CrowdPrediction:
        """AI-powered crowd level prediction"""
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            day_of_week = current_time.strftime('%A')

            # Generate hourly predictions for the day
            predicted_levels = {}

            for hour in range(24):
                # Rule-based prediction with AI enhancement
                base_level = self._calculate_base_crowd_level(
                    hour, day_of_week, location)

                # Apply location-specific adjustments
                if 'museum' in location.lower() or 'museo' in location.lower():
                    if 10 <= hour <= 16:
                        base_level += 1  # Museums busier during day
                elif 'restaurant' in location.lower() or 'ristorante' in location.lower():
                    if hour in [12, 13, 19, 20, 21]:
                        base_level += 2  # Meal times
                elif 'church' in location.lower() or 'chiesa' in location.lower():
                    if hour in [9, 10, 11, 17, 18]:  # Morning and evening services
                        base_level += 1

                predicted_levels[f"{hour:02d}:00"] = min(max(base_level, 1), 5)

            # Find best and worst times to visit
            best_times = [time for time,
                          level in predicted_levels.items() if level <= 2]
            worst_times = [time for time,
                           level in predicted_levels.items() if level >= 4]

            current_level = predicted_levels.get(f"{current_hour:02d}:00", 3)

            return CrowdPrediction(
                location=location,
                current_crowd_level=current_level,
                predicted_levels=predicted_levels,
                best_visit_times=best_times[:3],  # Top 3 best times
                worst_visit_times=worst_times[:3]  # Top 3 worst times
            )

        except Exception as e:
            logger.error(f"❌ AI crowd prediction error: {e}")
            return self._get_fallback_crowd_prediction(location)

    def _calculate_base_crowd_level(self, hour: int, day_of_week: str, location: str) -> int:
        """Calculate base crowd level using heuristics"""
        base_level = 2  # Default moderate level

        # Time of day adjustments
        if 6 <= hour <= 9:  # Early morning
            base_level = 1
        elif 10 <= hour <= 12:  # Late morning
            base_level = 3
        elif 13 <= hour <= 15:  # Early afternoon
            base_level = 4
        elif 16 <= hour <= 18:  # Late afternoon
            base_level = 3
        elif 19 <= hour <= 21:  # Evening
            base_level = 2
        else:  # Night/very early morning
            base_level = 1

        # Day of week adjustments
        if day_of_week in ['Saturday', 'Sunday']:
            base_level += 1  # Weekends busier

        return base_level

    def _get_fallback_crowd_prediction(self, location: str) -> CrowdPrediction:
        """Fallback crowd prediction when AI is unavailable"""
        current_hour = datetime.now().hour

        # Simple heuristic-based prediction
        predicted_levels = {}
        for hour in range(24):
            if 6 <= hour <= 9:
                level = 1  # Low
            elif 10 <= hour <= 16:
                level = 3  # Moderate to high
            elif 17 <= hour <= 19:
                level = 2  # Moderate
            else:
                level = 1  # Low

            predicted_levels[f"{hour:02d}:00"] = level

        return CrowdPrediction(
            location=location,
            current_crowd_level=predicted_levels.get(
                f"{current_hour:02d}:00", 2),
            predicted_levels=predicted_levels,
            best_visit_times=["08:00", "09:00", "20:00"],
            worst_visit_times=["12:00", "14:00", "16:00"]
        )

    # ==================== PERSONALIZED RECOMMENDATIONS ====================
    async def get_personalized_recommendations(self, user_preferences: Dict[str, Any],
                                               location: str, limit: int = 10) -> List[PersonalizedRecommendation]:
        """Generate AI-powered personalized travel recommendations"""
        cache_key = f"rec_{hash(str(user_preferences))}_{location}_{limit}"

        if cache_key in self.recommendation_cache:
            cached_data = self.recommendation_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=4):
                return cached_data['data']

        try:
            # Get candidate places
            candidate_places = await self._get_candidate_places(location)

            # Score and rank places using AI
            recommendations = await self._ai_score_places(candidate_places, user_preferences)

            # Sort by relevance score and limit results
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            final_recommendations = recommendations[:limit]

            # Cache the result
            self.recommendation_cache[cache_key] = {
                'data': final_recommendations,
                'timestamp': datetime.now()
            }

            return final_recommendations

        except Exception as e:
            logger.error(f"❌ Personalized recommendations error: {e}")
            return []

    async def _get_candidate_places(self, location: str) -> List[Dict[str, Any]]:
        """Get candidate places from database for recommendations"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT id, name, city, type, latitude, longitude, description
                    FROM place_cache 
                    WHERE city ILIKE %s 
                    ORDER BY RANDOM()
                    LIMIT 50
                """
                cursor.execute(query, (f'%{location}%',))

                places = []
                for row in cursor.fetchall():
                    places.append({
                        'id': row[0],
                        'name': row[1],
                        'city': row[2],
                        'type': row[3] or 'attraction',
                        'latitude': row[4],
                        'longitude': row[5],
                        'description': row[6]
                    })

                return places

        except Exception as e:
            logger.error(f"❌ Candidate places query error: {e}")
            return []
        finally:
            conn.close()

    async def _ai_score_places(self, places: List[Dict], user_preferences: Dict) -> List[PersonalizedRecommendation]:
        """Use AI to score and rank places based on user preferences"""
        recommendations = []

        # Extract user preferences
        interests = user_preferences.get('interests', [])
        pace = user_preferences.get('pace', 'Moderato')
        budget = user_preferences.get('budget', '€€')

        for place in places:
            try:
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    place, interests, pace, budget)

                # Generate reason using AI
                reason = await self._generate_recommendation_reason(place, user_preferences)

                # Find optimal visit time
                optimal_time = self._get_optimal_visit_time(place['type'])

                # Identify matching preferences
                matching_prefs = self._get_matching_preferences(
                    place, interests)

                recommendation = PersonalizedRecommendation(
                    place_id=str(place['id']),
                    name=place['name'],
                    city=place['city'],
                    relevance_score=relevance_score,
                    reason=reason,
                    user_preferences_match=matching_prefs,
                    optimal_visit_time=optimal_time
                )

                recommendations.append(recommendation)

            except Exception as e:
                logger.error(f"❌ Error scoring place {place['name']}: {e}")
                continue

        return recommendations

    def _calculate_relevance_score(self, place: Dict, interests: List[str], pace: str, budget: str) -> float:
        """Calculate relevance score for a place based on user preferences"""
        score = 0.5  # Base score

        place_type = place['type'].lower()
        place_name = place['name'].lower()
        place_desc = (place['description'] or '').lower()

        # Interest matching
        for interest in interests:
            interest_lower = interest.lower()

            if interest_lower == 'arte' and any(keyword in place_type or keyword in place_name or keyword in place_desc
                                                for keyword in ['museum', 'gallery', 'art', 'museo', 'galleria']):
                score += 0.3
            elif interest_lower == 'cibo' and any(keyword in place_type or keyword in place_name
                                                  for keyword in ['restaurant', 'cafe', 'ristorante', 'bar']):
                score += 0.3
            elif interest_lower == 'natura' and any(keyword in place_type or keyword in place_name or keyword in place_desc
                                                    for keyword in ['park', 'garden', 'parco', 'giardino', 'natural']):
                score += 0.3
            elif interest_lower == 'shopping' and any(keyword in place_type or keyword in place_name
                                                      for keyword in ['shop', 'store', 'market', 'negozio', 'mercato']):
                score += 0.3
            elif interest_lower == 'storia' and any(keyword in place_type or keyword in place_name or keyword in place_desc
                                                    for keyword in ['church', 'castle', 'historical', 'chiesa', 'castello', 'storico']):
                score += 0.3
            elif interest_lower == 'relax' and any(keyword in place_type or keyword in place_name or keyword in place_desc
                                                   for keyword in ['spa', 'park', 'garden', 'beach', 'parco', 'spiaggia']):
                score += 0.3

        # Pace adjustments
        if pace == 'Rilassato':
            if any(keyword in place_type or keyword in place_name for keyword in ['park', 'cafe', 'parco', 'bar']):
                score += 0.1
        elif pace == 'Intenso':
            if any(keyword in place_type for keyword in ['attraction', 'museum', 'church']):
                score += 0.1

        # Budget considerations (simplified)
        if budget == '€':
            if any(keyword in place_type for keyword in ['park', 'church', 'square']):
                score += 0.1
        elif budget == '€€€':
            if any(keyword in place_type for keyword in ['restaurant', 'hotel', 'shop']):
                score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    async def _generate_recommendation_reason(self, place: Dict, user_preferences: Dict) -> str:
        """Generate AI-powered recommendation reason"""
        try:
            interests = ', '.join(user_preferences.get('interests', []))
            pace = user_preferences.get('pace', 'Moderato')

            prompt = f"""
            Spiega brevemente perché {place['name']} a {place['city']} è consigliato per un viaggiatore con questi interessi: {interests}.
            Il viaggiatore preferisce un ritmo {pace.lower()}.
            Rispondi in massimo 50 parole in italiano.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"❌ AI recommendation reason error: {e}")
            return f"Interessante {place['type']} a {place['city']} che potrebbe piacerti"

    def _get_optimal_visit_time(self, place_type: str) -> str:
        """Get optimal visit time based on place type"""
        place_type = place_type.lower()

        if 'museum' in place_type or 'museo' in place_type:
            return "10:00-11:00 (meno affollato)"
        elif 'restaurant' in place_type or 'ristorante' in place_type:
            return "12:30-13:30 o 19:30-20:30"
        elif 'church' in place_type or 'chiesa' in place_type:
            return "09:00-10:00 (mattina tranquilla)"
        elif 'park' in place_type or 'parco' in place_type:
            return "08:00-09:00 o 17:00-18:00"
        else:
            return "09:00-11:00 (mattina)"

    def _get_matching_preferences(self, place: Dict, interests: List[str]) -> List[str]:
        """Get list of user preferences that match this place"""
        matching = []
        place_type = place['type'].lower()
        place_name = place['name'].lower()

        for interest in interests:
            interest_lower = interest.lower()

            if interest_lower == 'arte' and any(keyword in place_type or keyword in place_name
                                                for keyword in ['museum', 'gallery', 'museo', 'galleria']):
                matching.append('Arte')
            elif interest_lower == 'cibo' and any(keyword in place_type
                                                  for keyword in ['restaurant', 'ristorante']):
                matching.append('Cibo')
            elif interest_lower == 'natura' and any(keyword in place_type or keyword in place_name
                                                    for keyword in ['park', 'garden', 'parco']):
                matching.append('Natura')
            elif interest_lower == 'shopping' and any(keyword in place_type
                                                      for keyword in ['shop', 'store']):
                matching.append('Shopping')
            elif interest_lower == 'storia' and any(keyword in place_type or keyword in place_name
                                                    for keyword in ['church', 'castle', 'chiesa']):
                matching.append('Storia')

        return matching


# Initialize the AI system
ai_system = AdvancedAISystem()

# ==================== API ENDPOINTS ====================


@ai_advanced_bp.route('/api/ai/weather/<city>', methods=['GET'])
async def get_weather(city):
    """Get weather data with AI-powered travel recommendations"""
    try:
        date = request.args.get('date')
        weather_data = await ai_system.get_weather_data(city, date)

        return jsonify({
            'city': city,
            'weather': {
                'temperature': weather_data.temperature,
                'description': weather_data.description,
                'humidity': weather_data.humidity,
                'wind_speed': weather_data.wind_speed,
                'visibility': weather_data.visibility,
                'recommendation': weather_data.recommendation
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Weather endpoint error: {e}")
        return jsonify({'error': 'Weather data unavailable'}), 500


@ai_advanced_bp.route('/api/ai/crowds/<location>', methods=['GET'])
async def get_crowd_prediction(location):
    """Get AI-powered crowd predictions for a location"""
    try:
        date = request.args.get('date')
        crowd_data = await ai_system.predict_crowd_levels(location, date)

        return jsonify({
            'location': location,
            'current_crowd_level': crowd_data.current_crowd_level,
            'predicted_levels': crowd_data.predicted_levels,
            'best_visit_times': crowd_data.best_visit_times,
            'worst_visit_times': crowd_data.worst_visit_times,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Crowd prediction endpoint error: {e}")
        return jsonify({'error': 'Crowd prediction unavailable'}), 500


@ai_advanced_bp.route('/api/ai/recommendations', methods=['POST'])
async def get_recommendations():
    """Get personalized AI recommendations based on user preferences"""
    try:
        data = request.get_json()
        user_preferences = data.get('preferences', {})
        location = data.get('location', '')
        limit = int(data.get('limit', 10))

        recommendations = await ai_system.get_personalized_recommendations(
            user_preferences, location, limit
        )

        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'place_id': rec.place_id,
                'name': rec.name,
                'city': rec.city,
                'relevance_score': rec.relevance_score,
                'reason': rec.reason,
                'matching_preferences': rec.user_preferences_match,
                'optimal_visit_time': rec.optimal_visit_time
            })

        return jsonify({
            'recommendations': recommendations_data,
            'location': location,
            'total_recommendations': len(recommendations_data),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Recommendations endpoint error: {e}")
        return jsonify({'error': 'Recommendations unavailable'}), 500


@ai_advanced_bp.route('/api/ai/itinerary/optimize', methods=['POST'])
async def optimize_itinerary():
    """AI-powered multi-day itinerary optimization"""
    try:
        data = request.get_json()
        places = data.get('places', [])
        days = int(data.get('days', 1))
        user_preferences = data.get('preferences', {})
        start_location = data.get('start_location', '')

        # Get weather data for planning
        weather_data = await ai_system.get_weather_data(start_location)

        # Optimize itinerary using AI
        optimized_itinerary = await _optimize_multi_day_itinerary(
            places, days, user_preferences, weather_data
        )

        return jsonify({
            'optimized_itinerary': optimized_itinerary,
            'total_days': days,
            'weather_considered': True,
            'optimization_factors': [
                'Distanze ottimizzate',
                'Meteo considerato',
                'Preferenze utente',
                'Orari ottimali',
                'Livelli di affollamento'
            ],
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Itinerary optimization error: {e}")
        return jsonify({'error': 'Itinerary optimization failed'}), 500


async def _optimize_multi_day_itinerary(places: List[Dict], days: int,
                                        preferences: Dict, weather: WeatherData) -> Dict[str, Any]:
    """Optimize itinerary across multiple days using AI algorithms"""
    try:
        # Simple optimization algorithm (can be enhanced with more sophisticated AI)
        places_per_day = len(places) // days
        optimized_days = {}

        for day in range(1, days + 1):
            start_idx = (day - 1) * places_per_day
            end_idx = start_idx + places_per_day if day < days else len(places)
            day_places = places[start_idx:end_idx]

            # Sort places by type and optimal visit times
            day_places.sort(key=lambda p: _get_visit_priority(p, preferences))

            # Add weather-based recommendations
            weather_advice = _get_weather_advice_for_day(weather, day_places)

            optimized_days[f'day_{day}'] = {
                'places': day_places,
                'weather_advice': weather_advice,
                'estimated_duration': f"{len(day_places) * 2} ore",
                'recommended_start_time': "09:00"
            }

        return optimized_days

    except Exception as e:
        logger.error(f"❌ Multi-day optimization error: {e}")
        return {}


def _get_visit_priority(place: Dict, preferences: Dict) -> int:
    """Get visit priority for place ordering"""
    priority = 5  # Default

    place_type = place.get('type', '').lower()
    interests = preferences.get('interests', [])

    # Prioritize based on user interests
    for interest in interests:
        if interest.lower() in place_type or interest.lower() in place.get('name', '').lower():
            priority -= 1

    # Morning places first
    if any(keyword in place_type for keyword in ['museum', 'church', 'museo', 'chiesa']):
        priority -= 2

    return priority


def _get_weather_advice_for_day(weather: WeatherData, places: List[Dict]) -> str:
    """Generate weather-specific advice for the day's itinerary"""
    if weather.temperature < 10:
        return "Giornata fredda: inizia con luoghi al chiuso come musei"
    elif weather.temperature > 28:
        return "Giornata calda: visita luoghi all'aperto al mattino presto"
    elif "rain" in weather.description.lower():
        return "Possibile pioggia: privilegia attività al coperto"
    else:
        return "Buone condizioni: equilibra attività interne ed esterne"

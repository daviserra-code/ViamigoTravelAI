"""
Weather-Aware Intelligence System for Viamigo
Automatically detects weather conditions and triggers Plan B when needed
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from api_error_handler import resilient_api_call, with_cache, APICache

logger = logging.getLogger(__name__)

# Cache for weather data (30 minutes TTL)
weather_cache = APICache(ttl_seconds=1800)


class WeatherIntelligence:
    """Weather monitoring and prediction system"""

    def __init__(self):
        # OpenWeatherMap API as primary weather source (free tier available)
        self.weather_api_key = os.environ.get("OPENWEATHER_API_KEY", "")
        self.weather_base_url = "https://api.openweathermap.org/data/2.5"

        # Weather thresholds for triggering Plan B
        self.thresholds = {
            'rain': {
                'light': 0.5,  # mm/hour
                'moderate': 2.5,
                'heavy': 7.5
            },
            'wind': {
                'moderate': 10,  # m/s
                'strong': 15,
                'dangerous': 20
            },
            'temperature': {
                'cold': 5,  # Celsius
                'hot': 35,
                'extreme_cold': 0,
                'extreme_hot': 40
            },
            'visibility': 1000,  # meters
            'snow': 1  # mm/hour
        }

    @resilient_api_call('weather', fallback_data={'weather': 'unknown', 'trigger_plan_b': False})
    @with_cache(weather_cache, lambda *args, **kwargs: f"weather_{args[1]}_{args[2]}")
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """Get current weather conditions for a location"""

        # If no API key, use mock data for demo
        if not self.weather_api_key:
            return self._get_fallback_weather(lat, lon)

        try:
            url = f"{self.weather_base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.weather_api_key,
                'units': 'metric'
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            return {
                'location': data.get('name', 'Unknown'),
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'weather': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
                'rain': data.get('rain', {}).get('1h', 0),
                'snow': data.get('snow', {}).get('1h', 0),
                'visibility': data.get('visibility', 10000),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return self._get_fallback_weather(lat, lon)

    def _get_fallback_weather(self, lat: float, lon: float) -> Dict:
        """Provide realistic weather based on location and season"""
        # Simulate weather based on latitude and current month
        month = datetime.now().month

        # Mediterranean climate for Italy
        if 35 < lat < 47 and 6 < lon < 19:  # Italy bounds
            if month in [6, 7, 8]:  # Summer
                return {
                    'location': 'Italy',
                    'temperature': 28,
                    'feels_like': 30,
                    'humidity': 65,
                    'wind_speed': 5,
                    'weather': 'Clear',
                    'description': 'clear sky',
                    'rain': 0,
                    'snow': 0,
                    'visibility': 10000,
                    'timestamp': datetime.now().isoformat()
                }
            elif month in [12, 1, 2]:  # Winter
                return {
                    'location': 'Italy',
                    'temperature': 8,
                    'feels_like': 6,
                    'humidity': 75,
                    'wind_speed': 8,
                    'weather': 'Clouds',
                    'description': 'overcast clouds',
                    'rain': 2,
                    'snow': 0,
                    'visibility': 8000,
                    'timestamp': datetime.now().isoformat()
                }

        # Default mild weather
        return {
            'location': 'Unknown',
            'temperature': 20,
            'feels_like': 20,
            'humidity': 60,
            'wind_speed': 5,
            'weather': 'Clouds',
            'description': 'few clouds',
            'rain': 0,
            'snow': 0,
            'visibility': 10000,
            'timestamp': datetime.now().isoformat()
        }

    def analyze_weather_conditions(self, weather_data: Dict) -> Tuple[str, bool, List[str]]:
        """
        Analyze weather conditions and determine if Plan B should be triggered

        Returns:
            - severity: 'good', 'moderate', 'bad', 'extreme'
            - trigger_plan_b: Boolean
            - reasons: List of weather issues
        """

        reasons = []
        severity_score = 0

        # Check rain
        rain = weather_data.get('rain', 0)
        if rain > self.thresholds['rain']['heavy']:
            reasons.append(f"Heavy rain ({rain:.1f}mm/h)")
            severity_score += 3
        elif rain > self.thresholds['rain']['moderate']:
            reasons.append(f"Moderate rain ({rain:.1f}mm/h)")
            severity_score += 2
        elif rain > self.thresholds['rain']['light']:
            reasons.append(f"Light rain ({rain:.1f}mm/h)")
            severity_score += 1

        # Check wind
        wind = weather_data.get('wind_speed', 0)
        if wind > self.thresholds['wind']['dangerous']:
            reasons.append(f"Dangerous winds ({wind:.1f}m/s)")
            severity_score += 4
        elif wind > self.thresholds['wind']['strong']:
            reasons.append(f"Strong winds ({wind:.1f}m/s)")
            severity_score += 2
        elif wind > self.thresholds['wind']['moderate']:
            reasons.append(f"Moderate winds ({wind:.1f}m/s)")
            severity_score += 1

        # Check temperature
        temp = weather_data.get('temperature', 20)
        if temp <= self.thresholds['temperature']['extreme_cold']:
            reasons.append(f"Extreme cold ({temp}°C)")
            severity_score += 3
        elif temp <= self.thresholds['temperature']['cold']:
            reasons.append(f"Cold weather ({temp}°C)")
            severity_score += 1
        elif temp >= self.thresholds['temperature']['extreme_hot']:
            reasons.append(f"Extreme heat ({temp}°C)")
            severity_score += 3
        elif temp >= self.thresholds['temperature']['hot']:
            reasons.append(f"Hot weather ({temp}°C)")
            severity_score += 1

        # Check visibility
        visibility = weather_data.get('visibility', 10000)
        if visibility < self.thresholds['visibility']:
            reasons.append(f"Poor visibility ({visibility}m)")
            severity_score += 2

        # Check snow
        snow = weather_data.get('snow', 0)
        if snow > self.thresholds['snow']:
            reasons.append(f"Snow ({snow:.1f}mm/h)")
            severity_score += 2

        # Determine severity
        if severity_score >= 5:
            severity = 'extreme'
            trigger_plan_b = True
        elif severity_score >= 3:
            severity = 'bad'
            trigger_plan_b = True
        elif severity_score >= 2:
            severity = 'moderate'
            trigger_plan_b = False  # Optional Plan B
        else:
            severity = 'good'
            trigger_plan_b = False

        return severity, trigger_plan_b, reasons

    def get_forecast(self, lat: float, lon: float, hours: int = 24) -> List[Dict]:
        """Get weather forecast for the next N hours"""

        if not self.weather_api_key:
            return self._get_fallback_forecast(hours)

        try:
            url = f"{self.weather_base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.weather_api_key,
                'units': 'metric',
                'cnt': hours // 3  # API returns 3-hour intervals
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            forecast = []
            for item in data['list']:
                forecast.append({
                    'time': datetime.fromtimestamp(item['dt']).isoformat(),
                    'temperature': item['main']['temp'],
                    'weather': item['weather'][0]['main'],
                    'description': item['weather'][0]['description'],
                    # Convert to hourly
                    'rain': item.get('rain', {}).get('3h', 0) / 3,
                    'wind_speed': item['wind']['speed']
                })

            return forecast

        except Exception as e:
            logger.error(f"Forecast API error: {e}")
            return self._get_fallback_forecast(hours)

    def _get_fallback_forecast(self, hours: int) -> List[Dict]:
        """Generate realistic forecast based on current conditions"""
        forecast = []
        base_time = datetime.now()

        for i in range(0, hours, 3):
            forecast.append({
                'time': (base_time + timedelta(hours=i)).isoformat(),
                'temperature': 20 + (5 if i < 12 else -2),
                'weather': 'Clouds' if i % 6 == 0 else 'Clear',
                'description': 'few clouds' if i % 6 == 0 else 'clear sky',
                'rain': 0.5 if i % 8 == 0 else 0,
                'wind_speed': 5 + (i % 3)
            })

        return forecast

    def suggest_weather_appropriate_activities(self, weather_data: Dict, activity_type: str) -> Dict:
        """Suggest weather-appropriate alternatives for activities"""

        weather_main = weather_data.get('weather', 'Clear')
        temp = weather_data.get('temperature', 20)
        rain = weather_data.get('rain', 0)
        location = weather_data.get('location', '').lower()

        # Extract city name (OpenWeather sometimes returns "Milan, IT" format)
        city = location.split(',')[0].strip().lower()

        suggestions = {
            'outdoor': [],
            'indoor': [],
            'covered': [],
            'tips': []
        }

        # City-specific indoor attractions (vary by location)
        city_indoor_attractions = {
            'milan': ["Duomo Cathedral", "Galleria Vittorio Emanuele II", "Pinacoteca di Brera", "La Scala Museum"],
            'milano': ["Duomo Cathedral", "Galleria Vittorio Emanuele II", "Pinacoteca di Brera", "La Scala Museum"],
            'rome': ["Vatican Museums", "Colosseum", "Capitoline Museums", "Borghese Gallery"],
            'roma': ["Vatican Museums", "Colosseum", "Capitoline Museums", "Borghese Gallery"],
            'florence': ["Uffizi Gallery", "Accademia Gallery", "Palazzo Pitti", "Bargello Museum"],
            'firenze': ["Uffizi Gallery", "Accademia Gallery", "Palazzo Pitti", "Bargello Museum"],
            'naples': ["Archaeological Museum", "Royal Palace", "Castel Nuovo", "San Carlo Theatre"],
            'napoli': ["Archaeological Museum", "Royal Palace", "Castel Nuovo", "San Carlo Theatre"],
            'venice': ["Doge's Palace", "St. Mark's Basilica", "Guggenheim Collection", "Correr Museum"],
            'venezia': ["Doge's Palace", "St. Mark's Basilica", "Guggenheim Collection", "Correr Museum"],
        }

        # Get city-specific attractions or use generic ones
        city_attractions = city_indoor_attractions.get(
            city, ["Museum visit", "Art gallery", "Shopping center"])

        # Rain conditions
        if rain > 0 or weather_main == 'Rain':
            suggestions['indoor'].extend(
                city_attractions[:3])  # Use city-specific
            suggestions['indoor'].extend([
                "Indoor market",
                "Cinema",
                "Cooking class"
            ])
            suggestions['covered'].extend([
                "Covered passages",
                "Train station architecture",
                "Church visit"
            ])
            suggestions['tips'].append("Bring umbrella and waterproof jacket")

        # Hot weather
        if temp >= 30:
            suggestions['indoor'].extend(
                city_attractions[:2])  # Use city-specific
            suggestions['indoor'].extend([
                "Shopping mall",
                "Indoor pool or spa"
            ])
            suggestions['outdoor'].extend([
                "Early morning walk",
                "Evening stroll",
                "Park with shade",
                "Beach or lake"
            ])
            suggestions['tips'].extend([
                "Stay hydrated - carry water bottle",
                "Avoid midday sun (12-16)",
                "Wear sunscreen SPF 30+ and hat"
            ])

        # Cold weather
        if temp <= 10:
            suggestions['indoor'].extend(
                city_attractions[:2])  # Use city-specific
            suggestions['indoor'].extend([
                "Thermal spa",
                "Library",
                "Cozy café"
            ])
            suggestions['outdoor'].extend([
                "Brisk walk in park",
                "Christmas markets (winter)" if city in [
                    'milano', 'roma', 'firenze'] else "Historic center walk",
                "Hot chocolate tour"
            ])
            suggestions['tips'].extend([
                "Dress in warm layers",
                "Wear comfortable walking shoes",
                "Bring gloves and scarf"
            ])

        # Perfect weather
        if 15 <= temp <= 25 and rain == 0 and weather_main in ['Clear', 'Clouds']:
            suggestions['outdoor'].extend([
                "Walking tour",
                "Bike rental",
                "Picnic in park",
                "Outdoor café",
                "Street photography",
                "Botanical garden"
            ])
            suggestions['tips'].append(
                "Perfect weather for outdoor activities!")

        return suggestions


# Global weather intelligence instance
weather_intelligence = WeatherIntelligence()


"""
Crowd Prediction System for Viamigo
Uses AI and patterns to predict busy times at attractions
"""


from api_error_handler import resilient_api_call, with_cache, APICache
from openai import OpenAI
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import dotenv
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Cache for crowd predictions (2 hours TTL)
crowd_cache = APICache(ttl_seconds=7200)


class CrowdPredictor:
    """Predicts crowd levels at tourist attractions"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        # Historical crowd patterns (general patterns for Italian attractions)
        self.patterns = {
            'museum': {
                'peak_hours': [11, 12, 14, 15, 16],
                'quiet_hours': [9, 10, 17, 18],
                'peak_days': ['saturday', 'sunday'],
                'quiet_days': ['tuesday', 'wednesday', 'thursday'],
                'seasonal_peak': [6, 7, 8],  # Summer months
                'seasonal_quiet': [1, 2, 11]  # Winter months
            },
            'restaurant': {
                'peak_hours': [13, 14, 20, 21],
                'quiet_hours': [11, 12, 15, 16, 17, 18],
                'peak_days': ['friday', 'saturday', 'sunday'],
                'quiet_days': ['monday', 'tuesday'],
                'seasonal_peak': [7, 8, 12],
                'seasonal_quiet': [1, 2, 3]
            },
            'beach': {
                'peak_hours': [11, 12, 13, 14, 15, 16],
                'quiet_hours': [7, 8, 9, 17, 18, 19],
                'peak_days': ['saturday', 'sunday'],
                'quiet_days': ['monday', 'tuesday', 'wednesday'],
                'seasonal_peak': [6, 7, 8],
                'seasonal_quiet': [11, 12, 1, 2, 3]
            },
            'church': {
                'peak_hours': [10, 11, 12, 17],
                'quiet_hours': [8, 9, 14, 15, 16],
                'peak_days': ['sunday'],
                'quiet_days': ['tuesday', 'wednesday', 'thursday'],
                'seasonal_peak': [7, 8, 12],
                'seasonal_quiet': [1, 2]
            },
            'shopping': {
                'peak_hours': [11, 12, 15, 16, 17, 18],
                'quiet_hours': [9, 10, 13, 14],
                'peak_days': ['saturday'],
                'quiet_days': ['monday', 'tuesday'],
                'seasonal_peak': [12, 7, 8],
                'seasonal_quiet': [1, 2]
            },
            'general': {
                'peak_hours': [11, 12, 14, 15, 16],
                'quiet_hours': [8, 9, 10, 17, 18],
                'peak_days': ['saturday', 'sunday'],
                'quiet_days': ['tuesday', 'wednesday'],
                'seasonal_peak': [7, 8],
                'seasonal_quiet': [1, 2, 11]
            }
        }

        # Special events that affect crowds
        self.italian_holidays = {
            '01-01': 'Capodanno',
            '01-06': 'Epifania',
            '04-25': 'Festa della Liberazione',
            '05-01': 'Festa del Lavoro',
            '06-02': 'Festa della Repubblica',
            '08-15': 'Ferragosto',
            '11-01': 'Ognissanti',
            '12-08': 'Immacolata Concezione',
            '12-25': 'Natale',
            '12-26': 'Santo Stefano'
        }

    def predict_crowd_level(self, place_name: str, place_type: str,
                            target_datetime: Optional[datetime] = None) -> Dict:
        """
        Predict crowd level for a specific place and time

        Returns crowd prediction with level, score, and recommendations
        """

        if target_datetime is None:
            target_datetime = datetime.now()

        # Get base pattern for place type
        pattern = self.patterns.get(
            place_type.lower(), self.patterns['general'])

        # Calculate crowd factors
        hour = target_datetime.hour
        day_name = target_datetime.strftime('%A').lower()
        month = target_datetime.month
        date_str = target_datetime.strftime('%m-%d')

        # Initialize score (0-100)
        crowd_score = 50
        factors = []

        # Hour factor (±30 points)
        if hour in pattern['peak_hours']:
            crowd_score += 30
            factors.append(f"Peak hour ({hour}:00)")
        elif hour in pattern['quiet_hours']:
            crowd_score -= 20
            factors.append(f"Quiet hour ({hour}:00)")
        else:
            factors.append(f"Normal hour ({hour}:00)")

        # Day factor (±20 points)
        if day_name in pattern['peak_days']:
            crowd_score += 20
            factors.append(f"Busy day ({day_name.capitalize()})")
        elif day_name in pattern['quiet_days']:
            crowd_score -= 15
            factors.append(f"Quiet day ({day_name.capitalize()})")

        # Season factor (±15 points)
        if month in pattern['seasonal_peak']:
            crowd_score += 15
            factors.append("Peak season")
        elif month in pattern['seasonal_quiet']:
            crowd_score -= 10
            factors.append("Low season")

        # Holiday factor (±25 points)
        if date_str in self.italian_holidays:
            crowd_score += 25
            factors.append(f"Holiday: {self.italian_holidays[date_str]}")

        # Weekend proximity
        if day_name == 'friday' and hour >= 17:
            crowd_score += 10
            factors.append("Weekend starting")

        # Normalize score
        crowd_score = max(0, min(100, crowd_score))

        # Determine crowd level
        if crowd_score >= 80:
            level = 'very_crowded'
            description = 'Very crowded - expect long waits'
            color = 'red'
        elif crowd_score >= 65:
            level = 'crowded'
            description = 'Crowded - moderate waits expected'
            color = 'orange'
        elif crowd_score >= 40:
            level = 'moderate'
            description = 'Moderate crowds - comfortable visit'
            color = 'yellow'
        elif crowd_score >= 20:
            level = 'quiet'
            description = 'Quiet - great time to visit'
            color = 'light_green'
        else:
            level = 'very_quiet'
            description = 'Very quiet - almost empty'
            color = 'green'

        # Generate recommendations
        recommendations = self._generate_recommendations(
            level, place_type, hour, day_name
        )

        # Find best alternative times
        best_times = self._find_best_visit_times(
            place_type, target_datetime
        )

        return {
            'place_name': place_name,
            'datetime': target_datetime.isoformat(),
            'crowd_level': level,
            'crowd_score': crowd_score,
            'description': description,
            'color': color,
            'factors': factors,
            'recommendations': recommendations,
            'best_alternative_times': best_times
        }

    def _generate_recommendations(self, level: str, place_type: str,
                                  hour: int, day: str) -> List[str]:
        """Generate smart recommendations based on crowd level"""

        recommendations = []

        if level in ['very_crowded', 'crowded']:
            recommendations.extend([
                "Book tickets online in advance if possible",
                "Consider visiting early morning or late afternoon",
                "Prepare for longer wait times",
                "Bring water and snacks"
            ])

            if place_type == 'museum':
                recommendations.append("Check for skip-the-line tickets")
                recommendations.append(
                    "Download the museum app for audio guide")
            elif place_type == 'restaurant':
                recommendations.append("Make a reservation")
                recommendations.append("Consider takeaway option")
            elif place_type == 'beach':
                recommendations.append("Arrive very early to secure a spot")
                recommendations.append("Consider less popular nearby beaches")

        elif level == 'moderate':
            recommendations.extend([
                "Good time to visit with reasonable crowds",
                "No advance booking typically needed",
                "Standard wait times expected"
            ])

        else:  # quiet or very_quiet
            recommendations.extend([
                "Excellent time to visit!",
                "Take your time exploring",
                "Great for photos without crowds",
                "Staff will have more time to assist"
            ])

            if place_type == 'restaurant':
                recommendations.append("No reservation needed")
                recommendations.append("Good time to try popular spots")

        return recommendations

    def _find_best_visit_times(self, place_type: str,
                               reference_date: datetime) -> List[Dict]:
        """Find the best times to visit in the next 7 days"""

        pattern = self.patterns.get(
            place_type.lower(), self.patterns['general'])
        best_times = []

        for days_ahead in range(7):
            check_date = reference_date + timedelta(days=days_ahead)

            for hour in pattern['quiet_hours']:
                visit_time = check_date.replace(hour=hour, minute=0, second=0)

                # Skip if in the past
                if visit_time < datetime.now():
                    continue

                day_name = visit_time.strftime('%A').lower()

                # Calculate score for this time
                score = 50
                if day_name in pattern['quiet_days']:
                    score -= 20
                if hour in pattern['quiet_hours']:
                    score -= 15
                if visit_time.month in pattern['seasonal_quiet']:
                    score -= 10

                if score < 30:  # Only include very quiet times
                    best_times.append({
                        'datetime': visit_time.isoformat(),
                        'day': visit_time.strftime('%A'),
                        'time': visit_time.strftime('%H:%M'),
                        'crowd_score': max(0, score),
                        'description': f"{visit_time.strftime('%A %H:%M')} - Very quiet"
                    })

        # Sort by crowd score and return top 5
        best_times.sort(key=lambda x: x['crowd_score'])
        return best_times[:5]

    @resilient_api_call('openai', fallback_data=None)
    @with_cache(crowd_cache, lambda *args, **kwargs: f"ai_crowd_{args[1]}_{args[2]}")
    def get_ai_crowd_insights(self, place_name: str, city: str) -> Optional[Dict]:
        """Use AI to get specific crowd insights for a place"""

        try:
            prompt = f"""
            Provide crowd pattern insights for {place_name} in {city}.
            
            Return a JSON with:
            {{
                "typical_wait_time": "average wait time",
                "peak_season": "when it's busiest",
                "local_tip": "insider tip to avoid crowds",
                "hidden_times": "secret best times locals know",
                "nearby_alternative": "less crowded similar place nearby"
            }}
            
            Be specific and accurate based on real data.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert on tourist crowds and local patterns."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=10
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"AI crowd insights error: {e}")
            return None

    def generate_crowd_aware_itinerary(self, places: List[Dict],
                                       start_time: datetime) -> List[Dict]:
        """Reorganize itinerary to minimize crowds"""

        optimized = []
        current_time = start_time

        # Sort places by predicted crowd level at their scheduled time
        for place in places:
            place_type = place.get('type', 'general')
            crowd_pred = self.predict_crowd_level(
                place['name'],
                place_type,
                current_time
            )
            place['crowd_prediction'] = crowd_pred
            place['scheduled_time'] = current_time
            current_time += timedelta(hours=place.get('duration', 1))

        # Reorder to visit crowded places at quieter times
        places_with_flexibility = []
        places_time_sensitive = []

        for place in places:
            if place.get('fixed_time', False):
                places_time_sensitive.append(place)
            else:
                places_with_flexibility.append(place)

        # Sort flexible places by crowd score (visit less crowded first)
        places_with_flexibility.sort(
            key=lambda x: x['crowd_prediction']['crowd_score']
        )

        # Rebuild itinerary
        final_itinerary = []
        current_time = start_time

        # Add time-sensitive places first
        for place in places_time_sensitive:
            place['optimized_time'] = place['scheduled_time']
            place['optimization_note'] = "Fixed time - cannot optimize"
            final_itinerary.append(place)

        # Add flexible places in optimized order
        for place in places_with_flexibility:
            # Find best time slot
            best_time = current_time
            best_score = 100

            for hour_offset in range(0, 8):
                test_time = start_time + timedelta(hours=hour_offset)
                test_pred = self.predict_crowd_level(
                    place['name'],
                    place.get('type', 'general'),
                    test_time
                )

                if test_pred['crowd_score'] < best_score:
                    best_score = test_pred['crowd_score']
                    best_time = test_time

            place['optimized_time'] = best_time
            place['optimization_note'] = f"Moved to avoid crowds (score: {best_score})"
            place['crowd_prediction'] = self.predict_crowd_level(
                place['name'],
                place.get('type', 'general'),
                best_time
            )
            final_itinerary.append(place)

        # Sort by optimized time
        final_itinerary.sort(key=lambda x: x['optimized_time'])

        return final_itinerary


# Global crowd predictor instance
crowd_predictor = CrowdPredictor()

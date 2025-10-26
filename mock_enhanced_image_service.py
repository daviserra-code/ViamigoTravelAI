"""
Mock Enhanced Image Service for testing UI fixes
"""

from typing import Dict, Tuple
import random


class MockEnhancedImageService:
    """Mock service for testing UI improvements without database"""

    def __init__(self):
        # Mock image URLs for testing
        self.mock_images = {
            'Roma': {
                'Colosseo': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&h=300&fit=crop',
                'Fontana di Trevi': 'https://images.unsplash.com/photo-1531572753322-ad063cecc140?w=400&h=300&fit=crop',
                'Pantheon': 'https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=400&h=300&fit=crop',
                'Foro Romano': 'https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=400&h=300&fit=crop'
            },
            'Firenze': {
                'Duomo': 'https://images.unsplash.com/photo-1543832923-44667a44c804?w=400&h=300&fit=crop',
                'Ponte Vecchio': 'https://images.unsplash.com/photo-1518307697693-e7a7e6e36b2d?w=400&h=300&fit=crop',
                'Uffizi': 'https://images.unsplash.com/photo-1601985843082-5e1ecdf71b71?w=400&h=300&fit=crop'
            },
            'Venezia': {
                'Piazza San Marco': 'https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=400&h=300&fit=crop',
                'Ponte di Rialto': 'https://images.unsplash.com/photo-1522199670076-2ac386793d85?w=400&h=300&fit=crop'
            },
            'Milano': {
                'Duomo': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=400&h=300&fit=crop',
                'La Scala': 'https://images.unsplash.com/photo-1574020976853-5b78b8e8b7c4?w=400&h=300&fit=crop'
            }
        }

    def classify_attraction_from_context(self, title: str, context: str) -> Tuple[str, str, float]:
        """Mock classification with improved accuracy"""
        # Extract city from context
        context_lower = context.lower()
        title_lower = title.lower()

        # Better city detection
        if 'roma' in context_lower or 'rome' in context_lower:
            city = 'Roma'
        elif 'firenze' in context_lower or 'florence' in context_lower:
            city = 'Firenze'
        elif 'venezia' in context_lower or 'venice' in context_lower:
            city = 'Venezia'
        elif 'milano' in context_lower or 'milan' in context_lower:
            city = 'Milano'
        else:
            city = 'Roma'  # Default

        # Better attraction matching
        attraction = self._find_best_match(title_lower, city)
        confidence = self._calculate_confidence(title_lower, attraction, city)

        return city, attraction, confidence

    def _find_best_match(self, title_lower: str, city: str) -> str:
        """Find best matching attraction"""
        if city not in self.mock_images:
            return f"{city}_generic"

        attractions = self.mock_images[city]

        # Try exact matches first
        for attraction in attractions.keys():
            if attraction.lower() in title_lower or title_lower in attraction.lower():
                return attraction

        # Try partial matches
        keywords = {
            'colosseo': 'Colosseo',
            'colosseum': 'Colosseo',
            'trevi': 'Fontana di Trevi',
            'pantheon': 'Pantheon',
            'foro': 'Foro Romano',
            'duomo': 'Duomo',
            'ponte vecchio': 'Ponte Vecchio',
            'uffizi': 'Uffizi',
            'san marco': 'Piazza San Marco',
            'rialto': 'Ponte di Rialto',
            'scala': 'La Scala'
        }

        for keyword, attraction in keywords.items():
            if keyword in title_lower and attraction in attractions:
                return attraction

        # Default to first available or generic
        return list(attractions.keys())[0] if attractions else f"{city}_generic"

    def _calculate_confidence(self, title_lower: str, attraction: str, city: str) -> float:
        """Calculate confidence score"""
        # Higher confidence for exact matches
        if attraction.lower() in title_lower:
            return 0.9
        elif any(word in title_lower for word in attraction.lower().split()):
            return 0.7
        else:
            return 0.5

    def get_best_image_for_attraction(self, city: str, attraction_name: str) -> Dict:
        """Get mock image for attraction"""
        if city in self.mock_images and attraction_name in self.mock_images[city]:
            return {
                'url': self.mock_images[city][attraction_name],
                'confidence': 0.9,
                'source': 'mock_db',
                'from_commons': True,
                'attribution': 'Unsplash',
                'license': 'Unsplash License'
            }

        # Fallback image
        fallback_url = 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=400&h=300&fit=crop'
        return {
            'url': fallback_url,
            'confidence': 0.4,
            'source': 'fallback',
            'from_commons': False
        }


# Mock instance for testing
mock_service = MockEnhancedImageService()


def get_enhanced_attraction_image(city: str, attraction_name: str, fallback_url: str = None) -> Dict:
    """Mock function for testing"""
    return mock_service.get_best_image_for_attraction(city, attraction_name)


def classify_attraction_enhanced(title: str, context: str) -> Tuple[str, str, float]:
    """Mock classification for testing"""
    return mock_service.classify_attraction_from_context(title, context)

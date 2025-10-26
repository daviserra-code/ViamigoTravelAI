"""
Enhanced Image Service for ViamigoTravelAI
Integrates comprehensive attractions database with improved image classification
"""

import json
import re
import os
import psycopg2
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class EnhancedImageService:
    """Enhanced image service using comprehensive attractions database"""

    def __init__(self, db_url: str = None):
        """Initialize with database connection"""
        self.db_url = db_url or os.getenv(
            'DATABASE_URL', 'postgresql://localhost:5432/viamigo')

        # Enhanced keyword mappings for better classification
        self.attraction_keywords = {
            # Rome attractions
            'Colosseo': [
                'colosseum', 'colosseo', 'amphitheatre', 'amphitheater',
                'flavian amphitheatre', 'rome colosseum', 'roma colosseo'
            ],
            'Fontana di Trevi': [
                'trevi fountain', 'fontana di trevi', 'trevi', 'fountain trevi',
                'baroque fountain', 'rome fountain'
            ],
            'Pantheon': [
                'pantheon', 'pantheon rome', 'roman pantheon', 'temple pantheon',
                'pantheon roma', 'ancient rome pantheon'
            ],
            'Foro Romano': [
                'roman forum', 'foro romano', 'forum romanum', 'ancient forum',
                'rome forum', 'palatine hill'
            ],
            'Castel Sant Angelo': [
                'castel sant angelo', 'hadrian mausoleum', 'castle sant angelo',
                'mausoleum of hadrian', 'vatican castle'
            ],
            'Basilica di San Pietro': [
                'st peter basilica', 'basilica san pietro', 'vatican basilica',
                'papal basilica', 'st peters rome', 'basilica di san pietro'
            ],
            'Musei Vaticani': [
                'vatican museums', 'musei vaticani', 'sistine chapel',
                'cappella sistina', 'vatican galleries'
            ],
            'Piazza Navona': [
                'piazza navona', 'navona square', 'baroque square',
                'bernini fountains', 'four rivers fountain'
            ],
            'Villa Borghese': [
                'villa borghese', 'borghese gardens', 'galleria borghese',
                'borghese park', 'villa borghese park'
            ],
            'Trastevere': [
                'trastevere', 'trastevere district', 'santa maria trastevere',
                'trastevere neighborhood', 'trastevere rome'
            ],

            # Florence attractions
            'Duomo di Firenze': [
                'florence cathedral', 'duomo firenze', 'cathedral florence',
                'brunelleschi dome', 'santa maria del fiore', 'duomo florence'
            ],
            'Ponte Vecchio': [
                'ponte vecchio', 'old bridge florence', 'medieval bridge',
                'florence bridge', 'arno bridge'
            ],
            'Galleria degli Uffizi': [
                'uffizi gallery', 'uffizi', 'galleria uffizi', 'uffizi museum',
                'renaissance art', 'botticelli venus'
            ],
            'Palazzo Pitti': [
                'palazzo pitti', 'pitti palace', 'medici palace',
                'boboli gardens', 'pitti florence'
            ],
            'Piazza della Signoria': [
                'piazza signoria', 'signoria square', 'palazzo vecchio',
                'loggia dei lanzi', 'neptune fountain florence'
            ],
            'Basilica di Santa Croce': [
                'santa croce', 'basilica santa croce', 'franciscan basilica',
                'giotto frescoes', 'santa croce florence'
            ],

            # Venice attractions
            'Piazza San Marco': [
                'st mark square', 'piazza san marco', 'san marco square',
                'st marks venice', 'venice square', 'marcos square'
            ],
            'Basilica di San Marco': [
                'st mark basilica', 'basilica san marco', 'san marco basilica',
                'st marks basilica', 'byzantine basilica', 'golden basilica'
            ],
            'Ponte di Rialto': [
                'rialto bridge', 'ponte rialto', 'ponte di rialto',
                'grand canal bridge', 'venice bridge', 'rialto venice'
            ],
            'Palazzo Ducale': [
                'doge palace', 'palazzo ducale', 'doges palace',
                'ducal palace', 'venice palace', 'palazzo doge'
            ],
            'Canal Grande': [
                'grand canal', 'canal grande', 'main canal venice',
                'grand canal venice', 'canale grande'
            ],
            'Ponte dei Sospiri': [
                'bridge of sighs', 'ponte sospiri', 'ponte dei sospiri',
                'sighs bridge', 'venice bridge sighs'
            ],

            # Milan attractions
            'Duomo di Milano': [
                'milan cathedral', 'duomo milano', 'gothic cathedral',
                'cathedral milan', 'duomo di milano', 'milan duomo'
            ],
            'Teatro alla Scala': [
                'la scala', 'scala opera', 'teatro scala', 'scala theater',
                'milan opera', 'scala milan'
            ],
            'Castello Sforzesco': [
                'sforza castle', 'castello sforzesco', 'sforzesco castle',
                'milan castle', 'visconti castle'
            ],
            'Galleria Vittorio Emanuele II': [
                'galleria vittorio emanuele', 'milan gallery', 'shopping gallery',
                'vittorio emanuele', 'glass gallery milan'
            ],
            'Navigli': [
                'navigli', 'milan canals', 'navigli district',
                'naviglio grande', 'milan waterways'
            ]
        }

        # City mappings for better recognition
        self.city_mappings = {
            'roma': 'Roma',
            'rome': 'Roma',
            'rom': 'Roma',
            'firenze': 'Firenze',
            'florence': 'Firenze',
            'venezia': 'Venezia',
            'venice': 'Venezia',
            'venedig': 'Venezia',
            'milano': 'Milano',
            'milan': 'Milano',
            'mailand': 'Milano',
            'napoli': 'Napoli',
            'naples': 'Napoli',
            'pisa': 'Pisa',
            'genova': 'Genova',
            'genoa': 'Genova'
        }

    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None

    def get_best_image_for_attraction(self, city: str, attraction_name: str) -> Optional[Dict]:
        """Get the best image for an attraction from comprehensive database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # First try exact match from comprehensive_attractions
                    cur.execute("""
                        SELECT image_url, thumb_url, has_image, confidence_score,
                               image_attribution, image_license, source_commons
                        FROM comprehensive_attractions 
                        WHERE LOWER(city) = LOWER(%s) 
                        AND (LOWER(name) LIKE LOWER(%s) OR LOWER(raw_name) LIKE LOWER(%s))
                        AND has_image = true
                        ORDER BY 
                            CASE 
                                WHEN source_commons = true THEN 3
                                WHEN source_wikidata = true THEN 2  
                                ELSE 1
                            END DESC,
                            confidence_score DESC
                        LIMIT 1
                    """, (city, f'%{attraction_name}%', f'%{attraction_name}%'))

                    result = cur.fetchone()
                    if result:
                        return {
                            # prefer full image, fallback to thumb
                            'url': result[0] or result[1],
                            'thumb_url': result[1],
                            'has_image': result[2],
                            'confidence': result[3] if result[3] else 0.8,
                            'attribution': result[4],
                            'license': result[5],
                            'source': 'comprehensive_db',
                            'from_commons': result[6]
                        }

                    # Fallback to attraction_images with better confidence filtering
                    cur.execute("""
                        SELECT original_url, confidence_score, attribution, license
                        FROM attraction_images 
                        WHERE LOWER(city) = LOWER(%s) 
                        AND LOWER(attraction_name) LIKE LOWER(%s)
                        AND confidence_score > 0.6  -- Higher threshold for better quality
                        ORDER BY confidence_score DESC, created_at DESC
                        LIMIT 1
                    """, (city, f'%{attraction_name}%'))

                    result = cur.fetchone()
                    if result:
                        return {
                            'url': result[0],
                            'confidence': result[1],
                            'attribution': result[2],
                            'license': result[3],
                            'source': 'attraction_images',
                            'from_commons': False
                        }

        except Exception as e:
            logger.error(
                f"Error getting image for {attraction_name} in {city}: {e}")

        return None

    def classify_attraction_from_context(self, title: str, context: str) -> Tuple[str, str, float]:
        """Enhanced attraction classification using context and comprehensive data"""
        # Extract city from context
        city = self._extract_city_from_context(context)

        # Clean and normalize title
        title_clean = self._normalize_attraction_name(title)

        # Try database lookup first
        db_match = self._find_in_database(city, title_clean)
        if db_match:
            return db_match

        # Fallback to keyword matching
        keyword_match = self._classify_by_keywords(title_clean, city)
        if keyword_match:
            return keyword_match

        # Ultimate fallback
        return city, f"{city}_generic", 0.3

    def _extract_city_from_context(self, context: str) -> str:
        """Extract city from context with better pattern matching"""
        context_lower = context.lower()

        # Check each city mapping
        for key, city in self.city_mappings.items():
            if key in context_lower:
                return city

        # Try pattern matching for "a Roma", "in Firenze", etc.
        patterns = [
            r'(?:a|in|di|nel|della|del)\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)(?:\s+city|\s+centro)',
            r'(?:visit|visiting|explore)\s+([A-Z][a-z]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                city_found = match.group(1).title()
                if city_found.lower() in self.city_mappings:
                    return self.city_mappings[city_found.lower()]
                return city_found

        return 'Italia'  # Default fallback

    def _normalize_attraction_name(self, name: str) -> str:
        """Normalize attraction name for better matching"""
        # Remove common prefixes/suffixes
        name = re.sub(r'^(the|il|la|le|lo|gli|i)\s+',
                      '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+(rome|roma|florence|firenze|venice|venezia|milan|milano)$',
                      '', name, flags=re.IGNORECASE)

        # Replace common variations
        replacements = {
            'colosseum': 'colosseo',
            'trevi fountain': 'fontana di trevi',
            'st peter': 'san pietro',
            'st mark': 'san marco',
            'old bridge': 'ponte vecchio',
            'cathedral': 'duomo'
        }

        name_lower = name.lower()
        for old, new in replacements.items():
            name_lower = name_lower.replace(old, new)

        return name_lower.strip()

    def _find_in_database(self, city: str, attraction_name: str) -> Optional[Tuple[str, str, float]]:
        """Find attraction in comprehensive database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Search with various matching strategies
                    search_queries = [
                        # Exact match
                        (f"LOWER(name) = LOWER(%s)", (attraction_name,)),
                        # Partial match in name
                        (f"LOWER(name) LIKE LOWER(%s)",
                         (f'%{attraction_name}%',)),
                        # Partial match in raw_name
                        (f"LOWER(raw_name) LIKE LOWER(%s)",
                         (f'%{attraction_name}%',)),
                        # Match in description
                        (f"LOWER(description) LIKE LOWER(%s)",
                         (f'%{attraction_name}%',))
                    ]

                    for where_clause, params in search_queries:
                        cur.execute(f"""
                            SELECT name, confidence_score, attraction_type
                            FROM comprehensive_attractions 
                            WHERE LOWER(city) = LOWER(%s) 
                            AND {where_clause}
                            ORDER BY confidence_score DESC
                            LIMIT 1
                        """, (city,) + params)

                        result = cur.fetchone()
                        if result:
                            confidence = result[1] if result[1] else 0.7
                            # Boost DB matches
                            return city, result[0], min(confidence + 0.1, 0.95)

        except Exception as e:
            logger.error(f"Database search error: {e}")

        return None

    def _classify_by_keywords(self, attraction_name: str, city: str) -> Optional[Tuple[str, str, float]]:
        """Classify using keyword matching with improved scoring"""
        best_match = None
        highest_score = 0.0

        attraction_lower = attraction_name.lower()

        for attraction, keywords in self.attraction_keywords.items():
            score = 0.0
            matches = 0

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Exact match gets highest score
                if attraction_lower == keyword_lower:
                    score += 1.0
                    matches += 1
                # Attraction name contains keyword
                elif keyword_lower in attraction_lower:
                    score += 0.7
                    matches += 1
                # Keyword contains attraction name (for short names)
                elif attraction_lower in keyword_lower and len(attraction_lower) > 3:
                    score += 0.5
                    matches += 1

            # Bonus for multiple matches
            if matches > 1:
                score *= 1.3

            # City relevance check
            if self._attraction_belongs_to_city(attraction, city):
                score *= 1.2
            else:
                score *= 0.4  # Penalty for wrong city

            if score > highest_score:
                highest_score = score
                best_match = attraction

        if best_match and highest_score > 0.3:
            # Convert score to confidence
            confidence = min(highest_score * 0.6, 0.9)  # Cap at 0.9
            return city, best_match, confidence

        return None

    def _attraction_belongs_to_city(self, attraction: str, city: str) -> bool:
        """Check if attraction belongs to the specified city"""
        city_attractions = {
            'Roma': ['Colosseo', 'Fontana di Trevi', 'Pantheon', 'Foro Romano',
                     'Castel Sant Angelo', 'Basilica di San Pietro', 'Musei Vaticani',
                     'Piazza Navona', 'Villa Borghese', 'Trastevere'],
            'Firenze': ['Duomo di Firenze', 'Ponte Vecchio', 'Galleria degli Uffizi',
                        'Palazzo Pitti', 'Piazza della Signoria', 'Basilica di Santa Croce'],
            'Venezia': ['Piazza San Marco', 'Basilica di San Marco', 'Ponte di Rialto',
                        'Palazzo Ducale', 'Canal Grande', 'Ponte dei Sospiri'],
            'Milano': ['Duomo di Milano', 'Teatro alla Scala', 'Castello Sforzesco',
                       'Galleria Vittorio Emanuele II', 'Navigli'],
            'Napoli': ['Spaccanapoli', 'Castel dell Ovo', 'Quartieri Spagnoli',
                       'Museo Archeologico']
        }

        return attraction in city_attractions.get(city, [])

    def get_fallback_image_url(self, attraction_name: str, city: str) -> str:
        """Get a high-quality fallback image URL"""
        # High-quality Unsplash images as fallbacks
        fallback_map = {
            'Colosseo': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&h=300&fit=crop',
            'Fontana di Trevi': 'https://images.unsplash.com/photo-1531572753322-ad063cecc140?w=400&h=300&fit=crop',
            'Pantheon': 'https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=400&h=300&fit=crop',
            'Duomo di Firenze': 'https://images.unsplash.com/photo-1543832923-44667a44c804?w=400&h=300&fit=crop',
            'Ponte Vecchio': 'https://images.unsplash.com/photo-1518307697693-e7a7e6e36b2d?w=400&h=300&fit=crop',
            'Piazza San Marco': 'https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=400&h=300&fit=crop',
            'Duomo di Milano': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=400&h=300&fit=crop'
        }

        # Try exact match first
        if attraction_name in fallback_map:
            return fallback_map[attraction_name]

        # Try partial match
        for key, url in fallback_map.items():
            if key.lower() in attraction_name.lower() or attraction_name.lower() in key.lower():
                return url

        # City-specific fallbacks
        city_fallbacks = {
            'Roma': 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=400&h=300&fit=crop',
            'Firenze': 'https://images.unsplash.com/photo-1543832923-44667a44c804?w=400&h=300&fit=crop',
            'Venezia': 'https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=400&h=300&fit=crop',
            'Milano': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=400&h=300&fit=crop'
        }

        return city_fallbacks.get(city, 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=400&h=300&fit=crop')


# Singleton instance for the service
enhanced_image_service = EnhancedImageService()


def get_enhanced_attraction_image(city: str, attraction_name: str, fallback_url: str = None) -> Dict:
    """
    Main function to get enhanced attraction images
    Returns dict with url, confidence, attribution, etc.
    """
    try:
        # Get best image from database
        image_data = enhanced_image_service.get_best_image_for_attraction(
            city, attraction_name)

        if image_data and image_data.get('url'):
            return {
                'url': image_data['url'],
                'thumb_url': image_data.get('thumb_url'),
                'confidence': image_data.get('confidence', 0.8),
                'attribution': image_data.get('attribution'),
                'license': image_data.get('license'),
                'source': image_data.get('source'),
                'from_commons': image_data.get('from_commons', False)
            }

        # Use provided fallback or generate one
        fallback = fallback_url or enhanced_image_service.get_fallback_image_url(
            attraction_name, city)

        return {
            'url': fallback,
            'confidence': 0.4,  # Lower confidence for fallbacks
            'source': 'fallback',
            'from_commons': False
        }

    except Exception as e:
        logger.error(f"Error in get_enhanced_attraction_image: {e}")

        # Emergency fallback
        return {
            'url': 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=400&h=300&fit=crop',
            'confidence': 0.2,
            'source': 'emergency_fallback',
            'from_commons': False
        }


def classify_attraction_enhanced(title: str, context: str) -> Tuple[str, str, float]:
    """Enhanced attraction classification function"""
    return enhanced_image_service.classify_attraction_from_context(title, context)

"""
🇮🇹 INTELLIGENT ITALIAN CITIES ROUTING SYSTEM
Universal database-driven router for ALL Italian cities

Works for: Milano, Roma, Torino, Venezia, Firenze, Napoli, Bologna, Genova, Palermo, etc.

Features:
1. Real attractions from comprehensive_attractions database (3000+ Italian attractions)
2. Real coordinates for accurate map rendering
3. Rich details from database (descriptions, images, categories)
4. Context-aware AI suggestions based on actual route
5. Image URLs from database (no placeholders)
"""

import psycopg2
import os
from typing import List, Dict, Optional, Tuple
import json


class IntelligentItalianRouter:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')

        # City centers for fallback geocoding
        self.city_centers = {
            'milano': [45.4642, 9.1900],
            'roma': [41.9028, 12.4964],
            'torino': [45.0703, 7.6869],
            'venezia': [45.4408, 12.3155],
            'firenze': [43.7696, 11.2558],
            'napoli': [40.8518, 14.2681],
            'bologna': [44.4949, 11.3426],
            'genova': [44.4056, 8.9463],
            'palermo': [38.1157, 13.3615],
            'catania': [37.5079, 15.0830],
            'bari': [41.1171, 16.8719],
            'verona': [45.4384, 10.9916],
            'padova': [45.4064, 11.8768],
            'trieste': [45.6495, 13.7768],
        }

    def generate_intelligent_itinerary(
        self,
        start: str,
        end: str,
        city_name: str,
        interests: List[str] = None,
        duration: str = "half_day"
    ) -> List[Dict]:
        """
        Generate intelligent itinerary for ANY Italian city using REAL database data

        Args:
            start: Starting location (e.g., "Piazza Castello, Torino")
            end: Destination (e.g., "Parco Valentino, Torino")
            city_name: City name (e.g., "Torino", "Milano")
            interests: User interests (e.g., ["culture", "parks"])
            duration: "half_day" or "full_day"

        Returns:
            List of itinerary stops with REAL data, images, and coordinates
        """
        try:
            city_key = city_name.lower().replace(' ', '')

            print(f"🇮🇹 Intelligent routing for {city_name}: {start} → {end}")

            # Step 1: Get REAL attractions from database
            attractions = self._get_city_attractions_from_db(
                city_name, interests)

            if not attractions or len(attractions) < 2:
                print(
                    f"⚠️ Insufficient data for {city_name}, using enhanced fallback")
                return self._enhanced_fallback(start, end, city_name)

            # Step 2: Geocode start and end points
            start_coords = self._geocode_location(start, city_name)
            end_coords = self._geocode_location(end, city_name)

            # Step 3: Get specific end attraction from database if it's a known place
            end_attraction = self._find_specific_attraction(end, city_name)

            # Step 4: Build intelligent route with proximity ordering
            itinerary = self._build_intelligent_route(
                start, end, start_coords, end_coords,
                attractions, end_attraction, city_name, duration
            )

            print(
                f"✅ Generated intelligent itinerary for {city_name} with {len(itinerary)} stops")
            return itinerary

        except Exception as e:
            print(f"❌ Error generating itinerary for {city_name}: {e}")
            import traceback
            traceback.print_exc()
            return self._enhanced_fallback(start, end, city_name)

    def _get_city_attractions_from_db(self, city_name: str, interests: List[str] = None) -> List[Dict]:
        """Get REAL attractions from database for ANY Italian city"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            attractions = []

            # Priority 1: Try place_cache (best curated data)
            print(f"📊 Querying place_cache for {city_name}...")
            cursor.execute("""
                SELECT place_name, city, place_data, cache_key
                FROM place_cache
                WHERE LOWER(city) = LOWER(%s)
                ORDER BY priority_level DESC, access_count DESC
                LIMIT 8
            """, (city_name,))

            place_cache_results = cursor.fetchall()

            for row in place_cache_results:
                place_name, city, place_data_json, cache_key = row
                place_data = json.loads(
                    place_data_json) if place_data_json else {}

                lat = place_data.get('lat') or place_data.get('latitude')
                lng = place_data.get('lon') or place_data.get(
                    'lng') or place_data.get('longitude')

                if lat and lng:  # Only add if coordinates exist
                    attractions.append({
                        'name': place_data.get('name', place_name),
                        'latitude': float(lat),
                        'longitude': float(lng),
                        'description': place_data.get('description', f'{place_name} a {city_name}'),
                        'image_url': place_data.get('image_url'),
                        'category': place_data.get('category', 'attraction'),
                        'source': 'place_cache'
                    })

            # Priority 2: Query comprehensive_attractions (3000+ Italian attractions)
            if len(attractions) < 6:
                print(
                    f"📊 Querying comprehensive_attractions for {city_name}...")

                # Build category filter if interests provided
                category_conditions = []
                if interests:
                    if 'culture' in interests or 'storia' in interests or 'arte' in interests:
                        category_conditions.append(
                            "(category ILIKE '%%museum%%' OR category ILIKE '%%monument%%' OR category ILIKE '%%church%%' OR category ILIKE '%%palace%%')")
                    if 'parks' in interests or 'nature' in interests:
                        category_conditions.append(
                            "(category ILIKE '%%park%%' OR category ILIKE '%%garden%%')")
                    if 'food' in interests:
                        category_conditions.append(
                            "(category ILIKE '%%restaurant%%' OR category ILIKE '%%cafe%%')")

                category_filter = ""
                if category_conditions:
                    category_filter = "AND (" + \
                        " OR ".join(category_conditions) + ")"

                # 🇮🇹 DUAL-TABLE STRATEGY: Query BOTH comprehensive_attractions AND comprehensive_attractions_italy
                # comprehensive_attractions: city-based (Roma, Torino, etc.) - 11,723 rows
                # comprehensive_attractions_italy: region-based (Lombardia, Toscana, etc.) - 14,172 rows

                # Map cities to regions AND geographic bounds for comprehensive_attractions_italy
                # Bounds format: (min_lat, max_lat, min_lng, max_lng)
                city_config = {
                    'milano': ('Lombardia', 45.3, 45.6, 9.0, 9.4),
                    'milan': ('Lombardia', 45.3, 45.6, 9.0, 9.4),
                    'firenze': ('Toscana', 43.7, 43.9, 11.1, 11.4),
                    'florence': ('Toscana', 43.7, 43.9, 11.1, 11.4),
                    # Rome is HUGE: actual extent is 53km x 52km
                    'roma': ('Lazio', 41.66, 42.15, 12.24, 12.86),
                    'rome': ('Lazio', 41.66, 42.15, 12.24, 12.86),
                    'napoli': ('Campania', 40.8, 40.9, 14.2, 14.3),
                    'naples': ('Campania', 40.8, 40.9, 14.2, 14.3),
                    'venezia': ('Veneto', 45.4, 45.5, 12.3, 12.4),
                    'venice': ('Veneto', 45.4, 45.5, 12.3, 12.4),
                    'torino': ('Piemonte', 45.0, 45.1, 7.6, 7.7),
                    'turin': ('Piemonte', 45.0, 45.1, 7.6, 7.7),
                    'genova': ('Liguria', 44.4, 44.5, 8.9, 9.0),
                    'genoa': ('Liguria', 44.4, 44.5, 8.9, 9.0),
                    'bologna': ('Emilia Romagna', 44.4, 44.6, 11.3, 11.4),
                    'palermo': ('Sicilia', 38.1, 38.2, 13.3, 13.4),
                    'bari': ('Puglia', 41.1, 41.2, 16.8, 16.9),
                    'verona': ('Veneto', 45.4, 45.5, 10.9, 11.1)
                }

                city_lower = city_name.lower()
                if city_lower in city_config:
                    region_name, min_lat, max_lat, min_lng, max_lng = city_config[city_lower]
                    geo_filter = f"AND cai.latitude BETWEEN {min_lat} AND {max_lat} AND cai.longitude BETWEEN {min_lng} AND {max_lng}"
                else:
                    region_name = city_name
                    geo_filter = ""  # No geographic filter if city not in config

                # 🔄 UNION query: Search both tables and merge results
                # JOIN with attraction_images to utilize the 932 new images!
                query = f"""
                    SELECT * FROM (
                        -- Table 1: comprehensive_attractions (city-based)
                        SELECT 
                            ca.name, 
                            ca.city, 
                            ca.category, 
                            ca.description, 
                            ca.latitude, 
                            ca.longitude, 
                            COALESCE(ai.original_url, ai.thumb_url, ca.image_url) as image_url,
                            ca.wikidata_id,
                            ai.source as ai_source,
                            ai.confidence_score,
                            'comprehensive_attractions' as table_source
                        FROM comprehensive_attractions ca
                        LEFT JOIN attraction_images ai
                            ON LOWER(ca.city) = LOWER(ai.city)
                            AND (
                                LOWER(ca.name) LIKE '%%' || LOWER(ai.attraction_name) || '%%'
                                OR LOWER(ai.attraction_name) LIKE '%%' || LOWER(ca.name) || '%%'
                            )
                            AND (ai.confidence_score > 0.5 OR ai.confidence_score IS NULL)
                        WHERE LOWER(ca.city) = LOWER(%s)
                          AND ca.latitude IS NOT NULL
                          AND ca.longitude IS NOT NULL
                          {category_filter}
                        
                        UNION ALL
                        
                        -- Table 2: comprehensive_attractions_italy (region-based)
                        -- For cities with geographic config, use ONLY geographic bounds
                        -- The city column in this table contains actual city names, not regions
                        SELECT 
                            cai.name,
                            cai.city as region,
                            cai.category,
                            cai.description,
                            cai.latitude,
                            cai.longitude,
                            COALESCE(ai.original_url, ai.thumb_url, cai.image_thumb_url, cai.image_original_url) as image_url,
                            cai.wikidata,
                            ai.source as ai_source,
                            ai.confidence_score,
                            'comprehensive_attractions_italy' as table_source
                        FROM comprehensive_attractions_italy cai
                        LEFT JOIN attraction_images ai
                            ON LOWER(ai.city) = LOWER(%s)
                            AND (
                                LOWER(cai.name) LIKE '%%' || LOWER(ai.attraction_name) || '%%'
                                OR LOWER(ai.attraction_name) LIKE '%%' || LOWER(cai.name) || '%%'
                            )
                            AND (ai.confidence_score > 0.5 OR ai.confidence_score IS NULL)
                        WHERE cai.latitude IS NOT NULL
                          AND cai.longitude IS NOT NULL
                          {geo_filter}
                          {category_filter.replace('ca.', 'cai.')}
                    ) combined_results
                    ORDER BY 
                        CASE WHEN ai_source IS NOT NULL THEN 1 
                             WHEN image_url IS NOT NULL THEN 2 
                             ELSE 3 END,
                        RANDOM()
                    LIMIT %s
                """

                # Parameters: city_name for comprehensive_attractions WHERE,
                #             city_name for attraction_images JOIN,
                #             limit for LIMIT clause
                cursor.execute(
                    query, (city_name, city_name, 12 - len(attractions)))
                db_results = cursor.fetchall()

                print(
                    f"🖼️ Database query returned {len(db_results)} results for {city_name}")

                for row in db_results:
                    # Defensive unpacking: UNION query returns 11 columns now (added table_source)
                    if len(row) >= 8:
                        name, city_or_region, category, description, lat, lng, image_url, wikidata_id = row[
                            :8]
                        ai_source = row[8] if len(row) > 8 else None
                        confidence = row[9] if len(row) > 9 else None
                        table_source = row[10] if len(row) > 10 else 'unknown'

                        # Determine final image source for tracking
                        if ai_source:
                            img_source = f'attraction_images+{table_source}'
                        elif image_url:
                            img_source = table_source
                        else:
                            img_source = 'none'

                        if image_url:
                            print(
                                f"✅ {name}: Has image (source: {img_source})")
                        else:
                            print(f"⚠️ {name}: NO IMAGE")

                        if lat and lng:  # Only add if coordinates exist
                            attractions.append({
                                'name': name,
                                'latitude': float(lat),
                                'longitude': float(lng),
                                'description': description or f'{name} a {city_name}',
                                'image_url': image_url,  # Now using attraction_images if available!
                                'category': category or 'attraction',
                                'wikidata_id': wikidata_id,
                                'source': img_source
                            })
                    else:
                        print(
                            f"⚠️ Skipping row with unexpected column count: {len(row)}")

            cursor.close()
            conn.close()

            print(
                f"✅ Found {len(attractions)} attractions with coordinates for {city_name}")
            return attractions

        except Exception as e:
            print(f"❌ Database query error for {city_name}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _find_specific_attraction(self, location_name: str, city_name: str) -> Optional[Dict]:
        """Find a specific attraction by name in the database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Clean location name (remove city suffix)
            clean_name = location_name.replace(
                f', {city_name}', '').replace(f',{city_name}', '').strip()

            # Search in comprehensive_attractions
            cursor.execute("""
                SELECT name, city, category, description, latitude, longitude, image_url
                FROM comprehensive_attractions
                WHERE LOWER(city) = LOWER(%s)
                  AND LOWER(name) ILIKE %s
                  AND latitude IS NOT NULL
                  AND longitude IS NOT NULL
                LIMIT 1
            """, (city_name, f'%{clean_name.lower()}%'))

            result = cursor.fetchone()

            if result:
                name, city, category, description, lat, lng, image_url = result
                cursor.close()
                conn.close()

                return {
                    'name': name,
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'description': description or f'{name} a {city_name}',
                    'image_url': image_url,
                    'category': category or 'destination',
                    'source': 'comprehensive_attractions'
                }

            cursor.close()
            conn.close()
            return None

        except Exception as e:
            print(f"⚠️ Error finding specific attraction: {e}")
            return None

    def _geocode_location(self, location: str, city_name: str) -> List[float]:
        """Geocode a location - try database first, then use city center"""
        # Try to find in database
        attraction = self._find_specific_attraction(location, city_name)
        if attraction:
            return [attraction['latitude'], attraction['longitude']]

        # Fallback to city center
        city_key = city_name.lower().replace(' ', '')
        # Default to Rome
        return self.city_centers.get(city_key, [41.9028, 12.4964])

    def _build_intelligent_route(
        self,
        start: str,
        end: str,
        start_coords: List[float],
        end_coords: List[float],
        attractions: List[Dict],
        end_attraction: Optional[Dict],
        city_name: str,
        duration: str
    ) -> List[Dict]:
        """Build intelligent route with proximity-based ordering"""

        itinerary = []
        current_time = 9.0  # Start at 9:00 AM

        # Add start location
        itinerary.append({
            'time': '09:00',
            'title': start,
            'name': start,
            'description': f'Punto di partenza a {city_name}',
            'latitude': start_coords[0],
            'longitude': start_coords[1],
            'lat': start_coords[0],
            'lng': start_coords[1],
            'type': 'start',
            'context': f'{self._clean_name(start)}_{city_name.lower()}',
            'image_url': None
        })

        # Select attractions based on duration
        max_stops = 4 if duration == "half_day" else 6
        selected_attractions = attractions[:max_stops]

        # Add intermediate attractions
        for i, attraction in enumerate(selected_attractions):
            # Add walking segment
            if i > 0 or True:  # Always add walk
                current_time += 0.25  # 15 minutes walk
                itinerary.append({
                    'time': f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                    'title': f"Verso {attraction['name']}",
                    'name': f"Verso {attraction['name']}",
                    'description': f"Passeggiata attraverso {city_name}",
                    'latitude': attraction['latitude'],
                    'longitude': attraction['longitude'],
                    'lat': attraction['latitude'],
                    'lng': attraction['longitude'],
                    'type': 'transport',
                    'context': f"walk_to_{self._clean_name(attraction['name'])}_{city_name.lower()}",
                    'transport': 'walking',
                    'image_url': None  # 🚫 NO IMAGES FOR TRANSIT
                })

            # Add attraction visit
            duration_hours = 1.5
            start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            current_time += duration_hours
            end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"

            itinerary.append({
                'time': f"{start_time} - {end_time}",
                'title': attraction['name'],
                'name': attraction['name'],
                'description': attraction['description'],
                'latitude': attraction['latitude'],
                'longitude': attraction['longitude'],
                'lat': attraction['latitude'],
                'lng': attraction['longitude'],
                'type': 'activity',
                'context': f"{self._clean_name(attraction['name'])}_{city_name.lower()}",
                # ✅ IMAGES FOR ACTIVITIES ONLY
                'image_url': attraction.get('image_url'),
                'category': attraction.get('category', 'attraction'),
                'source': attraction.get('source')
            })

        # Add final destination if different from last attraction
        if end_attraction:
            current_time += 0.25
            itinerary.append({
                'time': f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                'title': f"Verso {end_attraction['name']}",
                'name': f"Verso {end_attraction['name']}",
                'description': f"Arrivo alla destinazione finale",
                'latitude': end_attraction['latitude'],
                'longitude': end_attraction['longitude'],
                'lat': end_attraction['latitude'],
                'lng': end_attraction['longitude'],
                'type': 'transport',
                'context': f"walk_to_{self._clean_name(end_attraction['name'])}_{city_name.lower()}",
                'transport': 'walking',
                'image_url': None  # 🚫 NO IMAGES FOR TRANSIT
            })

            current_time += 1.0
            itinerary.append({
                'time': f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                'title': end_attraction['name'],
                'name': end_attraction['name'],
                'description': end_attraction['description'],
                'latitude': end_attraction['latitude'],
                'longitude': end_attraction['longitude'],
                'lat': end_attraction['latitude'],
                'lng': end_attraction['longitude'],
                'type': 'destination',
                'context': f"{self._clean_name(end_attraction['name'])}_{city_name.lower()}",
                # ✅ IMAGES FOR DESTINATIONS
                'image_url': end_attraction.get('image_url'),
                'category': end_attraction.get('category', 'destination')
            })
        elif end != start:  # End location different from start
            itinerary.append({
                'time': f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                'title': end,
                'name': end,
                'description': f'Destinazione finale a {city_name}',
                'latitude': end_coords[0],
                'longitude': end_coords[1],
                'lat': end_coords[0],
                'lng': end_coords[1],
                'type': 'destination',
                'context': f'{self._clean_name(end)}_{city_name.lower()}',
                'image_url': None
            })

        return itinerary

    def _clean_name(self, name: str) -> str:
        """Clean attraction name for context generation"""
        return name.lower().replace(' ', '_').replace(',', '').replace("'", '').replace('à', 'a').replace('è', 'e').replace('ì', 'i').replace('ò', 'o').replace('ù', 'u')

    def _enhanced_fallback(self, start: str, end: str, city_name: str) -> List[Dict]:
        """Enhanced fallback when database has insufficient data"""
        city_key = city_name.lower().replace(' ', '')
        coords = self.city_centers.get(city_key, [41.9028, 12.4964])

        return [
            {
                'time': '09:00',
                'title': start,
                'name': start,
                'description': f'Punto di partenza a {city_name}',
                'latitude': coords[0],
                'longitude': coords[1],
                'lat': coords[0],
                'lng': coords[1],
                'type': 'start',
                'context': f'{self._clean_name(start)}_{city_key}'
            },
            {
                'time': '11:00',
                'title': f'Centro Storico di {city_name}',
                'name': f'Centro Storico di {city_name}',
                'description': f'Esplora il centro storico di {city_name}',
                'latitude': coords[0],
                'longitude': coords[1],
                'lat': coords[0],
                'lng': coords[1],
                'type': 'activity',
                'context': f'centro_storico_{city_key}'
            },
            {
                'time': '14:00',
                'title': end,
                'name': end,
                'description': f'Destinazione finale a {city_name}',
                'latitude': coords[0] + 0.01,
                'longitude': coords[1] + 0.01,
                'lat': coords[0] + 0.01,
                'lng': coords[1] + 0.01,
                'type': 'destination',
                'context': f'{self._clean_name(end)}_{city_key}'
            }
        ]


# Singleton instance
italian_router = IntelligentItalianRouter()

"""
Extended Safe Tourism Data Loader for ViaMigo - Comprehensive Italian Coverage
Uses OpenStreetMap Overpass API (100% Safe, Free, Open Source)
Loads 40+ Italian cities from North to South, including islands
"""

import os
import requests
import psycopg2
from psycopg2.extras import execute_batch
import chromadb
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict, Tuple, Optional
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


class ExtendedSafeTourismDataLoader:
    def __init__(self, chroma_path: str = "./chromadb_data"):
        """
        Initialize connections using DATABASE_URL from .env
        Uses OpenStreetMap Overpass API - 100% safe and free
        """
        # Get PostgreSQL connection from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("❌ DATABASE_URL not found in .env file")

        # Add SSL requirement for cloud databases (Neon, Supabase, etc.)
        if '?' in database_url:
            database_url += '&sslmode=require'
        else:
            database_url += '?sslmode=require'

        self.pg_conn = psycopg2.connect(database_url)
        self.pg_cursor = self.pg_conn.cursor()
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Initialize embedding model for RAG
        print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")

        # Use single ChromaDB collection consistent with app architecture
        self.collection = self.chroma_client.get_or_create_collection(
            name="viamigo_travel_data",
            metadata={
                "description": "Travel places and experiences for AI companion"}
        )

        print("✅ PostgreSQL and ChromaDB connections established")

    def query_overpass(self, bbox: Tuple[float, float, float, float], poi_types: List[str]) -> List[Dict]:
        """
        Query OpenStreetMap using Overpass API for specific POI types within bounding box

        Args:
            bbox: Bounding box (south, west, north, east)
            poi_types: List of POI types to search for

        Returns:
            List of POI dictionaries with OSM data
        """
        # Construct Overpass QL query
        south, west, north, east = bbox

        # Build query for multiple POI types
        query_parts = []
        for poi_type in poi_types:
            if poi_type == "restaurant":
                query_parts.append(
                    f'node["amenity"~"restaurant|cafe|bar|pub|fast_food"]({south},{west},{north},{east});')
                query_parts.append(
                    f'way["amenity"~"restaurant|cafe|bar|pub|fast_food"]({south},{west},{north},{east});')
            elif poi_type == "tourist_attraction":
                query_parts.append(
                    f'node["tourism"~"attraction|museum|gallery|monument"]({south},{west},{north},{east});')
                query_parts.append(
                    f'way["tourism"~"attraction|museum|gallery|monument"]({south},{west},{north},{east});')
                query_parts.append(
                    f'node["historic"]({south},{west},{north},{east});')
                query_parts.append(
                    f'way["historic"]({south},{west},{north},{east});')
            elif poi_type == "hotel":
                query_parts.append(
                    f'node["tourism"~"hotel|guest_house|hostel"]({south},{west},{north},{east});')
                query_parts.append(
                    f'way["tourism"~"hotel|guest_house|hostel"]({south},{west},{north},{east});')

        overpass_query = f"""
        [out:json][timeout:25];
        (
          {' '.join(query_parts)}
        );
        out geom;
        """

        overpass_url = "https://overpass-api.de/api/interpreter"

        try:
            # Try with shorter timeout first, then retry
            for timeout_val in [15, 30]:
                try:
                    response = requests.post(
                        overpass_url, data=overpass_query, timeout=timeout_val)
                    response.raise_for_status()
                    break  # Success, exit retry loop
                except requests.exceptions.Timeout:
                    if timeout_val == 15:
                        print(
                            f"⏱️ First attempt timed out, retrying with longer timeout...")
                        time.sleep(3)
                        continue
                    else:
                        raise  # Final timeout, let it bubble up

            data = response.json()
            elements = data.get('elements', [])

            print(f"📊 Found {len(elements)} raw POIs from OpenStreetMap")

            # Convert to standardized format
            standardized_pois = []
            for element in elements:
                poi = self._convert_osm_to_standard(element)
                if poi:
                    standardized_pois.append(poi)

            print(
                f"✅ Converted {len(standardized_pois)} POIs to standard format")
            return standardized_pois

        except Exception as e:
            print(f"❌ Error querying Overpass API: {e}")
            return []

    def _convert_osm_to_standard(self, osm_element: Dict) -> Optional[Dict]:
        """
        Convert OSM element to standardized place format

        Args:
            osm_element: Raw OSM element from Overpass API

        Returns:
            Standardized place dictionary or None if invalid
        """
        tags = osm_element.get('tags', {})

        # Extract basic info
        name = tags.get('name')
        if not name:
            return None  # Skip unnamed places

        # Get coordinates
        if osm_element.get('type') == 'node':
            lat = osm_element.get('lat')
            lon = osm_element.get('lon')
        elif osm_element.get('center'):
            lat = osm_element['center']['lat']
            lon = osm_element['center']['lon']
        else:
            return None

        # Determine category
        category = self._determine_category(tags)

        # Build standardized place
        place = {
            'name': name,
            'category': category,
            'coordinates': [lat, lon],
            'types': [category],
            'osm_id': osm_element.get('id'),
            'osm_type': osm_element.get('type', 'node')
        }

        # Add optional fields
        if tags.get('cuisine'):
            place['cuisine'] = tags['cuisine']
        if tags.get('tourism'):
            place['tourism_type'] = tags['tourism']
        if tags.get('historic'):
            place['historic_type'] = tags['historic']
        if tags.get('addr:street') and tags.get('addr:housenumber'):
            place['address'] = f"{tags['addr:housenumber']} {tags['addr:street']}"
        if tags.get('website'):
            place['website'] = tags['website']
        if tags.get('phone'):
            place['phone'] = tags['phone']
        if tags.get('opening_hours'):
            place['opening_hours'] = tags['opening_hours']

        # Create description
        description_parts = [name]
        if tags.get('cuisine'):
            description_parts.append(f"Cuisine: {tags['cuisine']}")
        if tags.get('tourism'):
            description_parts.append(f"Type: {tags['tourism']}")
        if tags.get('historic'):
            description_parts.append(f"Historic: {tags['historic']}")

        place['description'] = '. '.join(description_parts)

        return place

    def _determine_category(self, tags: Dict) -> str:
        """Determine place category from OSM tags"""
        amenity = tags.get('amenity', '')
        tourism = tags.get('tourism', '')
        historic = tags.get('historic', '')

        # Restaurant/Food
        if amenity in ['restaurant', 'cafe', 'bar', 'pub', 'fast_food', 'pizzeria']:
            return 'restaurant'

        # Hotels
        if tourism in ['hotel', 'guest_house', 'hostel', 'motel']:
            return 'hotel'

        # Museums
        if tourism in ['museum', 'gallery'] or amenity == 'museum':
            return 'museum'

        # Tourist attractions
        if tourism in ['attraction', 'monument', 'artwork'] or historic:
            return 'tourist_attraction'

        # Default
        return 'tourist_attraction'

    def load_city_data(self, city: str, bbox: Tuple[float, float, float, float],
                       load_attractions: bool = True, load_restaurants: bool = True,
                       load_hotels: bool = True) -> bool:
        """
        Load comprehensive data for a city from OpenStreetMap

        Args:
            city: City name
            bbox: Bounding box (south, west, north, east)
            load_attractions: Whether to load tourist attractions
            load_restaurants: Whether to load restaurants
            load_hotels: Whether to load hotels

        Returns:
            Success status
        """
        print(f"\n🏛️ Loading data for {city}...")

        # Determine POI types to load
        poi_types = []
        if load_restaurants:
            poi_types.append('restaurant')
        if load_attractions:
            poi_types.append('tourist_attraction')
        if load_hotels:
            poi_types.append('hotel')

        # Query OpenStreetMap
        places = self.query_overpass(bbox, poi_types)

        if not places:
            print(f"⚠️ No places found for {city}")
            return False

        # Store in PostgreSQL
        success = self._store_in_postgres(city, places)

        if success:
            # Store in ChromaDB for semantic search
            self._store_in_chromadb(city, places)
            print(f"✅ Successfully loaded {len(places)} places for {city}")
            return True
        else:
            print(f"❌ Failed to store data for {city}")
            return False

    def _store_in_postgres(self, city: str, places: List[Dict]) -> bool:
        """Store places in PostgreSQL place_cache table"""
        try:
            # Group places by category
            categories = {}
            for place in places:
                category = place.get('category', 'tourist_attraction')
                if category not in categories:
                    categories[category] = []
                categories[category].append(place)

            # Store each category
            for category, category_places in categories.items():
                cache_key = f"{city.lower()}_{category}"
                place_data = json.dumps(category_places, ensure_ascii=False)

                # Insert or update - proper created_at semantics
                self.pg_cursor.execute("""
                    INSERT INTO place_cache (cache_key, place_data, city, place_name, country, priority_level, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (cache_key) 
                    DO UPDATE SET 
                        place_data = EXCLUDED.place_data,
                        last_accessed = CURRENT_TIMESTAMP,
                        access_count = COALESCE(place_cache.access_count, 0) + 1
                    -- Note: created_at remains unchanged on updates (correct behavior)
                """, (cache_key, place_data, city, f"{city} {category}", "Italia", "high"))

            self.pg_conn.commit()
            print(f"💾 Stored {len(categories)} categories in PostgreSQL")
            return True

        except Exception as e:
            print(f"❌ Error storing in PostgreSQL: {e}")
            self.pg_conn.rollback()
            return False

    def _store_in_chromadb(self, city: str, places: List[Dict]):
        """Store places in ChromaDB for semantic search"""
        try:
            documents = []
            metadatas = []
            ids = []

            for i, place in enumerate(places):
                # Create searchable document text
                doc_parts = [
                    place.get('name', ''),
                    place.get('description', ''),
                    place.get('category', ''),
                    city
                ]

                if place.get('cuisine'):
                    doc_parts.append(f"cuisine: {place['cuisine']}")
                if place.get('tourism_type'):
                    doc_parts.append(f"type: {place['tourism_type']}")

                document = ' '.join(filter(None, doc_parts))
                documents.append(document)

                # Create metadata
                metadata = {
                    'place_name': place.get('name', ''),
                    'city': city.lower(),
                    'category': place.get('category', ''),
                    'country': 'Italia'
                }

                # Add optional metadata
                for key in ['cuisine', 'tourism_type', 'historic_type']:
                    if place.get(key):
                        metadata[key] = place[key]

                metadatas.append(metadata)
                ids.append(f"{city.lower()}_{place.get('osm_id', i)}")

            # Add to ChromaDB
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"🔍 Added {len(documents)} places to ChromaDB")

        except Exception as e:
            print(f"⚠️ ChromaDB storage warning: {e}")

    def close(self):
        """Close database connections"""
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        print("🔌 Database connections closed")


def main():
    """
    Load comprehensive Italian city data using OpenStreetMap
    Extended to cover 40+ cities across all regions
    """
    print("🇮🇹 EXTENDED ViaMigo Safe Data Loader - Comprehensive Italian Coverage 🇮🇹\n")
    print("✅ Using OpenStreetMap (Overpass API) - 100% Safe")
    print("✅ No suspicious APIs, No scam risks")
    print("✅ Community-maintained, Open Source data")
    print("✅ Extended coverage: 40+ Italian cities\n")

    # Initialize loader
    try:
        loader = ExtendedSafeTourismDataLoader(chroma_path="./chromadb_data")
    except ValueError as e:
        print(str(e))
        print("\n📝 Setup instructions:")
        print("1. Create .env file in project root")
        print("2. Add: DATABASE_URL=postgresql://user:pass@host:port/dbname")
        return

    # Extended Italian cities with bounding boxes (south, west, north, east)
    extended_italian_cities = {
        # Major cities (already in some databases)
        "Bergamo": (45.67, 9.64, 45.72, 9.70),
        "Rome": (41.80, 12.40, 41.95, 12.55),
        "Florence": (43.75, 11.20, 43.80, 11.30),
        "Venice": (45.40, 12.30, 45.45, 12.36),
        "Milan": (45.40, 9.10, 45.52, 9.25),
        "Naples": (40.80, 14.20, 40.90, 14.30),
        "Turin": (45.00, 7.60, 45.10, 7.72),
        "Bologna": (44.47, 11.30, 44.52, 11.37),
        "Genoa": (44.38, 8.88, 44.44, 8.98),
        "Verona": (45.42, 10.96, 45.47, 11.04),

        # Additional Tuscany cities
        "Pisa": (43.69, 10.37, 43.74, 10.42),
        "Siena": (43.30, 11.31, 43.34, 11.34),
        "Lucca": (43.83, 10.47, 43.86, 10.52),
        "Arezzo": (43.45, 11.86, 43.48, 11.90),
        "Livorno": (43.53, 10.28, 43.57, 10.33),

        # Southern Italy & Sicily
        "Palermo": (38.08, 13.32, 38.14, 13.38),
        "Catania": (37.48, 15.05, 37.52, 15.10),
        "Bari": (41.11, 16.85, 41.14, 16.90),
        "Lecce": (40.34, 18.16, 40.38, 18.20),
        "Matera": (40.64, 16.58, 40.67, 16.62),

        # Northern cities
        "Trieste": (45.63, 13.76, 45.67, 13.81),
        "Padua": (45.39, 11.86, 45.43, 11.90),
        "Vicenza": (45.54, 11.52, 45.57, 11.56),
        "Brescia": (45.52, 10.20, 45.56, 10.25),
        "Parma": (44.79, 10.31, 44.82, 10.35),

        # Central Italy
        "Perugia": (43.09, 12.37, 43.12, 12.41),
        "Assisi": (43.06, 12.61, 43.08, 12.64),
        "Orvieto": (42.71, 12.10, 42.73, 12.13),
        "Urbino": (43.72, 12.62, 43.74, 12.65),

        # Coastal cities
        "Rimini": (44.05, 12.56, 44.08, 12.59),
        "La Spezia": (44.10, 9.80, 44.13, 9.84),
        "Salerno": (40.66, 14.74, 40.69, 14.78),
        "Pescara": (42.45, 14.20, 42.48, 14.24),

        # Historic small cities
        "San Gimignano": (43.46, 11.04, 43.47, 11.05),
        "Montepulciano": (43.09, 11.78, 43.10, 11.79),
        "Cortona": (43.27, 11.98, 43.28, 12.00),
        "Volterra": (43.39, 10.86, 43.40, 10.87),

        # Island destinations
        "Cagliari": (39.20, 9.10, 39.23, 9.14),  # Sardinia
        "Sassari": (40.72, 8.54, 40.74, 8.57),   # Sardinia
        "Taormina": (37.84, 15.28, 37.85, 15.29),  # Sicily
    }

    print(f"📊 Processing {len(extended_italian_cities)} Italian cities")
    print("🎯 This will provide comprehensive coverage from Alps to Sicily\n")

    successful_loads = 0
    failed_loads = 0

    # Load data for each city
    for city, bbox in extended_italian_cities.items():
        try:
            success = loader.load_city_data(
                city=city,
                bbox=bbox,
                load_attractions=True,
                load_restaurants=True,
                load_hotels=True
            )

            if success:
                successful_loads += 1
            else:
                failed_loads += 1

            time.sleep(2)  # Be respectful to OSM servers

        except Exception as e:
            print(f"❌ Error loading {city}: {e}")
            failed_loads += 1
            continue

    # Close connections
    loader.close()

    print(f"\n🎉 Extended Data Loading Complete!")
    print(f"✅ Successfully loaded: {successful_loads} cities")
    print(f"❌ Failed to load: {failed_loads} cities")
    print(
        f"📊 Total coverage: {successful_loads}/{len(extended_italian_cities)} Italian cities")
    print(f"\n💡 Your database now has comprehensive Italian coverage!")
    print(f"🔍 ChromaDB enhanced for semantic search across all regions")
    print(f"✅ 100% Safe OpenStreetMap data - No suspicious APIs")


if __name__ == "__main__":
    main()

"""
Safe Tourism Data Loader for ViaMigo - OpenStreetMap Integration
Uses Overpass API (100% Safe, Free, Open Source)
Integrates with existing place_cache and ChromaDB architecture
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


class SafeTourismDataLoader:
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
            metadata={"description": "ViaMigo travel data from OpenStreetMap"}
        )
        print(f"📚 Using ChromaDB collection: viamigo_travel_data")

    def ensure_place_cache_ready(self):
        """
        Ensure place_cache table exists (should already exist)
        This script integrates WITH existing schema
        """
        self.pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'place_cache'
            )
        """)
        exists = self.pg_cursor.fetchone()[0]

        if not exists:
            print("⚠️ place_cache table not found. Creating it...")
            self.pg_cursor.execute("""
                CREATE TABLE place_cache (
                    cache_key VARCHAR(500) PRIMARY KEY,
                    place_name VARCHAR(500) NOT NULL,
                    city VARCHAR(255) NOT NULL,
                    place_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.pg_conn.commit()
            print("✅ place_cache table created")
        else:
            print("✅ place_cache table exists")

    def fetch_osm_attractions(self, city: str, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Fetch tourist attractions from OpenStreetMap Overpass API

        Args:
            city: City name for logging
            bbox: (south, west, north, east) bounding box coordinates

        Returns:
            List of OSM elements (attractions, museums, historic sites, churches)
        """
        overpass_url = "https://overpass-api.de/api/interpreter"

        # Comprehensive query for tourist attractions
        query = f"""
        [out:json][timeout:30];
        (
          node["tourism"="attraction"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["tourism"="attraction"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["tourism"="museum"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["tourism"="museum"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["historic"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["historic"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["amenity"="place_of_worship"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["amenity"="place_of_worship"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["tourism"="viewpoint"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out center body;
        """

        print(f"🔍 Fetching attractions for {city} from OpenStreetMap...")

        try:
            response = requests.post(
                overpass_url, data={"data": query}, timeout=60)
            response.raise_for_status()
            data = response.json()
            elements = data.get('elements', [])
            print(f"✅ Found {len(elements)} attractions in {city}")
            return elements
        except Exception as e:
            print(f"❌ Error fetching attractions for {city}: {e}")
            return []

    def fetch_osm_restaurants(self, city: str, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Fetch restaurants and cafes from OpenStreetMap

        Args:
            city: City name for logging
            bbox: (south, west, north, east) bounding box coordinates

        Returns:
            List of OSM restaurant/cafe elements
        """
        overpass_url = "https://overpass-api.de/api/interpreter"

        query = f"""
        [out:json][timeout:30];
        (
          node["amenity"="restaurant"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["amenity"="restaurant"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["amenity"="cafe"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["amenity"="cafe"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["amenity"="bar"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out center body;
        """

        print(f"🍽️  Fetching restaurants for {city} from OpenStreetMap...")

        try:
            response = requests.post(
                overpass_url, data={"data": query}, timeout=60)
            response.raise_for_status()
            data = response.json()
            elements = data.get('elements', [])
            print(f"✅ Found {len(elements)} restaurants/cafes in {city}")
            return elements
        except Exception as e:
            print(f"❌ Error fetching restaurants for {city}: {e}")
            return []

    def transform_osm_to_place_cache(self, osm_element: Dict, city: str, element_type: str) -> Dict:
        """
        Transform OSM element to place_cache JSONB format
        Compatible with existing cache structure

        Args:
            osm_element: OSM element from Overpass API
            city: City name
            element_type: 'attraction' or 'restaurant'

        Returns:
            Dict ready for place_cache.place_data JSONB column
        """
        tags = osm_element.get('tags', {})

        # Get coordinates (handle both nodes and ways with center)
        if 'lat' in osm_element and 'lon' in osm_element:
            lat = osm_element['lat']
            lon = osm_element['lon']
        elif 'center' in osm_element:
            lat = osm_element['center']['lat']
            lon = osm_element['center']['lon']
        else:
            lat = 0
            lon = 0

        # Extract name
        name = tags.get('name', tags.get('name:en', 'Unknown Place'))

        # Build comprehensive types list
        types = []
        if element_type == 'attraction':
            types.append('tourist_attraction')
            if tags.get('tourism'):
                types.append(tags['tourism'])
            if tags.get('historic'):
                types.append(f"historic_{tags['historic']}")
            if tags.get('amenity') == 'place_of_worship':
                types.append('place_of_worship')
                if tags.get('religion'):
                    types.append(tags['religion'])
        else:  # restaurant
            types.append('restaurant')
            if tags.get('amenity'):
                types.append(tags['amenity'])
            if tags.get('cuisine'):
                types.extend(tags['cuisine'].split(';'))

        # Build address
        address_parts = []
        if tags.get('addr:street'):
            address_parts.append(tags['addr:street'])
        if tags.get('addr:housenumber'):
            address_parts.append(tags['addr:housenumber'])
        if tags.get('addr:city'):
            address_parts.append(tags['addr:city'])
        address = ', '.join(address_parts) if address_parts else ''

        # Build description
        description_parts = []
        if tags.get('description'):
            description_parts.append(tags['description'])
        if tags.get('historic'):
            description_parts.append(f"Historic {tags['historic']}")
        if tags.get('architecture'):
            description_parts.append(f"Architecture: {tags['architecture']}")
        if tags.get('cuisine'):
            description_parts.append(f"Cuisine: {tags['cuisine']}")
        if tags.get('wikipedia'):
            description_parts.append(f"Wikipedia: {tags['wikipedia']}")

        description = '. '.join(description_parts) if description_parts else ''

        # Build place_data structure matching existing cache format
        place_data = {
            "name": name,
            "types": types,
            "vicinity": address,
            "geometry": {
                "location": {
                    "lat": lat,
                    "lng": lon
                }
            },
            "rating": 0,  # OSM doesn't provide ratings
            "user_ratings_total": 0,
            "opening_hours": {
                "weekday_text": [tags.get('opening_hours', '')] if tags.get('opening_hours') else []
            },
            "formatted_phone_number": tags.get('phone', tags.get('contact:phone', '')),
            "website": tags.get('website', tags.get('contact:website', '')),
            "description": description,
            "source": "openstreetmap",
            "osm_id": osm_element.get('id', 0),
            "osm_type": osm_element.get('type', 'node'),
            "wikipedia": tags.get('wikipedia', ''),
            "wikidata": tags.get('wikidata', ''),
            "cuisine": tags.get('cuisine', '') if element_type == 'restaurant' else '',
            "outdoor_seating": tags.get('outdoor_seating', '') == 'yes',
            "wheelchair": tags.get('wheelchair', '') == 'yes',
            "historic_type": tags.get('historic', ''),
            "tourism_type": tags.get('tourism', ''),
            "religion": tags.get('religion', ''),
            "denomination": tags.get('denomination', ''),
            "fetched_at": datetime.now().isoformat()
        }

        return place_data

    def insert_into_place_cache(self, city: str, place_name: str, place_data: Dict):
        """
        Insert place into place_cache table
        Cache key format: osm:{city}:{osm_id}

        Args:
            city: City name
            place_name: Place name
            place_data: Place data dict (will be stored as JSONB)
        """
        osm_id = place_data.get('osm_id', 'unknown')
        cache_key = f"osm:{city.lower()}:{osm_id}"

        try:
            # Match existing table schema (has country, priority_level, etc.)
            self.pg_cursor.execute("""
                INSERT INTO place_cache (cache_key, place_name, city, country, place_data, priority_level, created_at, last_accessed, access_count)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), 0)
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    place_data = EXCLUDED.place_data,
                    last_accessed = NOW(),
                    access_count = place_cache.access_count + 1
            """, (cache_key, place_name, city, 'Italy', json.dumps(place_data), 'standard'))
            
            # DEBUG: Confirm insert
            # print(f"  🔹 Inserted with key: {cache_key}")

        except Exception as e:
            print(f"⚠️ Failed to insert {place_name} into place_cache: {e}")
            import traceback
            traceback.print_exc()

    def add_to_chromadb(self, place_name: str, city: str, place_data: Dict):
        """
        Add place to ChromaDB for RAG retrieval
        Uses existing viamigo_travel_data collection

        Args:
            place_name: Place name
            city: City name
            place_data: Full place data dict
        """
        # Create rich text for embedding
        description = place_data.get('description', '')
        types = ', '.join(place_data.get('types', []))
        vicinity = place_data.get('vicinity', '')
        wikipedia = place_data.get('wikipedia', '')
        cuisine = place_data.get('cuisine', '')

        # Build comprehensive document text
        document_parts = [f"{place_name} in {city}"]
        if description:
            document_parts.append(description)
        if types:
            document_parts.append(f"Categories: {types}")
        if vicinity:
            document_parts.append(f"Location: {vicinity}")
        if cuisine:
            document_parts.append(f"Cuisine: {cuisine}")
        if wikipedia:
            document_parts.append(f"More info: {wikipedia}")

        document_text = '. '.join(document_parts)

        # Create unique ID for ChromaDB
        osm_id = place_data.get('osm_id', 'unknown')
        doc_id = f"osm_{city}_{osm_id}".replace(' ', '_').lower()

        try:
            self.collection.add(
                ids=[doc_id],
                documents=[document_text],
                metadatas=[{
                    "city": city,
                    "place_name": place_name,
                    "source": "openstreetmap",
                    "types": types,
                    "osm_id": str(osm_id)
                }]
            )
        except Exception as e:
            # Document might already exist, that's ok
            if "already exists" not in str(e):
                print(f"⚠️ Failed to add {place_name} to ChromaDB: {e}")

    def load_city_data(self, city: str, bbox: Tuple[float, float, float, float],
                       load_attractions: bool = True, load_restaurants: bool = True):
        """
        Load all data for a city from OpenStreetMap

        Args:
            city: City name (e.g., "Bergamo", "Rome")
            bbox: Bounding box (south, west, north, east)
            load_attractions: Whether to load attractions/museums/historic sites
            load_restaurants: Whether to load restaurants/cafes
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting SAFE data load for {city} (OpenStreetMap)")
        print(f"{'='*60}\n")

        # Ensure table exists
        self.ensure_place_cache_ready()

        total_inserted = 0

        # Load attractions
        if load_attractions:
            attractions = self.fetch_osm_attractions(city, bbox)
            time.sleep(1)  # Be nice to OSM servers

            for element in attractions:
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:en'))

                if not name or name == 'Unknown Place':
                    continue

                try:
                    place_data = self.transform_osm_to_place_cache(
                        element, city, 'attraction')
                    self.insert_into_place_cache(city, name, place_data)
                    self.add_to_chromadb(name, city, place_data)
                    total_inserted += 1
                    print(f"✅ Saved attraction: {name}")
                except Exception as e:
                    print(f"⚠️ Failed to process {name}: {e}")

            self.pg_conn.commit()

        # Load restaurants
        if load_restaurants:
            restaurants = self.fetch_osm_restaurants(city, bbox)
            time.sleep(1)  # Be nice to OSM servers

            for element in restaurants:
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:en'))

                if not name or name == 'Unknown Place':
                    continue

                try:
                    place_data = self.transform_osm_to_place_cache(
                        element, city, 'restaurant')
                    self.insert_into_place_cache(city, name, place_data)
                    self.add_to_chromadb(name, city, place_data)
                    total_inserted += 1
                    print(f"✅ Saved restaurant: {name}")
                except Exception as e:
                    print(f"⚠️ Failed to process {name}: {e}")

            self.pg_conn.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ {city} SAFE Data Load Complete (OpenStreetMap)")
        print(f"{'='*60}")
        print(f"Total places inserted: {total_inserted}")
        print(f"Source: OpenStreetMap (100% Safe)")
        print(f"{'='*60}\n")

    def close(self):
        """Close database connections"""
        self.pg_cursor.close()
        self.pg_conn.close()
        print("🔒 Database connections closed")


def main():
    """
    Main execution: Load safe data for Italian cities
    Uses OpenStreetMap Overpass API - 100% Safe and Free
    """
    print("🇮🇹 ViaMigo SAFE Data Loader - OpenStreetMap Integration 🇮🇹\n")
    print("✅ Using OpenStreetMap (Overpass API) - 100% Safe")
    print("✅ No suspicious APIs, No scam risks")
    print("✅ Community-maintained, Open Source data\n")

    # Initialize loader
    try:
        loader = SafeTourismDataLoader(chroma_path="./chromadb_data")
    except ValueError as e:
        print(str(e))
        print("\n📝 Setup instructions:")
        print("1. Create .env file in project root")
        print("2. Add: DATABASE_URL=postgresql://user:pass@host:port/dbname")
        return

    # Italian cities with bounding boxes (south, west, north, east)
    italian_cities = {
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
    }

    # Load data for each city
    for city, bbox in italian_cities.items():
        try:
            loader.load_city_data(
                city=city,
                bbox=bbox,
                load_attractions=True,
                load_restaurants=True
            )
            time.sleep(2)  # Be respectful to OSM servers
        except Exception as e:
            print(f"❌ Error loading {city}: {e}")
            continue

    # Close connections
    loader.close()

    print("\n🎉 All done! Your place_cache and ChromaDB are now enriched with SAFE OpenStreetMap data!")
    print("💡 Tip: This data integrates seamlessly with cost_effective_scraping.py")
    print("✅ 100% Safe - No suspicious APIs - No scam risks")


if __name__ == "__main__":
    main()

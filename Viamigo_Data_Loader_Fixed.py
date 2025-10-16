"""
⚠️⚠️⚠️ DEPRECATED - DO NOT USE ⚠️⚠️⚠️

OpenTripMap has been identified as SUSPICIOUS/POTENTIAL SCAM.

USE SAFE ALTERNATIVE: Safe_Data_Loader.py (OpenStreetMap)

See: OPENTRIPMAP_WARNING.md for details

⚠️⚠️⚠️ DEPRECATED - DO NOT USE ⚠️⚠️⚠️
"""

"""
ViaMigo AI Companion - Tourism Data Loader (CONTEXTUALIZED)
Load tourism data from OpenTripMap FREE API into existing PostgreSQL place_cache and ChromaDB
Integrates seamlessly with current app architecture

⚠️ WARNING: This file uses OpenTripMap which has been identified as suspicious.
⚠️ DO NOT USE - Use Safe_Data_Loader.py instead (OpenStreetMap)

Usage:
    python Viamigo_Data_Loader_Fixed.py

Requirements:
    - .env file with DATABASE_URL and OPENTRIPMAP_API_KEY
    - Existing place_cache table in PostgreSQL
    - ChromaDB at ./chromadb_data with collection viamigo_travel_data
"""

from datetime import datetime
from dotenv import load_dotenv
import time
from typing import List, Dict, Optional
import json
from sentence_transformers import SentenceTransformer
import chromadb
from psycopg2.extras import execute_batch
import psycopg2
import os
import requests

# Load environment variables
load_dotenv()


class ViaMigoDataLoader:
    def __init__(self, chroma_path: str = "./chromadb_data"):
        """
        Initialize connections to PostgreSQL and ChromaDB
        Uses DATABASE_URL from .env file for PostgreSQL connection
        """
        # Get PostgreSQL connection from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError(
                "❌ DATABASE_URL not found in .env file. Add: DATABASE_URL=postgresql://user:pass@host:port/dbname")

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
            metadata={"description": "ViaMigo travel data from OpenTripMap API"}
        )
        print(f"📚 Using ChromaDB collection: viamigo_travel_data")

        # Get OpenTripMap API key from .env
        self.opentripmap_api_key = os.getenv('OPENTRIPMAP_API_KEY')
        if not self.opentripmap_api_key:
            raise ValueError(
                "❌ OPENTRIPMAP_API_KEY not found in .env file. Get free key from: https://opentripmap.io/")

    def ensure_place_cache_ready(self):
        """
        Ensure place_cache table exists (it should from main app)
        This script integrates WITH existing schema, not replacing it
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

    def geocode_city(self, city: str, country_code: str) -> Optional[Dict]:
        """
        Get coordinates for a city using OpenTripMap geocoding

        Args:
            city: City name (e.g., "Bergamo", "Rome")
            country_code: ISO country code (e.g., "it", "fr")

        Returns:
            Dict with lat/lon or None if failed
        """
        geocode_url = "https://api.opentripmap.com/0.1/en/places/geoname"
        params = {
            "name": city,
            "country": country_code,
            "apikey": self.opentripmap_api_key
        }

        try:
            response = requests.get(geocode_url, params=params, timeout=10)
            response.raise_for_status()
            geo_data = response.json()

            if 'lat' in geo_data and 'lon' in geo_data:
                print(
                    f"📍 {city} coordinates: ({geo_data['lat']}, {geo_data['lon']})")
                return {"lat": geo_data['lat'], "lon": geo_data['lon']}
            else:
                print(f"⚠️ No coordinates found for {city}")
                return None

        except Exception as e:
            print(f"❌ Geocoding error for {city}: {e}")
            return None

    def fetch_pois_in_radius(self, city: str, latitude: float, longitude: float,
                             radius: int = 5000, limit: int = 100) -> List[Dict]:
        """
        Fetch POIs (Points of Interest) from OpenTripMap API
        FREE tier supports up to 100 places per request

        Args:
            city: City name for logging
            latitude: Center latitude
            longitude: Center longitude
            radius: Search radius in meters (default 5km)
            limit: Max results (default 100, free tier limit)

        Returns:
            List of POI dictionaries with xid, name, kinds, point
        """
        poi_url = "https://api.opentripmap.com/0.1/en/places/radius"

        params = {
            "radius": radius,
            "lon": longitude,
            "lat": latitude,
            "kinds": "interesting_places,tourist_facilities,restaurants,museums,monuments,churches",
            "apikey": self.opentripmap_api_key,
            "limit": limit,
            "format": "json"
        }

        print(
            f"🔍 Fetching POIs for {city} (radius: {radius}m, limit: {limit})...")

        try:
            response = requests.get(poi_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # OpenTripMap returns array of POIs
            if isinstance(data, list):
                print(f"✅ Found {len(data)} POIs for {city}")
                return data
            else:
                print(
                    f"⚠️ Unexpected response format for {city}: {type(data)}")
                return []

        except Exception as e:
            print(f"❌ Error fetching POIs for {city}: {e}")
            return []

    def get_poi_details(self, xid: str) -> Optional[Dict]:
        """
        Get detailed information about a POI by its XID
        Includes description, Wikipedia link, images, etc.

        Args:
            xid: OpenTripMap place identifier

        Returns:
            Detailed POI dict or None if failed
        """
        detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}"
        params = {"apikey": self.opentripmap_api_key}

        try:
            response = requests.get(detail_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ Failed to get details for {xid}: {e}")
            return None

    def transform_to_place_cache_format(self, poi: Dict, city: str, details: Optional[Dict] = None) -> Dict:
        """
        Transform OpenTripMap POI data to place_cache JSONB format
        Compatible with existing cache structure used by cost_effective_scraping.py

        Args:
            poi: Basic POI data from radius search
            city: City name
            details: Optional detailed POI data

        Returns:
            Dict ready for place_cache.place_data JSONB column
        """
        # Extract coordinates
        lat = poi.get('point', {}).get('lat', 0)
        lon = poi.get('point', {}).get('lon', 0)

        # Build place_data structure matching existing cache format
        place_data = {
            "name": poi.get('name', 'Unknown Place'),
            "types": poi.get('kinds', '').split(',') if poi.get('kinds') else [],
            "vicinity": details.get('address', {}).get('road', '') if details else '',
            "geometry": {
                "location": {
                    "lat": lat,
                    "lng": lon
                }
            },
            "rating": details.get('rate', 0) if details else 0,
            "user_ratings_total": 0,  # OpenTripMap doesn't provide this
            "opening_hours": {},
            "formatted_phone_number": details.get('address', {}).get('phone', '') if details else '',
            "website": details.get('url', '') if details else '',
            "description": details.get('wikipedia_extracts', {}).get('text', '') if details else '',
            "source": "opentripmap",
            "xid": poi.get('xid', ''),
            "kinds": poi.get('kinds', ''),
            "wikipedia": details.get('wikipedia', '') if details else '',
            "image": details.get('image', '') if details else '',
            "fetched_at": datetime.now().isoformat()
        }

        return place_data

    def insert_into_place_cache(self, city: str, place_name: str, place_data: Dict):
        """
        Insert place into place_cache table using standard cache_key format
        Cache key format: opentripmap:{city}:{place_name}

        Args:
            city: City name
            place_name: Place name
            place_data: Place data dict (will be stored as JSONB)
        """
        cache_key = f"opentripmap:{city.lower()}:{place_name.lower()}"

        try:
            self.pg_cursor.execute("""
                INSERT INTO place_cache (cache_key, place_name, city, place_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    place_data = EXCLUDED.place_data,
                    updated_at = NOW()
            """, (cache_key, place_name, city, json.dumps(place_data)))

        except Exception as e:
            print(f"⚠️ Failed to insert {place_name} into place_cache: {e}")

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
        kinds = ', '.join(place_data.get('types', []))
        vicinity = place_data.get('vicinity', '')

        document_text = f"{place_name} in {city}. {description}. Categories: {kinds}. Location: {vicinity}"

        # Create unique ID for ChromaDB
        doc_id = f"opentripmap_{city}_{place_name}".replace(' ', '_').lower()

        try:
            self.collection.add(
                ids=[doc_id],
                documents=[document_text],
                metadatas=[{
                    "city": city,
                    "place_name": place_name,
                    "source": "opentripmap",
                    "kinds": kinds,
                    "rating": str(place_data.get('rating', 0))
                }]
            )
        except Exception as e:
            print(f"⚠️ Failed to add {place_name} to ChromaDB: {e}")

    def load_city_data(self, city: str, country_code: str = "it", radius: int = 5000,
                       fetch_details: bool = True, limit: int = 50):
        """
        Load all data for a city: geocode, fetch POIs, get details, store in DB + ChromaDB

        Args:
            city: City name (e.g., "Bergamo", "Rome", "Florence")
            country_code: ISO country code (default "it" for Italy)
            radius: Search radius in meters (default 5km)
            fetch_details: Whether to fetch detailed info (slower but richer data)
            limit: Max POIs to process (default 50 to respect free tier)
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting data load for {city}, {country_code.upper()}")
        print(f"{'='*60}\n")

        # Ensure table exists
        self.ensure_place_cache_ready()

        # Step 1: Geocode city
        coords = self.geocode_city(city, country_code)
        if not coords:
            print(f"❌ Cannot proceed without coordinates for {city}")
            return

        # Step 2: Fetch POIs in radius
        pois = self.fetch_pois_in_radius(
            city, coords['lat'], coords['lon'], radius, limit)

        if not pois:
            print(f"⚠️ No POIs found for {city}")
            return

        # Step 3: Process each POI
        successful_inserts = 0
        failed_inserts = 0

        for i, poi in enumerate(pois, 1):
            place_name = poi.get('name', f'Place_{i}')
            xid = poi.get('xid')

            print(f"\n[{i}/{len(pois)}] Processing: {place_name}")

            # Get detailed info if requested
            details = None
            if fetch_details and xid:
                details = self.get_poi_details(xid)
                time.sleep(0.3)  # Rate limiting for free tier

            # Transform to place_cache format
            place_data = self.transform_to_place_cache_format(
                poi, city, details)

            try:
                # Insert into PostgreSQL
                self.insert_into_place_cache(city, place_name, place_data)

                # Add to ChromaDB for RAG
                self.add_to_chromadb(place_name, city, place_data)

                successful_inserts += 1
                print(f"✅ Saved: {place_name}")

            except Exception as e:
                failed_inserts += 1
                print(f"❌ Failed to save {place_name}: {e}")

        # Commit all PostgreSQL changes
        self.pg_conn.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ {city} Data Load Complete")
        print(f"{'='*60}")
        print(f"Total POIs processed: {len(pois)}")
        print(f"Successful inserts: {successful_inserts}")
        print(f"Failed inserts: {failed_inserts}")
        print(f"{'='*60}\n")

    def close(self):
        """Close database connections"""
        self.pg_cursor.close()
        self.pg_conn.close()
        print("🔒 Database connections closed")


def main():
    """
    Main execution: Load data for Italian cities
    Add Bergamo and other key tourist destinations
    """
    print("🇮🇹 ViaMigo Data Loader - OpenTripMap Integration 🇮🇹\n")

    # Initialize loader
    try:
        loader = ViaMigoDataLoader(chroma_path="./chromadb_data")
    except ValueError as e:
        print(str(e))
        print("\n📝 Setup instructions:")
        print("1. Create .env file in project root")
        print("2. Add: DATABASE_URL=postgresql://user:pass@host:port/dbname")
        print("3. Add: OPENTRIPMAP_API_KEY=your_key_here")
        print("4. Get free API key from: https://opentripmap.io/")
        return

    # Italian cities to load (including Bergamo!)
    italian_cities = [
        {"city": "Bergamo", "country_code": "it", "radius": 5000, "limit": 50},
        {"city": "Rome", "country_code": "it", "radius": 8000, "limit": 100},
        {"city": "Florence", "country_code": "it", "radius": 5000, "limit": 80},
        {"city": "Venice", "country_code": "it", "radius": 4000, "limit": 60},
        {"city": "Milan", "country_code": "it", "radius": 6000, "limit": 80},
        {"city": "Naples", "country_code": "it", "radius": 5000, "limit": 70},
        {"city": "Turin", "country_code": "it", "radius": 5000, "limit": 50},
        {"city": "Bologna", "country_code": "it", "radius": 4000, "limit": 50},
        {"city": "Genoa", "country_code": "it", "radius": 5000, "limit": 50},
        {"city": "Verona", "country_code": "it", "radius": 4000, "limit": 40},
    ]

    # Load data for each city
    for city_config in italian_cities:
        try:
            loader.load_city_data(
                city=city_config["city"],
                country_code=city_config["country_code"],
                radius=city_config["radius"],
                fetch_details=True,  # Get rich descriptions
                limit=city_config["limit"]
            )
        except Exception as e:
            print(f"❌ Error loading {city_config['city']}: {e}")
            continue

    # Close connections
    loader.close()

    print("\n🎉 All done! Your place_cache and ChromaDB are now enriched with FREE OpenTripMap data!")
    print("💡 Tip: This data integrates seamlessly with cost_effective_scraping.py")


if __name__ == "__main__":
    main()

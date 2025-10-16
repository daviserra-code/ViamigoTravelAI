"""
ViaMigo AI Companion - Tourism Data Loader
Load tourism data from multiple FREE sources into PostgreSQL and ChromaDB
Integrates with existing place_cache and hotel_reviews tables
"""

import os
import requests
import psycopg2
from psycopg2.extras import execute_batch
import chromadb
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict, Optional
import time
from dotenv import load_dotenv

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
            raise ValueError("DATABASE_URL not found in environment variables")

        self.pg_conn = psycopg2.connect(database_url)
        self.pg_cursor = self.pg_conn.cursor()
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Initialize embedding model for RAG
        print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Use single ChromaDB collection consistent with app architecture
        self.collection = self.chroma_client.get_or_create_collection(
            name="viamigo_travel_data",
            metadata={"description": "ViaMigo travel data from OpenTripMap API"}
        )
        print(f"📚 Using ChromaDB collection: viamigo_travel_data")

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
        print("✅ Embedding model loaded")

    def create_tables(self):
        """Create database schema for ViaMigo"""

        # Attractions table
        self.pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS attractions (
            id SERIAL PRIMARY KEY,
            external_id VARCHAR(255) UNIQUE,
            name VARCHAR(500) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            city VARCHAR(200),
            country VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            address TEXT,
            website VARCHAR(500),
            phone VARCHAR(50),
            rating DECIMAL(3, 2),
            price_level VARCHAR(50),
            opening_hours JSONB,
            image_url TEXT,
            tags TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_city ON attractions(city);
        CREATE INDEX IF NOT EXISTS idx_category ON attractions(category);
        CREATE INDEX IF NOT EXISTS idx_location ON attractions(latitude, longitude);
        """)

        # Restaurants table
        self.pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id SERIAL PRIMARY KEY,
            external_id VARCHAR(255) UNIQUE,
            name VARCHAR(500) NOT NULL,
            description TEXT,
            cuisine_type VARCHAR(100),
            city VARCHAR(200),
            country VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            address TEXT,
            website VARCHAR(500),
            phone VARCHAR(50),
            rating DECIMAL(3, 2),
            price_range VARCHAR(50),
            opening_hours JSONB,
            image_url TEXT,
            amenities TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_rest_city ON restaurants(city);
        CREATE INDEX IF NOT EXISTS idx_cuisine ON restaurants(cuisine_type);
        """)

        # Monuments table
        self.pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS monuments (
            id SERIAL PRIMARY KEY,
            external_id VARCHAR(255) UNIQUE,
            name VARCHAR(500) NOT NULL,
            description TEXT,
            historical_period VARCHAR(200),
            city VARCHAR(200),
            country VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            address TEXT,
            website VARCHAR(500),
            entry_fee VARCHAR(100),
            unesco_site BOOLEAN DEFAULT FALSE,
            built_year INTEGER,
            architect VARCHAR(200),
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        self.pg_conn.commit()
        print("✅ Database tables created successfully")

    def load_from_opentripmap(self, city: str, country_code: str,
                              api_key: str, radius: int = 5000):
        """
        Load POIs from OpenTripMap API
        Get free API key from: https://opentripmap.io/

        Args:
            city: City name (e.g., "Rome", "Paris")
            country_code: ISO country code (e.g., "it", "fr")
            api_key: Your OpenTripMap API key
            radius: Search radius in meters
        """
        print(f"🌍 Loading data for {city}, {country_code}...")

        # Get city coordinates
        geocode_url = f"https://api.opentripmap.com/0.1/en/places/geoname"
        params = {"name": city, "country": country_code, "apikey": api_key}

        response = requests.get(geocode_url, params=params)
        if response.status_code != 200:
            print(f"❌ Failed to geocode {city}")
            return

        geo_data = response.json()
        lat, lon = geo_data['lat'], geo_data['lon']

        # Get POIs in radius
        poi_url = f"https://api.opentripmap.com/0.1/en/places/radius"
        params = {
            "radius": radius,
            "lon": lon,
            "lat": lat,
            "kinds": "interesting_places,tourist_facilities,restaurants,monuments",
            "apikey": api_key,
            "limit": 500
        }

        response = requests.get(poi_url, params=params)
        if response.status_code != 200:
            print(f"❌ Failed to fetch POIs")
            return

        pois = response.json()['features']
        print(f"📍 Found {len(pois)} points of interest")

        attractions_data = []
        restaurants_data = []
        monuments_data = []

        for poi in pois:
            props = poi['properties']
            coords = poi['geometry']['coordinates']

            # Get detailed info
            detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{props['xid']}"
            detail_response = requests.get(
                detail_url, params={"apikey": api_key})

            if detail_response.status_code == 200:
                details = detail_response.json()

                base_data = (
                    props['xid'],
                    props.get('name', 'Unknown'),
                    details.get('wikipedia_extracts', {}).get('text', ''),
                    city,
                    country_code,
                    coords[1],  # latitude
                    coords[0],  # longitude
                    details.get('address', {}).get('road', ''),
                    details.get('url', ''),
                    details.get('image', ''),
                    props.get('kinds', '').split(',')
                )

                # Categorize by kind
                kinds = props.get('kinds', '').lower()

                if 'restaurant' in kinds or 'cafe' in kinds:
                    restaurants_data.append(base_data + (
                        props.get('rate', 0),
                        None,  # cuisine_type - would need additional API
                    ))
                elif 'monument' in kinds or 'historic' in kinds:
                    monuments_data.append(base_data)
                else:
                    attractions_data.append(base_data + (
                        props.get('rate', 0),
                        props.get('kinds', '').split(',')[
                            0] if props.get('kinds') else 'attraction',
                    ))

            time.sleep(0.1)  # Rate limiting

        # Insert into database
        self._insert_attractions(attractions_data)
        self._insert_restaurants(restaurants_data)
        self._insert_monuments(monuments_data)

        print(
            f"✅ Loaded {len(attractions_data)} attractions, {len(restaurants_data)} restaurants, {len(monuments_data)} monuments")

    def _insert_attractions(self, data: List):
        """Insert attractions into database"""
        if not data:
            return

        query = """
        INSERT INTO attractions 
        (external_id, name, description, city, country, latitude, longitude, 
         address, website, image_url, tags, rating, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_id) DO NOTHING
        """
        execute_batch(self.pg_cursor, query, data)
        self.pg_conn.commit()

    def _insert_restaurants(self, data: List):
        """Insert restaurants into database"""
        if not data:
            return

        query = """
        INSERT INTO restaurants 
        (external_id, name, description, city, country, latitude, longitude,
         address, website, image_url, amenities, rating)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_id) DO NOTHING
        """
        execute_batch(self.pg_cursor, query, data)
        self.pg_conn.commit()

    def _insert_monuments(self, data: List):
        """Insert monuments into database"""
        if not data:
            return

        query = """
        INSERT INTO monuments 
        (external_id, name, description, city, country, latitude, longitude,
         address, website, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_id) DO NOTHING
        """
        execute_batch(self.pg_cursor, query, data)
        self.pg_conn.commit()

    def add_to_chromadb_for_rag(self):
        """Add all data to ChromaDB for RAG queries"""
        print("🔄 Adding data to ChromaDB for RAG...")

        # Create collections
        attractions_collection = self.chroma_client.get_or_create_collection(
            "attractions")
        restaurants_collection = self.chroma_client.get_or_create_collection(
            "restaurants")
        monuments_collection = self.chroma_client.get_or_create_collection(
            "monuments")

        # Fetch and embed attractions
        self.pg_cursor.execute("""
            SELECT id, name, description, city, category, address, latitude, longitude
            FROM attractions WHERE description IS NOT NULL AND description != ''
        """)

        for row in self.pg_cursor.fetchall():
            doc_id, name, desc, city, category, address, lat, lon = row

            text = f"{name} in {city}. Category: {category}. {desc}"
            embedding = self.embedding_model.encode([text])[0].tolist()

            attractions_collection.add(
                ids=[f"attr_{doc_id}"],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "name": name,
                    "city": city,
                    "category": category,
                    "address": address or "",
                    "latitude": str(lat),
                    "longitude": str(lon)
                }]
            )

        print("✅ ChromaDB populated for RAG queries")

    def close(self):
        """Close connections"""
        self.pg_cursor.close()
        self.pg_conn.close()


# Usage Example
if __name__ == "__main__":
    # PostgreSQL config
    pg_config = {
        "host": "ep-ancient-morning-a6us6om6.us-west-2.aws.neon.tech",
        "database": "neondb",
        "user": "neondb_user",
        "password": "npg_r9e2PGORqsAx",
        "port": "5432"
    }

    # Initialize loader
    loader = ViaMigoDataLoader(pg_config)

    # Create database schema
    loader.create_tables()

    # Load data from OpenTripMap (get free API key from opentripmap.io)
    OPENTRIPMAP_API_KEY = "your_api_key_here"

    # Popular Italian cities for your ViaMigo app
    italian_cities = [
        ("Rome", "it"),
        ("Florence", "it"),
        ("Venice", "it"),
        ("Milan", "it"),
        ("Naples", "it"),
        ("Genoa", "it"),  # Your location!
        ("Turin", "it"),
        ("Bologna", "it")
    ]

    for city, country in italian_cities:
        loader.load_from_opentripmap(city, country, OPENTRIPMAP_API_KEY)
        time.sleep(1)  # Rate limiting between cities

    # Add to ChromaDB for RAG
    loader.add_to_chromadb_for_rag()

    # Close connections
    loader.close()

    print("🎉 ViaMigo database initialization complete!")

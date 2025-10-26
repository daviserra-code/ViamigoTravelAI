#!/usr/bin/env python3
"""
Complete Missing Cities Loader
Targeted approach to complete the 2 failed cities from Extended_Safe_Data_Loader
"""

import requests
import json
import time
import sys
import os
import psycopg2
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ChromaDB functionality
try:
    import chromadb
    from chromadb.config import Settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the ViamigoTravelAI directory")
    sys.exit(1)


class MissingCitiesLoader:
    def __init__(self):
        """Initialize the missing cities loader with optimized settings"""
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ViamigoTravelAI/1.0 (Educational Purpose)',
            'Accept': 'application/json'
        })

        # Initialize PostgreSQL connection
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("❌ DATABASE_URL not found in .env file")

        # Add SSL requirement for cloud databases (Neon, Supabase, etc.)
        if '?' in database_url:
            if 'sslmode=' not in database_url:
                database_url += '&sslmode=require'
        else:
            database_url += '?sslmode=require'

        self.pg_conn = psycopg2.connect(database_url)
        print("✅ PostgreSQL connection established")

        # Initialize ChromaDB client
        try:
            self.chroma_client = chromadb.PersistentClient(
                path="/workspaces/ViamigoTravelAI/chromadb_data",
                settings=Settings(anonymized_telemetry=False)
            )
            # Get or create the collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="places_collection",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ ChromaDB client initialized successfully")
        except Exception as e:
            print(f"⚠️  ChromaDB initialization warning: {e}")
            self.chroma_client = None
            self.collection = None

    def osm_to_place_data(self, osm_element: Dict[str, Any], city: str) -> Dict[str, Any]:
        """Convert OSM element to standardized place data format"""
        tags = osm_element.get('tags', {})

        # Determine category based on OSM tags
        category = self.determine_category(tags)

        # Build comprehensive description
        description = self.build_description(tags, osm_element)

        # Extract coordinates
        lat = osm_element.get('lat')
        lon = osm_element.get('lon')

        # For ways/relations, try to get center coordinates
        if not lat and 'center' in osm_element:
            lat = osm_element['center'].get('lat')
            lon = osm_element['center'].get('lon')

        place_data = {
            'name': tags.get('name', tags.get('name:it', tags.get('name:en', f"Unnamed {category}"))),
            'category': category,
            'description': description,
            'lat': lat,
            'lng': lon,
            'city': city,
            'country': 'Italy',
            'tags': tags,
            'osm_id': osm_element.get('id'),
            'osm_type': osm_element.get('type')
        }

        return place_data

    def determine_category(self, tags: Dict[str, str]) -> str:
        """Determine place category from OSM tags"""
        # Tourism and attractions
        if tags.get('tourism') in ['attraction', 'museum', 'monument', 'artwork', 'viewpoint']:
            return 'tourist_attraction'
        elif tags.get('tourism') in ['hotel', 'guest_house', 'hostel']:
            return 'hotel'
        elif tags.get('tourism') == 'information':
            return 'tourist_information'

        # Food and dining
        elif tags.get('amenity') in ['restaurant', 'cafe', 'bar', 'pub', 'fast_food']:
            return 'restaurant'

        # Historic sites
        elif tags.get('historic'):
            return 'historic_site'

        # Religious sites
        elif tags.get('amenity') == 'place_of_worship' or tags.get('building') == 'church':
            return 'church'

        # Shopping
        elif tags.get('shop') or tags.get('amenity') == 'marketplace':
            return 'shopping'

        # Nature and parks
        elif tags.get('leisure') == 'park' or tags.get('landuse') == 'forest':
            return 'park'

        # Transportation
        elif tags.get('public_transport') or tags.get('railway'):
            return 'transportation'

        # Entertainment
        elif tags.get('amenity') in ['theatre', 'cinema', 'arts_centre']:
            return 'entertainment'

        # Default fallback
        else:
            return 'other'

    def build_description(self, tags: Dict[str, str], osm_element: Dict[str, Any]) -> str:
        """Build comprehensive description from OSM tags"""
        name = tags.get('name', tags.get(
            'name:it', tags.get('name:en', 'Unnamed place')))
        description_parts = [name]

        # Add basic type information
        if tags.get('tourism'):
            description_parts.append(f"Type: {tags['tourism']}")
        elif tags.get('amenity'):
            description_parts.append(f"Type: {tags['amenity']}")
        elif tags.get('historic'):
            description_parts.append(f"Historic: {tags['historic']}")
        elif tags.get('shop'):
            description_parts.append(f"Shop: {tags['shop']}")

        # Add category for ChromaDB
        category = self.determine_category(tags)
        description_parts.append(category)

        # Add city information
        city = tags.get('addr:city', '')
        if city:
            description_parts.append(city)

        # Add specific attributes
        for key, value in tags.items():
            if key in ['cuisine', 'building', 'religion', 'denomination']:
                description_parts.append(f"{key}: {value}")

        return ' '.join(description_parts)

    def query_overpass_with_retry(self, query: str, max_retries: int = 3, base_delay: int = 5) -> Optional[Dict]:
        """Query Overpass API with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"  🔄 Attempt {attempt + 1}/{max_retries}")

                response = self.session.post(
                    self.overpass_url,
                    data=query,
                    timeout=60  # Increased timeout for problematic cities
                )

                if response.status_code == 200:
                    data = response.json()
                    print(
                        f"  ✅ Success: {len(data.get('elements', []))} elements found")
                    return data
                elif response.status_code == 429:  # Rate limited
                    delay = base_delay * (2 ** attempt)
                    print(f"  ⏳ Rate limited, waiting {delay}s...")
                    time.sleep(delay)
                else:
                    print(
                        f"  ❌ HTTP {response.status_code}: {response.text[:100]}")

            except requests.exceptions.Timeout:
                delay = base_delay * (2 ** attempt)
                print(f"  ⏰ Timeout, waiting {delay}s before retry...")
                time.sleep(delay)
            except Exception as e:
                print(f"  ❌ Error: {e}")
                time.sleep(base_delay)

        print(f"  💀 Failed after {max_retries} attempts")
        return None

    def load_city_data(self, city_name: str, overpass_query: str) -> bool:
        """Load data for a single city with comprehensive error handling"""
        print(f"\n🏛️  Loading {city_name}...")
        print(f"Query: {overpass_query[:100]}...")

        # Query Overpass API
        data = self.query_overpass_with_retry(overpass_query)
        if not data:
            return False

        elements = data.get('elements', [])
        if not elements:
            print(f"  ⚠️  No elements found for {city_name}")
            return False

        # Process places and insert into database
        places_inserted = 0
        places_in_chromadb = 0

        for element in elements:
            try:
                place_data = self.osm_to_place_data(element, city_name)

                # Skip places without names
                if not place_data['name'] or place_data['name'].startswith('Unnamed'):
                    continue

                # Create cache key
                cache_key = f"{city_name.lower()}_{place_data['name'].lower().replace(' ', '_')}"

                # Insert into PostgreSQL database
                insert_query = """
                    INSERT INTO place_cache (cache_key, place_data, city, place_name, country, priority_level, created_at, last_accessed, access_count)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), 0)
                    ON CONFLICT (cache_key) DO NOTHING
                """

                with self.pg_conn.cursor() as cursor:
                    cursor.execute(
                        insert_query,
                        (cache_key, json.dumps(place_data),
                         city_name, place_data['name'], 'Italy', 1)
                    )
                    if cursor.rowcount > 0:
                        places_inserted += 1

                # Commit the transaction
                self.pg_conn.commit()

                # Add to ChromaDB
                if self.collection and place_data.get('description'):
                    try:
                        self.collection.upsert(
                            documents=[place_data['description']],
                            metadatas=[{
                                'name': place_data['name'],
                                'city': city_name,
                                'category': place_data['category'],
                                'cache_key': cache_key
                            }],
                            ids=[cache_key]
                        )
                        places_in_chromadb += 1
                    except Exception as e:
                        print(
                            f"    ⚠️  ChromaDB error for {place_data['name']}: {e}")

            except Exception as e:
                print(f"    ❌ Error processing element: {e}")
                continue

        print(
            f"  ✅ {city_name}: {places_inserted} new places added to PostgreSQL")
        print(f"  📚 {city_name}: {places_in_chromadb} places indexed in ChromaDB")

        return places_inserted > 0

    def load_missing_cities(self):
        """Load the two missing cities with optimized queries"""

        # Define the two missing cities with more focused queries
        missing_cities = {
            "Padua": """
                [out:json][timeout:60];
                (
                  area["name"="Padova"][admin_level=8];
                )->.searchArea;
                (
                  node["tourism"~"attraction|museum|monument|artwork"](area.searchArea);
                  node["historic"]["name"](area.searchArea);
                  node["amenity"~"restaurant|cafe"](area.searchArea);
                  node["amenity"="place_of_worship"](area.searchArea);
                  way["tourism"~"attraction|museum|monument"](area.searchArea);
                  way["historic"]["name"](area.searchArea);
                  way["amenity"="place_of_worship"](area.searchArea);
                );
                out center meta;
            """,

            "Volterra": """
                [out:json][timeout:60];
                (
                  area["name"="Volterra"][admin_level=8];
                )->.searchArea;
                (
                  node["tourism"~"attraction|museum|monument|artwork"](area.searchArea);
                  node["historic"]["name"](area.searchArea);
                  node["amenity"~"restaurant|cafe"](area.searchArea);
                  node["amenity"="place_of_worship"](area.searchArea);
                  way["tourism"~"attraction|museum|monument"](area.searchArea);
                  way["historic"]["name"](area.searchArea);
                  way["amenity"="place_of_worship"](area.searchArea);
                );
                out center meta;
            """
        }

        print("🎯 COMPLETING MISSING CITIES")
        print("=" * 50)
        print("Loading Padua and Volterra with focused queries...")

        success_count = 0
        total_cities = len(missing_cities)

        for city_name, query in missing_cities.items():
            if self.load_city_data(city_name, query):
                success_count += 1

            # Brief pause between cities
            time.sleep(2)

        print(f"\n🎉 COMPLETION SUMMARY")
        print("=" * 30)
        print(f"✅ Successfully loaded: {success_count}/{total_cities} cities")
        print(
            f"🏛️  Cities completed: {', '.join(city for city, _ in missing_cities.items())}")

        if success_count == total_cities:
            print("🎊 All missing cities have been successfully loaded!")
        else:
            print(
                f"⚠️  {total_cities - success_count} cities still need attention")

        return success_count == total_cities


def main():
    """Main execution function"""
    print("🚀 ViamigoTravelAI - Complete Missing Cities")
    print("=" * 55)

    # Initialize loader and complete missing cities
    try:
        loader = MissingCitiesLoader()
        success = loader.load_missing_cities()

        if success:
            print("\n🎊 MISSION ACCOMPLISHED!")
            print("All 40 target Italian cities are now loaded")
            print("Ready for full AI Companion testing")
        else:
            print("\n🔄 Some cities may need manual attention")
            print("Consider alternative data sources for remaining cities")

        # Close database connection
        loader.pg_conn.close()
        print("🔌 Database connection closed")

        return success
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    main()

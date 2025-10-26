#!/usr/bin/env python3
"""
Add Smaller Italian Cities to Viamigo Travel AI Database
Uses Safe_Data_Loader to add tourism data for smaller Italian cities
"""

from Viamigo_Data_Loader_Fixed import ViaMigoDataLoader
import sys
import time
from typing import List

# Add the current directory to the path
sys.path.append('/workspaces/ViamigoTravelAI')


def add_smaller_italian_cities():
    """Add smaller Italian cities to the database using ViaMigoDataLoader"""

    # Priority list of smaller Italian cities to add
    priority_cities = [
        # Tuscany gems
        "Siena", "Pisa", "Lucca", "San Gimignano", "Cortona",
        "Montepulciano", "Montalcino",

        # Umbria treasures
        "Assisi", "Orvieto", "Gubbio", "Urbino",

        # Amalfi Coast
        "Positano", "Ravello",

        # Sicily
        "Taormina", "Cefalù",

        # Puglia
        "Matera", "Alberobello", "Lecce",

        # Emilia-Romagna
        "Parma", "Modena", "Ravenna", "Ferrara",

        # Veneto
        "Vicenza", "Treviso",

        # Northern Italy
        "Cremona", "Mantova",

        # Friuli-Venezia Giulia
        "Udine", "Trieste"
    ]

    print("🇮🇹 Adding Smaller Italian Cities to Viamigo Database")
    print("=" * 60)
    print(f"Total cities to process: {len(priority_cities)}")
    print()

    # Initialize the data loader
    try:
        loader = ViaMigoDataLoader(chroma_path="./chromadb_data")
        print("✅ ViaMigoDataLoader initialized")
    except Exception as e:
        print(f"❌ Failed to initialize loader: {e}")
        return    # Process each city
    success_count = 0
    error_count = 0

    for i, city in enumerate(priority_cities, 1):
        print(f"\n[{i}/{len(priority_cities)}] 🏙️ Processing {city}")
        print("-" * 40)

        try:
            # Load data for the city
            loader.load_city_data(city)
            print(f"✅ Successfully added {city}")
            success_count += 1

            # Add a small delay to be respectful to the API
            time.sleep(2)

        except Exception as e:
            print(f"❌ Failed to add {city}: {e}")
            error_count += 1
            # Continue with next city on error
            continue

    print("\n" + "=" * 60)
    print("🎉 Batch Processing Complete!")
    print(f"✅ Successfully added: {success_count} cities")
    print(f"❌ Failed: {error_count} cities")
    print(
        f"📊 Success rate: {(success_count / len(priority_cities) * 100):.1f}%")


def add_specific_cities(cities: List[str]):
    """Add specific cities to the database"""

    print(f"🇮🇹 Adding Specific Cities: {', '.join(cities)}")
    print("=" * 60)

    # Initialize the data loader
    try:
        loader = ViaMigoDataLoader(chroma_path="./chromadb_data")
        print("✅ ViaMigoDataLoader initialized")
    except Exception as e:
        print(f"❌ Failed to initialize loader: {e}")
        return

    for city in cities:
        print(f"\n🏙️ Processing {city}")
        print("-" * 30)

        try:
            loader.load_city_data(city)
            print(f"✅ Successfully added {city}")
            time.sleep(2)  # Be respectful to the API

        except Exception as e:
            print(f"❌ Failed to add {city}: {e}")


def verify_new_cities():
    """Verify that new cities were added successfully"""
    import psycopg2
    import os
    from dotenv import load_dotenv

    load_dotenv()

    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()

        # Count OSM cities
        cur.execute("""
            WITH osm_cities AS (
                SELECT SPLIT_PART(cache_key, ':', 2) as city
                FROM place_cache 
                WHERE cache_key LIKE 'osm:%'
            )
            SELECT city, COUNT(*)
            FROM osm_cities
            GROUP BY city
            ORDER BY COUNT(*) DESC
        """)
        osm_cities = cur.fetchall()

        cur.close()
        conn.close()

        print("\n🔍 Current OSM Cities in Database:")
        print("=" * 40)
        for city, count in osm_cities:
            print(f"   {city.title()}: {count:,} places")

        print(f"\nTotal OSM cities: {len(osm_cities)}")

    except Exception as e:
        print(f"❌ Error verifying cities: {e}")


if __name__ == "__main__":
    print("🚀 Viamigo Travel AI - City Data Expansion")
    print("=" * 60)

    # Option 1: Add a few high-priority cities first (for testing)
    test_cities = ["Siena", "Pisa", "Assisi"]

    print("Starting with high-priority cities for testing...")
    add_specific_cities(test_cities)

    # Verify the additions
    verify_new_cities()

    # Ask if user wants to continue with all cities
    print("\n" + "=" * 60)
    print("Test completed! Check the results above.")
    print("To add all remaining cities, uncomment the line below and run again:")
    print("# add_smaller_italian_cities()")

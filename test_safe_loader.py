"""
Test Safe Data Loader - Domestic Italian Cities Only
Quick test with 3 cities: Bergamo, Rome, Florence
"""

from Safe_Data_Loader import SafeTourismDataLoader
import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """
    Test loader with 3 domestic Italian cities
    """
    print("\n" + "="*70)
    print("🇮🇹 TESTING Safe Data Loader - Domestic Italian Cities")
    print("="*70 + "\n")

    # Check environment
    load_dotenv()
    if not os.getenv('DATABASE_URL'):
        print("❌ ERROR: DATABASE_URL not found in .env file")
        print("\n📝 Add to .env:")
        print("DATABASE_URL=postgresql://user:password@host:port/dbname")
        return

    print("✅ DATABASE_URL found")
    print("✅ Using OpenStreetMap (100% Safe)")
    print("✅ No API key required\n")

    # Initialize loader
    try:
        loader = SafeTourismDataLoader(chroma_path="./chromadb_data")
    except Exception as e:
        print(f"❌ Failed to initialize loader: {e}")
        return

    # Test cities (start small - 3 cities)
    test_cities = {
        "Bergamo": {
            "bbox": (45.67, 9.64, 45.72, 9.70),
            "description": "Your priority city - Città Alta medieval town"
        },
        "Rome": {
            # Smaller bbox for faster test
            "bbox": (41.88, 12.46, 41.92, 12.52),
            "description": "Capital - Colosseum area"
        },
        "Florence": {
            "bbox": (43.76, 11.24, 43.78, 11.27),  # Smaller bbox
            "description": "Renaissance city - Historic center"
        }
    }

    print(f"📍 Testing with {len(test_cities)} cities:\n")
    for city, info in test_cities.items():
        print(f"   • {city}: {info['description']}")
    print()

    # Track statistics
    total_places = 0
    successful_cities = 0

    # Load data for each city
    for city, info in test_cities.items():
        bbox = info['bbox']

        try:
            print(f"\n{'─'*70}")
            loader.load_city_data(
                city=city,
                bbox=bbox,
                load_attractions=True,
                load_restaurants=True
            )
            successful_cities += 1

            # Query count from database
            loader.pg_cursor.execute(
                "SELECT COUNT(*) FROM place_cache WHERE city = %s AND cache_key LIKE 'osm:%'",
                (city,)
            )
            city_count = loader.pg_cursor.fetchone()[0]
            total_places += city_count
            print(f"✅ {city}: {city_count} places loaded")

            # Brief pause between cities (respect OSM servers)
            import time
            time.sleep(2)

        except Exception as e:
            print(f"❌ Error loading {city}: {e}")
            continue

    # Close connections
    loader.close()

    # Final summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ Cities processed: {successful_cities}/{len(test_cities)}")
    print(f"✅ Total places loaded: {total_places}")
    print(
        f"✅ Average per city: {total_places//successful_cities if successful_cities > 0 else 0}")
    print(f"✅ Data source: OpenStreetMap (100% Safe)")
    print("="*70 + "\n")

    # Verification queries
    print("🔍 VERIFICATION:\n")

    # Verify Bergamo (your priority)
    import psycopg2
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    cur.execute("""
        SELECT place_name, place_data->>'description' as description
        FROM place_cache 
        WHERE city = 'Bergamo' 
        AND cache_key LIKE 'osm:%'
        LIMIT 5
    """)

    results = cur.fetchall()
    if results:
        print("📍 Sample Bergamo places:")
        for name, desc in results:
            desc_preview = (
                desc[:60] + '...') if desc and len(desc) > 60 else (desc or 'No description')
            print(f"   • {name}")
            print(f"     {desc_preview}\n")
    else:
        print("⚠️ No Bergamo places found yet")

    cur.close()
    conn.close()

    print("\n🎉 TEST COMPLETE!")
    print("\n💡 Next steps:")
    print("   1. Verify data in database")
    print("   2. Test with AI companion")
    print("   3. If successful, run full Safe_Data_Loader.py for all 10 cities\n")


if __name__ == "__main__":
    main()

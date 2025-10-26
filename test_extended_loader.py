"""
Test Extended Safe Data Loader - 3 Cities Only
Quick test to verify integration with existing PostgreSQL schema
"""

import time
from Extended_Safe_Data_Loader import ExtendedSafeTourismDataLoader
import sys
sys.path.append('/workspaces/ViamigoTravelAI')


def test_three_cities():
    """Test the extended loader with just 3 new cities"""
    print("🧪 TESTING Extended Safe Data Loader - 3 Cities")
    print("=" * 55)
    print("🎯 Testing: Pisa, Siena, Lecce")
    print("✅ Will verify PostgreSQL integration")
    print("✅ Will test ChromaDB semantic search")
    print()

    try:
        # Initialize loader
        loader = ExtendedSafeTourismDataLoader(chroma_path="./chromadb_data")
        print("✅ Loader initialized successfully")

        # Test cities (new ones not in your current 31)
        test_cities = {
            "Pisa": (43.69, 10.37, 43.74, 10.42),     # Tuscany - Leaning Tower
            "Siena": (43.30, 11.31, 43.34, 11.34),    # Tuscany - Medieval
            "Lecce": (40.34, 18.16, 40.38, 18.20),    # Puglia - Baroque
        }

        successful = 0

        for city, bbox in test_cities.items():
            print(f"\n📍 Loading {city}...")
            try:
                success = loader.load_city_data(
                    city=city,
                    bbox=bbox,
                    load_attractions=True,
                    load_restaurants=True,
                    load_hotels=True
                )

                if success:
                    successful += 1
                    print(f"✅ {city} loaded successfully")
                else:
                    print(f"⚠️ {city} had issues")

                time.sleep(3)  # Be nice to OpenStreetMap

            except Exception as e:
                print(f"❌ Error with {city}: {e}")

        # Close connections
        loader.close()

        print(f"\n🎉 TEST RESULTS:")
        print(f"✅ Successfully loaded: {successful}/3 cities")

        if successful == 3:
            print(f"✅ ALL TESTS PASSED!")
            print(f"🚀 Ready to run full Extended_Safe_Data_Loader.py for all 40 cities")
        elif successful > 0:
            print(f"⚠️ PARTIAL SUCCESS - {successful} cities loaded")
            print(f"💡 Check the issues above before full run")
        else:
            print(f"❌ NO CITIES LOADED")
            print(f"🔧 Check database connection and .env configuration")

        print(f"\n📊 Next step:")
        if successful >= 2:
            print(f"   python Extended_Safe_Data_Loader.py  # Load all 40 cities")
        else:
            print(f"   Fix the issues above first")

    except Exception as e:
        print(f"❌ Test initialization error: {e}")
        print(f"🔧 Check .env file and DATABASE_URL")


if __name__ == "__main__":
    test_three_cities()

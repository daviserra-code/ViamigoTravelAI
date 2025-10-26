#!/usr/bin/env python3
"""
Test script for image storage API
"""
import requests
import json
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_database_connection():
    """Test direct database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not found in environment")
            return False

        conn = psycopg2.connect(db_url)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as total_images,
                       COUNT(DISTINCT city) as cities_count,
                       SUM(LENGTH(img_bytes)) as total_size
                FROM attraction_images
            """)
            result = cur.fetchone()
            print(f"✅ Database connection successful:")
            print(f"   Total images: {result[0]}")
            print(f"   Cities: {result[1]}")
            print(f"   Total size: {result[2]} bytes")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_api_endpoint():
    """Test the API endpoint"""
    try:
        response = requests.get(
            'http://localhost:5000/api/images/stats', timeout=10)
        print(f"✅ API response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   API data: {json.dumps(data, indent=2)}")
        else:
            print(f"   API error: {response.text}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API connection refused - server not running")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing Image Storage System")
    print("=" * 50)

    # Test database first
    print("\n1. Testing direct database connection:")
    db_ok = test_database_connection()

    # Test API
    print("\n2. Testing API endpoint:")
    api_ok = test_api_endpoint()

    print("\n" + "=" * 50)
    print(f"Summary: DB={'✅' if db_ok else '❌'} API={'✅' if api_ok else '❌'}")

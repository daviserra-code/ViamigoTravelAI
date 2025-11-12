#!/usr/bin/env python3
"""
Fetch Duomo di Milano from Apify and cache in database
"""
import os
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()


def fetch_and_cache_duomo():
    """Fetch Duomo di Milano from Apify Google Places API and cache in DB"""

    # Apify Google Places API
    APIFY_TOKEN = os.getenv('APIFY_API_TOKEN')
    if not APIFY_TOKEN:
        print("❌ APIFY_API_TOKEN not found in .env")
        return False

    print("🔍 Fetching Duomo di Milano from Apify Google Places API...")

    # Apify actor run
    actor_url = "https://api.apify.com/v2/acts/nwua9Gu5YrADL7ZDj/runs"

    payload = {
        "queries": "Duomo di Milano, Milan, Italy",
        "maxReviews": 5,
        "language": "en"
    }

    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    # Start actor run
    response = requests.post(f"{actor_url}?token={APIFY_TOKEN}", json=payload)

    if response.status_code != 201:
        print(f"❌ Failed to start Apify actor: {response.status_code}")
        print(response.text)
        return False

    run_data = response.json()['data']
    run_id = run_data['id']

    print(f"⏳ Apify run started: {run_id}")
    print("   Waiting for results...")

    # Wait for completion (poll every 2 seconds for max 60 seconds)
    import time
    max_attempts = 30
    for attempt in range(max_attempts):
        time.sleep(2)

        status_response = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        )

        if status_response.status_code != 200:
            continue

        status = status_response.json()['data']['status']
        print(f"   Status: {status} ({attempt + 1}/{max_attempts})")

        if status == 'SUCCEEDED':
            break
    else:
        print("❌ Timeout waiting for Apify results")
        return False

    # Get dataset results
    dataset_id = run_data['defaultDatasetId']
    results_response = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    )

    if results_response.status_code != 200:
        print(f"❌ Failed to fetch results: {results_response.status_code}")
        return False

    results = results_response.json()

    if not results:
        print("❌ No results from Apify")
        return False

    duomo_data = results[0]
    print(f"✅ Found: {duomo_data.get('title', 'Unknown')}")

    # Extract data
    name = duomo_data.get('title', 'Duomo di Milano')
    address = duomo_data.get('address', 'Piazza del Duomo, Milan, Italy')
    lat = duomo_data.get('latitude')
    lng = duomo_data.get('longitude')
    rating = duomo_data.get('totalScore')
    reviews = duomo_data.get('reviewsCount', 0)
    description = duomo_data.get('description', '')
    category = duomo_data.get('categoryName', 'Cathedral')
    image_url = duomo_data.get('imageUrl')

    print(f"   Location: ({lat}, {lng})")
    print(f"   Rating: {rating}/5 ({reviews} reviews)")
    print(f"   Category: {category}")
    print(f"   Image: {image_url[:60] if image_url else 'None'}...")

    # Connect to database
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()

    # Insert into comprehensive_attractions
    print("\n📝 Inserting into comprehensive_attractions...")
    cursor.execute("""
        INSERT INTO comprehensive_attractions (
            name, city, category, description,
            latitude, longitude, image_url,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON CONFLICT DO NOTHING
        RETURNING id
    """, (name, 'Milan', category, description[:500], lat, lng, image_url))

    result = cursor.fetchone()
    if result:
        attraction_id = result[0]
        print(
            f"✅ Inserted into comprehensive_attractions (ID: {attraction_id})")
    else:
        print("ℹ️  Already exists in comprehensive_attractions")

    # Insert image into attraction_images
    if image_url:
        print("\n📝 Inserting into attraction_images...")
        cursor.execute("""
            INSERT INTO attraction_images (
                source, city, attraction_name,
                original_url, thumb_url,
                confidence_score, source_actor,
                fetched_at
            ) VALUES (
                'apify_google_places', 'Milan', %s,
                %s, %s, 0.95, 'google_places', NOW()
            )
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (name, image_url, image_url))

        result = cursor.fetchone()
        if result:
            image_id = result[0]
            print(f"✅ Inserted into attraction_images (ID: {image_id})")
        else:
            print("ℹ️  Already exists in attraction_images")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Duomo di Milano cached successfully!")
    return True


if __name__ == '__main__':
    success = fetch_and_cache_duomo()
    exit(0 if success else 1)

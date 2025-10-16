#!/usr/bin/env python3
"""
Cache Population Script for ViamigoTravelAI
Populates PostgreSQL cache with Apify data for common Italian cities
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
ADMIN_SECRET = os.getenv(
    'ADMIN_SECRET', 'change-this-secret-key-in-production')

# Common Italian cities to pre-populate
ITALIAN_CITIES = [
    'Bergamo',
    'Bologna',
    'Verona',
    'Firenze',
    'Pisa',
    'Siena',
    'Lucca',
    'Perugia',
    'Assisi',
    'Rimini',
    'Parma',
    'Modena',
    'Ravenna',
    'Ferrara',
    'Mantova',
    'Padova',
    'Vicenza',
    'Treviso',
    'Trento',
    'Bolzano',
    'Como',
    'Lecco',
    'Brescia',
    'Cremona',
    'Pavia'
]


def populate_city(city, delay=5):
    """Populate cache for a single city"""
    url = f'{BASE_URL}/admin/populate-city'
    headers = {'X-Admin-Secret': ADMIN_SECRET}
    payload = {
        'city': city,
        'categories': ['tourist_attraction', 'restaurant'],
        'force_refresh': False
    }

    print(f"\n{'='*60}")
    print(f"📍 Populating {city}...")
    print(f"{'='*60}")

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=180)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"   Duration: {data.get('duration_seconds', 0):.1f}s")

            for category, result in data.get('results', {}).items():
                if result.get('cached'):
                    print(
                        f"   {category}: {result['count']} places (already cached)")
                else:
                    print(
                        f"   {category}: {result['count']} places (newly cached)")

            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

    finally:
        if delay > 0:
            print(f"⏳ Waiting {delay}s before next city...")
            time.sleep(delay)


def populate_batch(cities, delay=5):
    """Populate multiple cities using batch endpoint"""
    url = f'{BASE_URL}/admin/populate-cities-batch'
    headers = {'X-Admin-Secret': ADMIN_SECRET}
    payload = {
        'cities': cities,
        'categories': ['tourist_attraction', 'restaurant'],
        'delay_seconds': delay
    }

    print(f"\n{'='*60}")
    print(f"🚀 Batch populating {len(cities)} cities...")
    print(f"{'='*60}\n")

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=3600)  # 1 hour timeout

        if response.status_code == 200:
            data = response.json()
            print(f"\n{'='*60}")
            print(f"✅ Batch completed!")
            print(
                f"   Total duration: {data.get('total_duration_seconds', 0):.1f}s")
            print(
                f"   ({data.get('total_duration_seconds', 0) / 60:.1f} minutes)")
            print(f"{'='*60}\n")

            for city, results in data.get('results', {}).items():
                print(f"{city}:")
                for category, result in results.items():
                    status = "cached" if result.get('cached') else "new"
                    print(
                        f"  - {category}: {result['count']} places ({status})")

            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def check_cache_status():
    """Check current cache status"""
    url = f'{BASE_URL}/admin/cache-status'
    headers = {'X-Admin-Secret': ADMIN_SECRET}

    print(f"\n{'='*60}")
    print(f"📊 Current Cache Status")
    print(f"{'='*60}\n")

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"Total cached cities: {data.get('total_cached_cities', 0)}")
            print(f"Total cache entries: {data.get('total_entries', 0)}\n")

            for city, categories in sorted(data.get('cities', {}).items()):
                print(f"{city.title()}:")
                for category, info in categories.items():
                    age = info.get('cache_age_hours', 0)
                    print(
                        f"  - {category}: {info['count']} places (age: {age:.1f}h)")

            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Populate PostgreSQL cache with Apify data')
    parser.add_argument('--city', help='Populate a single city')
    parser.add_argument('--batch', action='store_true',
                        help='Populate all Italian cities in batch')
    parser.add_argument('--status', action='store_true',
                        help='Check current cache status')
    parser.add_argument('--delay', type=int, default=5,
                        help='Delay between API calls (seconds)')
    parser.add_argument(
        '--cities-file', help='File with list of cities (one per line)')

    args = parser.parse_args()

    if args.status:
        check_cache_status()
    elif args.city:
        populate_city(args.city, delay=0)
    elif args.cities_file:
        with open(args.cities_file) as f:
            cities = [line.strip() for line in f if line.strip()]
        populate_batch(cities, delay=args.delay)
    elif args.batch:
        print(
            f"\n🚀 Starting batch population of {len(ITALIAN_CITIES)} Italian cities")
        print(
            f"⏱️  Estimated time: {len(ITALIAN_CITIES) * 2 * 40 / 60:.0f} minutes")
        print(
            f"    (2 categories × ~40s each × {len(ITALIAN_CITIES)} cities)\n")

        response = input("Continue? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            populate_batch(ITALIAN_CITIES, delay=args.delay)
        else:
            print("Cancelled.")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

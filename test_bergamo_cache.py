#!/usr/bin/env python3
"""
Test script to verify Bergamo uses PostgreSQL cache
"""
import inspect
from dynamic_routing import dynamic_router
from cost_effective_scraping import CostEffectiveDataProvider
from apify_integration import apify_travel
from flask_app import app
from dotenv import load_dotenv
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv()

# Create Flask app context

print("="*60)
print("🧪 TESTING BERGAMO CACHE USAGE")
print("="*60)

# Test 1: Verify cache exists
print("\n📊 TEST 1: Check PostgreSQL cache exists")

with app.app_context():
    from models import PlaceCache
with app.app_context():
    from models import PlaceCache
    bergamo_restaurants = PlaceCache.query.filter_by(
        cache_key='bergamo_restaurant').first()
    bergamo_attractions = PlaceCache.query.filter_by(
        cache_key='bergamo_tourist_attraction').first()

    if bergamo_restaurants:
        import json
        data = json.loads(bergamo_restaurants.place_data)
        print(f"✅ bergamo_restaurant cache found: {len(data)} places")
        print(f"   Sample: {data[0]['name'] if data else 'N/A'}")
    else:
        print("❌ bergamo_restaurant cache NOT found!")

    if bergamo_attractions:
        import json
        data = json.loads(bergamo_attractions.place_data)
        print(f"✅ bergamo_tourist_attraction cache found: {len(data)} places")
        print(f"   Sample: {data[0]['name'] if data else 'N/A'}")
    else:
        print("❌ bergamo_tourist_attraction cache NOT found!")

# Test 2: Test apify_travel.get_cached_places
print("\n📊 TEST 2: Test apify_travel.get_cached_places()")

cached_restaurants = apify_travel.get_cached_places('bergamo', 'restaurant')
print(
    f"Result: {len(cached_restaurants) if cached_restaurants else 0} restaurants from cache")
if cached_restaurants:
    print(f"✅ Cache retrieval works! Sample: {cached_restaurants[0]['name']}")
else:
    print("❌ Cache retrieval failed!")

cached_attractions = apify_travel.get_cached_places(
    'bergamo', 'tourist_attraction')
print(
    f"Result: {len(cached_attractions) if cached_attractions else 0} attractions from cache")
if cached_attractions:
    print(f"✅ Cache retrieval works! Sample: {cached_attractions[0]['name']}")
else:
    print("❌ Cache retrieval failed!")

# Test 3: Test CostEffectiveDataProvider
print("\n📊 TEST 3: Test CostEffectiveDataProvider.get_places_data()")

provider = CostEffectiveDataProvider()
print("\n🔍 Getting restaurants for Bergamo...")
restaurants = provider.get_places_data('bergamo', 'restaurant')
print(f"Result: {len(restaurants)} restaurants")
if restaurants:
    print(f"✅ Provider returned data! Sample: {restaurants[0]['name']}")
    print(f"   Source: {restaurants[0].get('source', 'unknown')}")
else:
    print("❌ Provider failed!")

print("\n🔍 Getting attractions for Bergamo...")
attractions = provider.get_places_data('bergamo', 'tourist_attraction')
print(f"Result: {len(attractions)} attractions")
if attractions:
    print(f"✅ Provider returned data! Sample: {attractions[0]['name']}")
    print(f"   Source: {attractions[0].get('source', 'unknown')}")
else:
    print("❌ Provider failed!")

# Test 4: Test dynamic routing would use cost-effective provider
print("\n📊 TEST 4: Check if Bergamo is in cost-effective cities list")

# Check the source code
source = inspect.getsource(dynamic_router._fallback_itinerary)
if 'bergamo' in source.lower():
    print("✅ Bergamo is explicitly mentioned in _fallback_itinerary")
else:
    # Check if it uses cost-effective for all cities
    if 'use_cost_effective_provider' in source:
        print("✅ Using use_cost_effective_provider list")
        # Try to find the list
        import re
        match = re.search(
            r'use_cost_effective_provider\s*=\s*\[(.*?)\]', source, re.DOTALL)
        if match:
            cities_str = match.group(1).lower()
            if 'bergamo' in cities_str:
                print("✅ ✅ BERGAMO IS IN THE LIST!")
            else:
                print("❌ Bergamo NOT in use_cost_effective_provider list")
    else:
        print("⚠️ Cannot determine if Bergamo uses cost-effective provider")

print("\n" + "="*60)
print("🏁 TEST COMPLETE")
print("="*60)

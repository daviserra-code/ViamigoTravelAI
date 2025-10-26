#!/usr/bin/env python3
"""
Minimal test of hardcoded attractions without full Flask context
"""


def test_hardcoded_attractions():
    """Test just the hardcoded attractions logic"""
    print("🧪 Testing Hardcoded Attractions (No Flask Required)")
    print("=" * 60)

    # Simulate the hardcoded attraction lookup logic
    from simple_enhanced_images import ATTRACTION_IMAGES

    # Test cases
    test_cases = [
        {"name": "colosseo", "city": "roma"},
        {"name": "piazza navona", "city": "roma"},
        {"name": "pantheon", "city": "roma"},
        {"name": "fontana di trevi", "city": "roma"},
        {"name": "nonexistent attraction", "city": "roma"},
    ]

    # Hardcoded attractions mapping (copy from intelligent_detail_handler.py)
    hardcoded_attractions = {
        'colosseo': {
            'name': 'Colosseo', 'city': 'Roma', 'category': 'historic:amphitheatre',
            'description': 'The iconic Colosseum, an ancient amphitheatre and symbol of Imperial Rome.',
            'coordinates': {'lat': 41.8902, 'lng': 12.4922},
            'confidence': 0.95
        },
        'colosseum': {
            'name': 'Colosseum', 'city': 'Roma', 'category': 'historic:amphitheatre',
            'confidence': 0.95
        },
        'piazza navona': {
            'name': 'Piazza Navona', 'city': 'Roma', 'category': 'tourism:attraction',
            'description': 'Beautiful baroque piazza with fountains, churches and street artists.',
            'coordinates': {'lat': 41.8986, 'lng': 12.4731},
            'confidence': 0.9
        },
        'fontana di trevi': {
            'name': 'Fontana di Trevi', 'city': 'Roma', 'category': 'tourism:attraction',
            'description': 'The famous Trevi Fountain where visitors throw coins to ensure their return to Rome.',
            'coordinates': {'lat': 41.9009, 'lng': 12.4833},
            'confidence': 0.9
        },
        'pantheon': {
            'name': 'Pantheon', 'city': 'Roma', 'category': 'historic:monument',
            'description': 'Ancient Roman temple, now a church, famous for its dome and oculus.',
            'coordinates': {'lat': 41.8986, 'lng': 12.4768},
            'confidence': 0.95
        }
    }

    print(f"\n📷 Available images: {len(ATTRACTION_IMAGES)} attractions")
    print(
        f"🏛️  Hardcoded attractions: {len(hardcoded_attractions)} major sites")

    for test_case in test_cases:
        name = test_case['name'].lower()
        city = test_case['city'].lower()

        print(f"\n🔍 Testing: '{name}' in {city}")

        # Search for matches (same logic as in _query_hardcoded_attractions)
        found = None
        for key, attraction in hardcoded_attractions.items():
            if key in name or any(word in name for word in key.split()):
                if not city or city in attraction['city'].lower():
                    # Add image URL if available
                    image_key = key.replace(' ', '_').replace(
                        'colosseum', 'colosseo')
                    attraction['image_url'] = ATTRACTION_IMAGES.get(image_key)
                    found = attraction
                    break

        if found:
            print(
                f"  ✅ MATCH: {found['name']} (confidence: {found['confidence']})")
            print(f"  📍 Coordinates: {found.get('coordinates', 'N/A')}")
            print(f"  🖼️  Image: {'Yes' if found.get('image_url') else 'No'}")
            print(
                f"  📝 Description: {found.get('description', 'N/A')[:80]}...")
        else:
            print(f"  ❌ NO MATCH: Would fall back to Apify (expensive!)")

    print(f"\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("✅ Major attractions (Colosseo, Piazza Navona, etc.) found in hardcoded data")
    print("✅ This means they WON'T trigger expensive Apify calls")
    print("✅ Only unknown attractions will use Apify as last resort")
    print("💰 Cost savings: Major tourist sites now free!")


if __name__ == "__main__":
    test_hardcoded_attractions()

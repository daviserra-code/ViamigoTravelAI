#!/usr/bin/env python3
"""
Hotels Integration Test Suite
Tests all hotels API endpoints and frontend integration
"""

import requests
import json

BASE_URL = "http://localhost:3000"


def test_api(endpoint, description):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {endpoint}")
    print('-'*60)

    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
            return True
        else:
            print(f"❌ Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


def test_static_file(path, description):
    """Test if static file is accessible"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Path: {path}")
    print('-'*60)

    try:
        response = requests.head(f"{BASE_URL}{path}", timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ File accessible")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(
                f"Content-Length: {response.headers.get('Content-Length')} bytes")
            return True
        else:
            print(f"❌ File not accessible")
            return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


def main():
    print("🏨 VIAMIGO HOTELS INTEGRATION TEST SUITE")
    print("="*60)

    results = []

    # Test 1: Hotel Availability API
    results.append(test_api(
        "/api/hotels/availability/Milan",
        "Hotel Availability Check - Milan"
    ))

    # Test 2: Hotel Search API
    results.append(test_api(
        "/api/hotels/search?city=Milan&limit=5",
        "Hotel Search - Milan (5 results)"
    ))

    # Test 3: Supported Cities API
    results.append(test_api(
        "/api/hotels/supported-cities",
        "Get Supported Cities List"
    ))

    # Test 4: Hotels Stats API
    results.append(test_api(
        "/api/hotels/stats/Milan",
        "Hotel Statistics - Milan"
    ))

    # Test 5: Check Milano (Italian name)
    results.append(test_api(
        "/api/hotels/availability/Milano",
        "Hotel Availability Check - Milano (Italian)"
    ))

    # Test 6: Hotels API JavaScript
    results.append(test_static_file(
        "/static/js/viamigo-hotels-api.js",
        "Hotels API JavaScript File"
    ))

    # Test 7: Hotels UI JavaScript
    results.append(test_static_file(
        "/static/js/viamigo-hotels-ui.js",
        "Hotels UI JavaScript File"
    ))

    # Test 8: Hotels Map JavaScript
    results.append(test_static_file(
        "/static/js/viamigo-hotels-map.js",
        "Hotels Map JavaScript File (Phase 2)"
    ))

    # Test 9: Hotels Map CSS
    results.append(test_static_file(
        "/static/css/viamigo-hotels-map.css",
        "Hotels Map CSS File (Phase 2)"
    ))

    # Test 10: Main Page
    results.append(test_static_file(
        "/",
        "Main Application Page"
    ))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED! Hotels integration is working correctly.")
    else:
        print(
            f"\n⚠️ {total - passed} test(s) failed. Please check the output above.")

    print('='*60)


if __name__ == "__main__":
    main()

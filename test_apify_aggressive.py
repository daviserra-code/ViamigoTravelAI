#!/usr/bin/env python3
"""
Aggressive test to force Apify calls and verify caching
Tests with completely fabricated attractions that won't be in any cache
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_unknown_attraction(name: str, attempt: int = 1):
    """Test with unknown attraction"""
    print(f"\n{'='*70}")
    print(f"Test {attempt}: {name}")
    print(f"{'='*70}")
    
    start = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/get_details",
            json={"context": name},
            timeout=60  # Allow time for Apify
        )
        
        elapsed = time.time() - start
        
        if response.ok:
            data = response.json()
            source = data.get('source', 'unknown')
            title = data.get('title', 'N/A')
            
            emoji = "💰" if source == "apify" else "🧠" if source == "chromadb" else "🗄️" if source == "comprehensive_attractions" else "🤖"
            speed = "🐌" if elapsed > 20 else "⏱️" if elapsed > 5 else "⚡"
            
            print(f"{emoji} Source: {source}")
            print(f"{speed} Time: {elapsed:.2f}s")
            print(f"📝 Title: {title}")
            
            if source == "apify":
                print(f"💰 APIFY CALLED! This will cost ~$0.02")
                print(f"💾 Should be cached for future requests")
            
            return {
                'name': name,
                'source': source,
                'time': elapsed,
                'title': title,
                'attempt': attempt
            }
        else:
            print(f"❌ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_caching_after_apify(name: str):
    """Test that Apify results are cached"""
    print(f"\n{'🔄'*35}")
    print(f"CACHING TEST: {name}")
    print(f"{'🔄'*35}")
    
    results = []
    
    # First request - might call Apify
    print("\n--- FIRST REQUEST (might be slow if Apify is called) ---")
    r1 = test_unknown_attraction(name, attempt=1)
    results.append(r1)
    
    if r1 and r1['source'] == 'apify':
        print(f"\n⏳ Waiting 3 seconds for cache to settle...")
        time.sleep(3)
        
        # Second request - should be cached
        print("\n--- SECOND REQUEST (should be fast from cache) ---")
        r2 = test_unknown_attraction(name, attempt=2)
        results.append(r2)
        
        if r2:
            if r2['source'] != 'apify':
                speedup = r1['time'] / r2['time'] if r2['time'] > 0 else 0
                print(f"\n✅ CACHING VERIFIED!")
                print(f"   1st request: Apify ({r1['time']:.2f}s)")
                print(f"   2nd request: {r2['source']} ({r2['time']:.2f}s)")
                print(f"   Speedup: {speedup:.1f}x faster!")
                print(f"   Cost saved: $0.02 per future request")
            else:
                print(f"\n❌ WARNING: Second request also called Apify!")
                print(f"   Caching may not be working properly")
    else:
        print(f"\n✅ First request didn't need Apify (served from {r1['source'] if r1 else 'error'})")
    
    return results

def main():
    """Run aggressive Apify tests"""
    print("\n" + "="*80)
    print("🧪 AGGRESSIVE APIFY TESTING")
    print("Testing with unknown attractions to verify Apify fallback and caching")
    print("="*80)
    
    all_results = []
    
    # Test 1: Completely random/unknown attractions
    print("\n\n📊 TEST 1: Random unknown places (should trigger Apify if not in ChromaDB)")
    print("-" * 80)
    
    unknown_places = [
        "Ristorante XYZ123 non esistente",
        "Bar Immaginario Torino 9999",
        "Museo Fantastico Milano ABC"
    ]
    
    for place in unknown_places:
        result = test_unknown_attraction(place)
        all_results.append(result)
        time.sleep(2)
    
    # Test 2: Specific caching test
    print("\n\n📊 TEST 2: Caching verification with specific attraction")
    print("-" * 80)
    
    # Use a real but potentially not-cached attraction
    test_place = "Caffè Mulassano Torino"
    cache_results = test_caching_after_apify(test_place)
    all_results.extend(cache_results)
    
    # Summary
    print("\n\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    sources = {}
    times_by_source = {}
    
    for r in all_results:
        if r:
            source = r['source']
            sources[source] = sources.get(source, 0) + 1
            if source not in times_by_source:
                times_by_source[source] = []
            times_by_source[source].append(r['time'])
    
    print("\n📈 Source Distribution:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        avg_time = sum(times_by_source[source]) / len(times_by_source[source])
        emoji = "💰" if source == "apify" else "🧠" if source == "chromadb" else "🗄️" if source == "comprehensive_attractions" else "🤖"
        print(f"  {emoji} {source:30s}: {count} requests - Avg: {avg_time:.2f}s")
    
    apify_count = sources.get('apify', 0)
    total = len([r for r in all_results if r])
    
    print(f"\n💰 Apify Calls: {apify_count}/{total}")
    print(f"💵 Estimated Cost: ${apify_count * 0.02:.2f}")
    
    if apify_count == 0:
        print(f"\n✅ NO APIFY CALLS! ChromaDB/DB handled everything.")
        print(f"   This means your database coverage is excellent.")
    else:
        print(f"\n⚠️  {apify_count} Apify calls were made.")
        print(f"   These attractions should now be cached for future requests.")
    
    # Save report
    report = {
        'test_date': datetime.now().isoformat(),
        'summary': {
            'total_requests': total,
            'apify_calls': apify_count,
            'estimated_cost': apify_count * 0.02,
            'source_distribution': sources
        },
        'results': all_results
    }
    
    filename = f"aggressive_apify_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Report saved to: {filename}")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

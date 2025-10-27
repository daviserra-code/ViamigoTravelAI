#!/usr/bin/env python3
"""
Test suite to analyze Apify usage and caching effectiveness
Tracks which data sources are being used and their performance
"""

import requests
import json
import time
from typing import Dict, List
from datetime import datetime

BASE_URL = "http://localhost:5000"


class ApifyPriorityTester:
    """Test and analyze detail endpoint source priorities"""

    def __init__(self):
        self.results = []

    def test_attraction(self, attraction_name: str, expected_source: str = None) -> Dict:
        """Test a single attraction and track results"""
        print(f"\n{'='*60}")
        print(f"🔍 Testing: {attraction_name}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            response = requests.post(
                f"{BASE_URL}/get_details",
                json={"context": attraction_name},
                timeout=45
            )

            elapsed = time.time() - start_time

            if response.ok:
                data = response.json()
                source = data.get('source', 'unknown')
                success = data.get('success', False)
                title = data.get('title', 'N/A')

                result = {
                    'attraction': attraction_name,
                    'source': source,
                    'time': round(elapsed, 2),
                    'success': success,
                    'title': title,
                    'expected_source': expected_source,
                    'timestamp': datetime.now().isoformat()
                }

                self.results.append(result)

                # Print result
                emoji = "✅" if success else "❌"
                speed_emoji = "⚡" if elapsed < 2 else "🐌" if elapsed > 10 else "⏱️"

                print(f"{emoji} Source: {source}")
                print(f"{speed_emoji} Time: {elapsed:.2f}s")
                print(f"📝 Title: {title}")

                if expected_source and source != expected_source:
                    print(f"⚠️  Expected {expected_source}, got {source}")

                return result
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return None

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Error: {e}")
            return {
                'attraction': attraction_name,
                'source': 'error',
                'time': round(elapsed, 2),
                'success': False,
                'error': str(e)
            }

    def test_repeat_request(self, attraction_name: str, times: int = 2):
        """Test the same attraction multiple times to verify caching"""
        print(f"\n{'🔄'*30}")
        print(f"Testing caching: {attraction_name} ({times} requests)")
        print(f"{'🔄'*30}")

        for i in range(times):
            print(f"\n--- Request {i+1}/{times} ---")
            result = self.test_attraction(attraction_name)
            if i == 0 and result:
                first_time = result['time']
                first_source = result['source']
            elif i > 0 and result:
                # Compare with first request
                speedup = first_time / \
                    result['time'] if result['time'] > 0 else 0
                if first_source == 'apify' and result['source'] != 'apify':
                    print(
                        f"✅ CACHING WORKS! {speedup:.1f}x faster, switched from Apify to {result['source']}")
                elif result['time'] < first_time * 0.5:
                    print(f"⚡ Faster on repeat: {speedup:.1f}x speedup")

            time.sleep(1)  # Small delay between requests

    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("\n" + "="*80)
        print("🧪 COMPREHENSIVE APIFY PRIORITY TEST")
        print("="*80)

        # Test 1: Well-known attractions (should be in DB)
        print("\n\n📊 TEST 1: Well-known attractions (Expected: comprehensive_attractions)")
        print("-" * 80)
        known_attractions = [
            "Mole Antonelliana",
            "Museo Egizio Torino",
            "Duomo di Milano",
            "Colosseo Roma",
            "Uffizi Firenze"
        ]

        for attraction in known_attractions:
            self.test_attraction(
                attraction, expected_source="comprehensive_attractions")
            time.sleep(0.5)

        # Test 2: Specific searches (might trigger ChromaDB)
        print("\n\n📊 TEST 2: Semantic searches (Expected: chromadb or comprehensive_attractions)")
        print("-" * 80)
        semantic_searches = [
            "Museo del Cinema Torino",
            "Galleria d'arte Torino",
            "Parco pubblico Milano"
        ]

        for search in semantic_searches:
            self.test_attraction(search, expected_source="chromadb")
            time.sleep(0.5)

        # Test 3: Obscure/unknown attractions (might trigger Apify or AI)
        print("\n\n📊 TEST 3: Obscure/unknown attractions (Expected: apify or ai)")
        print("-" * 80)
        obscure = [
            "Piccolo bar vicino Piazza Castello",
            "Negozio artigianale Via Roma Torino"
        ]

        for attraction in obscure:
            self.test_attraction(attraction, expected_source="apify")
            time.sleep(0.5)

        # Test 4: Caching effectiveness
        print("\n\n📊 TEST 4: Caching effectiveness (repeat requests)")
        print("-" * 80)
        self.test_repeat_request("Palazzo Reale Torino", times=2)

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate summary report"""
        print("\n\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)

        if not self.results:
            print("No results to analyze")
            return

        # Count by source
        source_counts = {}
        source_times = {}

        for result in self.results:
            source = result.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

            if source not in source_times:
                source_times[source] = []
            source_times[source].append(result.get('time', 0))

        # Print source distribution
        print("\n📈 Source Distribution:")
        print("-" * 80)
        total = len(self.results)
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            avg_time = sum(source_times[source]) / len(source_times[source])

            emoji = {
                'comprehensive_attractions': '🗄️',
                'chromadb': '🧠',
                'place_cache': '💾',
                'apify': '💰',
                'ai': '🤖',
                'database': '📊'
            }.get(source, '❓')

            print(
                f"{emoji} {source:30s}: {count:2d} requests ({percentage:5.1f}%) - Avg: {avg_time:.2f}s")

        # Calculate cost estimate
        apify_calls = source_counts.get('apify', 0)
        estimated_cost = apify_calls * 0.02
        print(
            f"\n💰 Estimated Apify Cost: ${estimated_cost:.2f} ({apify_calls} calls)")

        # Performance metrics
        all_times = [r.get('time', 0) for r in self.results]
        avg_time = sum(all_times) / len(all_times) if all_times else 0
        min_time = min(all_times) if all_times else 0
        max_time = max(all_times) if all_times else 0

        print(f"\n⏱️  Performance Metrics:")
        print(f"   Average response time: {avg_time:.2f}s")
        print(f"   Fastest response: {min_time:.2f}s")
        print(f"   Slowest response: {max_time:.2f}s")

        # Success rate
        successes = sum(1 for r in self.results if r.get('success'))
        success_rate = (successes / total) * 100 if total > 0 else 0
        print(f"\n✅ Success Rate: {success_rate:.1f}% ({successes}/{total})")

        # Save detailed results
        report_file = f"apify_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_requests': total,
                    'source_distribution': source_counts,
                    'apify_calls': apify_calls,
                    'estimated_cost': estimated_cost,
                    'avg_response_time': avg_time,
                    'success_rate': success_rate
                },
                'detailed_results': self.results
            }, f, indent=2)

        print(f"\n💾 Detailed report saved to: {report_file}")

        # Recommendations
        print("\n\n" + "="*80)
        print("💡 RECOMMENDATIONS")
        print("="*80)

        if apify_calls == 0:
            print(
                "✅ EXCELLENT: No Apify calls needed! All requests served from cache/DB.")
            print("   Current priority order is optimal.")
        elif apify_calls < total * 0.1:
            print(
                f"✅ GOOD: Only {apify_calls} Apify calls ({(apify_calls/total)*100:.1f}%)")
            print("   Most requests served from cache. Priority order is working well.")
        elif apify_calls < total * 0.3:
            print(
                f"⚠️  MODERATE: {apify_calls} Apify calls ({(apify_calls/total)*100:.1f}%)")
            print("   Consider enriching database with more attractions.")
        else:
            print(
                f"❌ HIGH: {apify_calls} Apify calls ({(apify_calls/total)*100:.1f}%)")
            print("   Database coverage may be insufficient. Consider:")
            print("   - Adding more attractions to comprehensive_attractions")
            print("   - Improving ChromaDB semantic search")
            print("   - Pre-caching popular attractions")

        if avg_time > 5:
            print(f"\n⚠️  Average response time is slow ({avg_time:.2f}s)")
            print("   This suggests Apify is being called frequently.")
        elif avg_time < 2:
            print(f"\n⚡ Average response time is excellent ({avg_time:.2f}s)")
            print("   Cache/DB sources are handling most requests.")

        print("\n" + "="*80 + "\n")


def main():
    """Main test runner"""
    tester = ApifyPriorityTester()

    # Run comprehensive test
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()

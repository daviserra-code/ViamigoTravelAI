#!/usr/bin/env python3
"""
Test script to verify the new priority system:
DB -> PlaceCache -> Hardcoded -> Apify (last resort)
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()


def test_priority_system():
    """Test the intelligent detail handler priority system"""
    print("🧪 Testing Priority System: DB -> Cache -> Hardcoded -> Apify")
    print("=" * 60)

    try:
        # Test cases that should hit different stages
        test_cases = [
            ("Colosseo Roma", "Should hit hardcoded (stage 3)"),
            ("Piazza Navona Roma", "Should hit hardcoded (stage 3)"),
            ("Pantheon Roma", "Should hit hardcoded (stage 3)"),
            ("Some random attraction", "Should eventually hit Apify or AI"),
        ]

        from intelligent_detail_handler import IntelligentDetailHandler
        handler = IntelligentDetailHandler()

        for context, expected in test_cases:
            print(f"\n🔍 Testing: '{context}' ({expected})")
            print("-" * 40)

            try:
                result = handler.get_details(context)

                source = result.get('source', 'unknown')
                name = result.get('name', 'N/A')
                confidence = result.get('confidence', 0)

                print(f"✅ Result: {name}")
                print(f"📊 Source: {source}")
                print(f"🎯 Confidence: {confidence}")

                # Check if expensive Apify was used
                if source == 'apify':
                    print("💰 WARNING: Expensive Apify was used!")
                elif source == 'hardcoded':
                    print("🎯 SUCCESS: Used hardcoded data (fast & free)")
                elif source == 'database':
                    print("🎯 SUCCESS: Used database (fast & free)")
                elif source == 'cache':
                    print("🎯 SUCCESS: Used cache (fast & free)")
                else:
                    print(f"ℹ️  Used {source} source")

            except Exception as e:
                print(f"❌ Test failed: {e}")

        print(f"\n" + "=" * 60)
        print("🎉 Priority system test completed!")

    except Exception as e:
        print(f"❌ Import/setup error: {e}")
        print(
            "Make sure you're running from the correct directory with Flask app available")


if __name__ == "__main__":
    test_priority_system()

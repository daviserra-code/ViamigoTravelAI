#!/usr/bin/env python3
"""
Demo script for the Comprehensive Attractions System
Shows the rich dataset from your custom Apify actor integrated with ViamigoTravelAI
"""
import requests
import json
from datetime import datetime


def test_comprehensive_system():
    """Test and demonstrate the comprehensive attractions system"""

    print("🎯 VIAMIGO TRAVEL AI - COMPREHENSIVE ATTRACTIONS DEMO")
    print("=" * 70)
    print(f"📅 Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Custom Apify Actor Integration: OSM + Wikidata + Wikimedia Commons")
    print()

    # Test 1: Database direct stats
    print("📊 DATABASE STATISTICS:")
    print("-" * 30)

    import psycopg2
    import os
    from dotenv import load_dotenv
    load_dotenv()

    db_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Get comprehensive stats
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE has_image = true) as with_images,
            COUNT(*) FILTER (WHERE wikidata_id IS NOT NULL) as with_wikidata,
            COUNT(*) FILTER (WHERE source_commons = true) as from_commons
        FROM comprehensive_attractions
    """)

    total, with_images, with_wikidata, from_commons = cur.fetchone()

    print(f"   ✅ Total Attractions: {total}")
    print(
        f"   📸 With Real Images: {with_images} ({with_images/total*100:.1f}%)")
    print(
        f"   🔗 With Wikidata: {with_wikidata} ({with_wikidata/total*100:.1f}%)")
    print(
        f"   📷 From Wikimedia Commons: {from_commons} ({from_commons/total*100:.1f}%)")

    # Get city breakdown
    cur.execute("""
        SELECT city, COUNT(*) as count, 
               COUNT(*) FILTER (WHERE has_image = true) as images
        FROM comprehensive_attractions 
        GROUP BY city 
        ORDER BY count DESC
    """)

    cities = cur.fetchall()
    print(f"\n🏙️  CITIES COVERAGE:")
    print("-" * 20)
    for city, count, images in cities:
        print(f"   {city}: {count} attractions ({images} with images)")

    # Sample high-quality attractions
    cur.execute("""
        SELECT name, category, attraction_type, wikidata_id, has_image
        FROM comprehensive_attractions 
        WHERE wikidata_id IS NOT NULL AND has_image = true
        ORDER BY name
        LIMIT 8
    """)

    samples = cur.fetchall()
    print(f"\n🏛️  SAMPLE HIGH-QUALITY ATTRACTIONS:")
    print("-" * 40)
    for name, category, attr_type, wikidata, has_image in samples:
        print(f"   • {name}")
        print(f"     Category: {category} | Type: {attr_type}")
        print(
            f"     Wikidata: {wikidata} | Image: {'✅' if has_image else '❌'}")
        print()

    # Image statistics
    cur.execute("""
        SELECT COUNT(*), AVG(confidence_score), SUM(CASE WHEN img_bytes IS NOT NULL THEN 1 ELSE 0 END)
        FROM attraction_images 
        WHERE source_actor = 'comprehensive'
    """)

    img_count, avg_conf, with_bytes = cur.fetchone()
    print(f"📸 IMAGE STATISTICS:")
    print("-" * 20)
    print(f"   Total Images Processed: {img_count}")
    print(f"   Average Confidence: {avg_conf:.2f}")
    print(f"   Successfully Downloaded: {with_bytes}")

    conn.close()

    print(f"\n🚀 INTEGRATION SUCCESS!")
    print(f"Your custom Apify actor has created the most comprehensive")
    print(f"Italian attractions dataset with real images, OSM data, and")
    print(f"Wikidata integration - far superior to previous datasets!")


def show_data_sources():
    """Show the data sources and their integration"""

    print("\n" + "=" * 70)
    print("🔍 DATA SOURCES & INTEGRATION")
    print("=" * 70)

    print("📍 OpenStreetMap (OSM):")
    print("   • Geographic coordinates")
    print("   • Category classification")
    print("   • Local names and tags")
    print("   • Tourist attraction markers")

    print("\n🔗 Wikidata:")
    print("   • Unique entity identifiers (Q-numbers)")
    print("   • Structured descriptions")
    print("   • Cross-language references")
    print("   • Authority data links")

    print("\n📷 Wikimedia Commons:")
    print("   • High-quality images")
    print("   • Proper licensing information")
    print("   • Creator attribution")
    print("   • Multiple image formats")

    print("\n⚙️  Custom Processing:")
    print("   • Confidence scoring algorithms")
    print("   • Image download & optimization")
    print("   • Deduplication by SHA256")
    print("   • PostgreSQL storage with JSONB")


def show_api_capabilities():
    """Show the API capabilities"""

    print("\n" + "=" * 70)
    print("🌐 API CAPABILITIES")
    print("=" * 70)

    endpoints = [
        ("/api/attractions/comprehensive/stats",
         "Overall statistics and breakdowns"),
        ("/api/attractions/comprehensive/search",
         "Search with filters (city, category, images, etc.)"),
        ("/api/attractions/comprehensive/<id>", "Detailed attraction information"),
        ("/api/attractions/comprehensive/categories",
         "List all categories and types"),
        ("/api/attractions/comprehensive/nearby",
         "Find attractions near coordinates"),
    ]

    for endpoint, description in endpoints:
        print(f"   🔗 {endpoint}")
        print(f"      {description}")
        print()


if __name__ == "__main__":
    test_comprehensive_system()
    show_data_sources()
    show_api_capabilities()

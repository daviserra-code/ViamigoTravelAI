#!/usr/bin/env python3
"""
Import Northern Italy tourist attractions dataset into PostgreSQL
Dataset: dataset_touristic-attractions_2025-11-06_20-38-13-921.json
Cities: Milano (521), Torino (360), Genova (600), Bologna (240), Pisa (600)
Total: 2,321 attractions with 553 images from Wikimedia Commons
"""

import json
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# Database connection
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_r9e2PGORqsAx@ep-ancient-morning-a6us6om6.us-west-2.aws.neon.tech/neondb?sslmode=require'
)


def load_dataset(filename):
    """Load JSON dataset"""
    print(f"📂 Loading dataset: {filename}")
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data)} attractions")
    return data


def import_to_comprehensive_attractions(data):
    """Import attractions to comprehensive_attractions table with deduplication"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("\n📊 Analyzing data before import...")

    # Count existing records
    cursor.execute("SELECT COUNT(*) FROM comprehensive_attractions")
    result = cursor.fetchone()
    existing_count = result[0] if result else 0
    print(f"   Existing records: {existing_count}")

    # Load existing (city, name) pairs to avoid duplicates
    print("   Loading existing attractions to check for duplicates...")
    cursor.execute(
        "SELECT LOWER(city), LOWER(name) FROM comprehensive_attractions")
    existing_pairs = set(cursor.fetchall())
    print(f"   Loaded {len(existing_pairs)} existing (city, name) pairs")

    # Also load existing OSM IDs to avoid OSM constraint violations
    cursor.execute(
        "SELECT osm_id, osm_type FROM comprehensive_attractions WHERE osm_id IS NOT NULL")
    existing_osm = set(cursor.fetchall())
    print(f"   Loaded {len(existing_osm)} existing OSM (id, type) pairs")

    # Prepare data for insertion with DISTINCT logic
    print("\n   Processing JSON data...")
    records_dict = {}  # Use dict to auto-deduplicate by (city, name)
    skipped = 0
    source_duplicates = 0

    for item in data:
        city = item.get('city')
        name = item.get('name')
        raw_name = item.get('rawName', name)
        category = item.get('category', 'attraction')
        description = item.get('description', '')

        # Get coordinates
        coords = item.get('coords', {})
        lat = coords.get('lat')
        lon = coords.get('lon')

        # Get image URLs
        image_data = item.get('image', {})
        thumb_url = image_data.get('thumbUrl')
        original_url = image_data.get('originalUrl')
        image_creator = image_data.get('creator', '')
        image_license = image_data.get('license', '')
        image_attribution = image_data.get('attribution', '')

        # Get metadata
        wikidata_id = item.get('wikidata')
        wikipedia = item.get('wikipedia')
        osm_id = item.get('osmId')
        osm_type = item.get('osmType')
        osm_tags = item.get('tags', {})

        # Source flags
        source_data = item.get('source', {})
        source_osm = source_data.get('osm', False)
        source_wikidata = source_data.get('wikidata', False)
        source_commons = source_data.get('commons', False)

        # Validate required fields
        if not all([city, name, lat, lon]):
            skipped += 1
            continue

        # Create unique key (case-insensitive)
        unique_key = (city.lower(), name.lower())

        # Check if already in database by name
        if unique_key in existing_pairs:
            continue

        # Check if OSM ID already exists (unique constraint)
        if osm_id and osm_type:
            osm_key = (osm_id, osm_type)
            if osm_key in existing_osm:
                continue

        # Check if duplicate in source data (keep first occurrence)
        if unique_key in records_dict:
            source_duplicates += 1
            continue

        # Store with unique key
        records_dict[unique_key] = (
            city,
            name,
            raw_name,
            description,
            category,
            float(lat),
            float(lon),
            osm_id,
            osm_type,
            json.dumps(osm_tags) if osm_tags else None,
            wikidata_id,
            wikipedia,
            bool(original_url or thumb_url),
            original_url or thumb_url,  # image_url (prefer original)
            thumb_url,
            original_url,
            image_creator,
            image_license,
            image_attribution,
            source_osm,
            source_wikidata,
            source_commons
        )

    values = list(records_dict.values())

    print(f"   Valid unique records to insert: {len(values)}")
    print(f"   Skipped (missing data): {skipped}")
    print(f"   Duplicates in source data: {source_duplicates}")
    print(
        f"   Already in database: {len(data) - skipped - source_duplicates - len(values)}")

    if not values:
        print("\n⚠️  No new records to insert!")
        cursor.close()
        conn.close()
        return

    # Bulk insert using execute_values for efficiency
    print(
        f"\n🚀 Bulk inserting {len(values)} records into comprehensive_attractions...")

    insert_query = """
        INSERT INTO comprehensive_attractions 
            (city, name, raw_name, description, category, 
             latitude, longitude, osm_id, osm_type, osm_tags,
             wikidata_id, wikipedia_url, has_image, image_url, 
             thumb_url, original_url, image_creator, image_license, 
             image_attribution, source_osm, source_wikidata, source_commons)
        VALUES %s
    """

    execute_values(cursor, insert_query, values, page_size=500)
    conn.commit()

    # Count after import
    cursor.execute("SELECT COUNT(*) FROM comprehensive_attractions")
    result = cursor.fetchone()
    new_count = result[0] if result else 0
    print(f"✅ Import complete!")
    print(f"   Records before: {existing_count}")
    print(f"   Records after: {new_count}")
    print(f"   New records added: {new_count - existing_count}")

    # Statistics by city
    print("\n📊 Records by city:")
    cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM comprehensive_attractions 
        WHERE city IN ('Milano', 'Torino', 'Genova', 'Bologna', 'Pisa')
        GROUP BY city 
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} attractions")

    # Statistics on images
    print("\n🖼️  Image coverage:")
    cursor.execute("""
        SELECT 
            city,
            COUNT(*) as total,
            COUNT(CASE WHEN has_image THEN 1 END) as with_images,
            ROUND(100.0 * COUNT(CASE WHEN has_image THEN 1 END) / COUNT(*), 1) as percentage
        FROM comprehensive_attractions 
        WHERE city IN ('Milano', 'Torino', 'Genova', 'Bologna', 'Pisa')
        GROUP BY city 
        ORDER BY total DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[2]}/{row[1]} ({row[3]}% with images)")

    cursor.close()
    conn.close()


def import_to_attraction_images(data):
    """Import high-quality images to attraction_images table with deduplication"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("\n📸 Importing to attraction_images table...")

    # Count existing
    cursor.execute(
        "SELECT COUNT(*) FROM attraction_images WHERE source = 'wikimedia_commons'")
    result = cursor.fetchone()
    existing_count = result[0] if result else 0
    print(f"   Existing Wikimedia Commons images: {existing_count}")

    # Load existing (city, name, source) tuples
    print("   Loading existing image records to check for duplicates...")
    cursor.execute("""
        SELECT LOWER(city), LOWER(attraction_name), source 
        FROM attraction_images 
        WHERE source = 'wikimedia_commons'
    """)
    existing_tuples = set(cursor.fetchall())
    print(f"   Loaded {len(existing_tuples)} existing image records")

    # Also load existing attraction_qid values (unique constraint)
    cursor.execute(
        "SELECT attraction_qid FROM attraction_images WHERE attraction_qid IS NOT NULL")
    existing_qids = set(row[0] for row in cursor.fetchall())
    print(f"   Loaded {len(existing_qids)} existing Wikidata QIDs")

    # Prepare image records with DISTINCT logic
    print("\n   Processing image data...")
    records_dict = {}  # Use dict to auto-deduplicate
    skipped = 0
    source_duplicates = 0

    for item in data:
        image_data = item.get('image', {})
        if not image_data.get('originalUrl'):
            skipped += 1
            continue  # Skip items without images

        city = item.get('city')
        name = item.get('name') or item.get('rawName')

        # Get coordinates
        coords = item.get('coords', {})
        lat = coords.get('lat')
        lon = coords.get('lon')

        wikidata_id = item.get('wikidata')

        if not all([city, name, lat, lon]):
            skipped += 1
            continue

        # Create unique key (case-insensitive)
        unique_key = (city.lower(), name.lower(), 'wikimedia_commons')

        # Check if already in database by (city, name, source)
        if unique_key in existing_tuples:
            continue

        # Check if Wikidata QID already exists (unique constraint)
        if wikidata_id and wikidata_id in existing_qids:
            continue

        # Check if duplicate in source data
        if unique_key in records_dict:
            source_duplicates += 1
            continue

        records_dict[unique_key] = (
            'wikimedia_commons',  # source
            wikidata_id,  # attraction_qid
            city,  # city
            name,  # attraction_name
            image_data.get('license', ''),  # license
            image_data.get('licenseUrl', ''),  # license_url
            image_data.get('creator', ''),  # creator
            image_data.get('attribution', ''),  # attribution
            image_data.get('originalUrl'),  # original_url
            image_data.get('thumbUrl'),  # thumb_url
            1.0,  # confidence_score (high confidence for official images)
            wikidata_id,  # wikidata_id
        )

    values = list(records_dict.values())

    print(f"   Valid unique image records to insert: {len(values)}")
    print(f"   Skipped (no image or missing data): {skipped}")
    print(f"   Duplicates in source data: {source_duplicates}")
    print(
        f"   Already in database: {len([i for i in data if i.get('image', {}).get('originalUrl')]) - skipped - source_duplicates - len(values)}")

    if not values:
        print("\n⚠️  No new image records to insert!")
        cursor.close()
        conn.close()
        return

    # Bulk insert using execute_values
    print(f"\n🚀 Bulk inserting {len(values)} image records...")

    insert_query = """
        INSERT INTO attraction_images 
            (source, attraction_qid, city, attraction_name, license, 
             license_url, creator, attribution, original_url, thumb_url,
             confidence_score, wikidata_id)
        VALUES %s
    """

    execute_values(cursor, insert_query, values, page_size=500)
    conn.commit()

    # Count after
    cursor.execute(
        "SELECT COUNT(*) FROM attraction_images WHERE source = 'wikimedia_commons'")
    result = cursor.fetchone()
    new_count = result[0] if result else 0
    print(f"✅ Image import complete!")
    print(f"   Records before: {existing_count}")
    print(f"   Records after: {new_count}")
    print(f"   New images added: {new_count - existing_count}")

    # Statistics by city
    print("\n📸 Image statistics by city:")
    cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM attraction_images 
        WHERE source = 'wikimedia_commons'
        AND city IN ('Milano', 'Torino', 'Genova', 'Bologna', 'Pisa')
        GROUP BY city 
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} images")

    cursor.close()
    conn.close()


def main():
    """Main import process"""
    filename = 'dataset_touristic-attractions_2025-11-06_20-38-13-921.json'

    if not os.path.exists(filename):
        print(f"❌ Error: File not found: {filename}")
        sys.exit(1)

    print("🇮🇹 Northern Italy Tourist Attractions Import")
    print("=" * 60)

    # Load dataset
    data = load_dataset(filename)

    # Import to comprehensive_attractions
    import_to_comprehensive_attractions(data)

    # Import to attraction_images
    import_to_attraction_images(data)

    print("\n" + "=" * 60)
    print("✅ Import completed successfully!")
    print("\n💡 The new attractions are now available for route planning.")
    print("   Milano routes will now have more diverse attractions!")


if __name__ == '__main__':
    main()

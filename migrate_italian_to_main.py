#!/usr/bin/env python3
"""
🇮🇹 MIGRATE ITALIAN DATASET TO EXISTING COMPREHENSIVE_ATTRACTIONS TABLE
=====================================================================
Migrate the Italian tourism dataset from comprehensive_attractions_italy 
to the existing comprehensive_attractions table structure.
"""

import psycopg2
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_db_connection():
    """Get PostgreSQL database connection from Neon"""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in environment")
            return None

        print(f"🔗 Connecting to Neon PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to Neon PostgreSQL successfully")
        return conn
    except Exception as e:
        print(f"❌ Neon PostgreSQL connection failed: {e}")
        return None


def check_existing_tables(conn):
    """Check what tables exist and their structures"""
    cursor = conn.cursor()

    # Check if comprehensive_attractions_italy exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'comprehensive_attractions_italy'
        )
    """)

    italy_exists = cursor.fetchone()[0]
    print(f"{'✅' if italy_exists else '❌'} comprehensive_attractions_italy table exists: {italy_exists}")

    # Check if comprehensive_attractions exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'comprehensive_attractions'
        )
    """)

    main_exists = cursor.fetchone()[0]
    print(f"{'✅' if main_exists else '❌'} comprehensive_attractions table exists: {main_exists}")

    if italy_exists:
        cursor.execute("SELECT COUNT(*) FROM comprehensive_attractions_italy")
        italy_count = cursor.fetchone()[0]
        print(f"📊 comprehensive_attractions_italy has {italy_count:,} records")

    if main_exists:
        cursor.execute("SELECT COUNT(*) FROM comprehensive_attractions")
        main_count = cursor.fetchone()[0]
        print(f"📊 comprehensive_attractions has {main_count:,} records")

    return italy_exists, main_exists


def create_comprehensive_table(conn):
    """Create the main comprehensive_attractions table if it doesn't exist"""
    cursor = conn.cursor()

    # First, check if table exists and modify columns if needed
    cursor.execute("""
        SELECT column_name, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'comprehensive_attractions' 
        AND column_name IN ('name', 'image_creator', 'image_license')
    """)

    existing_columns = dict(cursor.fetchall())

    # Extend field lengths if table exists but columns are too short
    if existing_columns:
        if existing_columns.get('name', 0) < 1000:
            cursor.execute(
                "ALTER TABLE comprehensive_attractions ALTER COLUMN name TYPE VARCHAR(1000)")
            print("✅ Extended name column to VARCHAR(1000)")

        if existing_columns.get('image_creator') and existing_columns.get('image_creator', 0) < 500:
            cursor.execute(
                "ALTER TABLE comprehensive_attractions ALTER COLUMN image_creator TYPE TEXT")
            print("✅ Extended image_creator column to TEXT")

        if existing_columns.get('image_license') and existing_columns.get('image_license', 0) < 200:
            cursor.execute(
                "ALTER TABLE comprehensive_attractions ALTER COLUMN image_license TYPE VARCHAR(200)")
            print("✅ Extended image_license column to VARCHAR(200)")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS comprehensive_attractions (
        id SERIAL PRIMARY KEY,
        city VARCHAR(100) NOT NULL,
        name VARCHAR(1000) NOT NULL,
        description TEXT,
        category VARCHAR(100),
        attraction_type VARCHAR(100),
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        osm_id BIGINT,
        wikidata_id VARCHAR(50),
        wikipedia_url TEXT,
        has_image BOOLEAN DEFAULT FALSE,
        thumb_url TEXT,
        image_license VARCHAR(200),
        image_creator TEXT,
        source_osm BOOLEAN DEFAULT FALSE,
        source_wikidata BOOLEAN DEFAULT FALSE,
        source_commons BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_comprehensive_city ON comprehensive_attractions(city);
    CREATE INDEX IF NOT EXISTS idx_comprehensive_category ON comprehensive_attractions(category);
    CREATE INDEX IF NOT EXISTS idx_comprehensive_coords ON comprehensive_attractions(latitude, longitude);
    CREATE INDEX IF NOT EXISTS idx_comprehensive_images ON comprehensive_attractions(thumb_url) WHERE thumb_url IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_comprehensive_wikidata ON comprehensive_attractions(wikidata_id) WHERE wikidata_id IS NOT NULL;
    """

    cursor.execute(create_table_sql)
    conn.commit()
    print("✅ Created/verified comprehensive_attractions table with indexes")


def migrate_italian_data(conn):
    """Migrate data from comprehensive_attractions_italy to comprehensive_attractions"""
    cursor = conn.cursor()

    # Clear any existing Italian data to avoid duplicates
    cursor.execute("""
        DELETE FROM comprehensive_attractions 
        WHERE city IN (
            SELECT DISTINCT city FROM comprehensive_attractions_italy
        )
    """)

    deleted_count = cursor.rowcount
    print(
        f"🧹 Deleted {deleted_count} existing Italian records from comprehensive_attractions")

    # Extend image_creator to TEXT if it's still VARCHAR(500)
    cursor.execute(
        "ALTER TABLE comprehensive_attractions ALTER COLUMN image_creator TYPE TEXT")
    print("✅ Extended image_creator column to TEXT")

    # Migrate data with deduplication and conflict handling
    migrate_sql = """
    INSERT INTO comprehensive_attractions (
        city, name, raw_name, description, category, attraction_type,
        latitude, longitude, osm_id, osm_type, osm_tags, wikidata_id, wikipedia_url,
        has_image, image_url, thumb_url, original_url, image_license, image_creator, image_attribution,
        source_osm, source_wikidata, source_commons, created_at
    )
    WITH deduplicated AS (
        SELECT DISTINCT ON (osm_id, osm_type)
            LEFT(city, 100) as city,
            LEFT(name, 1000) as name,
            LEFT(raw_name, 500) as raw_name,
            description,
            LEFT(category, 100) as category,
            LEFT(attraction_type, 100) as attraction_type,
            latitude,
            longitude,
            osm_id,
            LEFT(osm_type, 20) as osm_type,
            osm_tags,
            LEFT(wikidata, 50) as wikidata,
            LEFT(wikipedia, 500) as wikipedia,
            CASE 
                WHEN image_original_url IS NOT NULL THEN true 
                ELSE false 
            END as has_image,
            LEFT(image_original_url, 1000) as image_url,
            LEFT(image_thumb_url, 1000) as thumb_url,
            LEFT(image_original_url, 1000) as original_url,
            LEFT(image_license, 200) as image_license,
            image_creator,
            image_attribution,
            source_osm,
            source_wikidata,
            source_commons,
            created_at
        FROM comprehensive_attractions_italy
        ORDER BY osm_id, osm_type, id
    )
    SELECT * FROM deduplicated
    WHERE NOT EXISTS (
        SELECT 1 FROM comprehensive_attractions ca 
        WHERE ca.osm_id = deduplicated.osm_id 
        AND ca.osm_type = deduplicated.osm_type
    )
    """

    cursor.execute(migrate_sql)
    migrated_count = cursor.rowcount
    conn.commit()

    print(
        f"✅ Migrated {migrated_count:,} Italian attractions to comprehensive_attractions")

    return migrated_count


def verify_migration(conn):
    """Verify the migration was successful"""
    cursor = conn.cursor()

    # Check total records
    cursor.execute("SELECT COUNT(*) FROM comprehensive_attractions")
    total_count = cursor.fetchone()[0]

    # Check Italian cities
    cursor.execute("""
        SELECT city, COUNT(*) 
        FROM comprehensive_attractions 
        WHERE city IN (
            SELECT DISTINCT city FROM comprehensive_attractions_italy
        )
        GROUP BY city 
        ORDER BY COUNT(*) DESC 
        LIMIT 10
    """)

    italian_cities = cursor.fetchall()

    # Check image statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE has_image = true) as with_images,
            COUNT(*) FILTER (WHERE wikidata_id IS NOT NULL) as with_wikidata,
            COUNT(*) FILTER (WHERE source_commons = true) as from_commons
        FROM comprehensive_attractions
        WHERE city IN (
            SELECT DISTINCT city FROM comprehensive_attractions_italy
        )
    """)

    stats = cursor.fetchone()

    print(f"\n📈 MIGRATION VERIFICATION:")
    print(
        f"🏛️  Total attractions in comprehensive_attractions: {total_count:,}")
    print(f"📊 Italian attractions: {stats[0]:,}")
    print(f"📸 With images: {stats[1]:,} ({stats[1]/stats[0]*100:.1f}%)")
    print(f"🔗 With Wikidata: {stats[2]:,} ({stats[2]/stats[0]*100:.1f}%)")
    print(f"📷 From Commons: {stats[3]:,} ({stats[3]/stats[0]*100:.1f}%)")

    print(f"\n🏙️  TOP ITALIAN CITIES:")
    for city, count in italian_cities:
        print(f"   {city}: {count:,} attractions")


def main():
    """Main execution function"""
    print(f"🇮🇹 ITALIAN DATASET MIGRATION")
    print(f"=" * 50)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        sys.exit(1)

    try:
        # Check existing tables
        italy_exists, main_exists = check_existing_tables(conn)

        if not italy_exists:
            print("❌ comprehensive_attractions_italy table doesn't exist")
            print("   Please run process_italian_dataset.py first")
            sys.exit(1)

        # Create main table if needed
        create_comprehensive_table(conn)

        # Migrate data
        migrated_count = migrate_italian_data(conn)

        # Verify migration
        verify_migration(conn)

        print(f"\n🎉 SUCCESS! Migrated {migrated_count:,} Italian attractions")
        print(f"💡 The data is now available through the existing comprehensive_attractions API")
        print(
            f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()

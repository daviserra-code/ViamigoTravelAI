#!/usr/bin/env python3
"""
🇮🇹 ITALIAN TOURISM DATASET PROCESSOR
===================================
Process the comprehensive Italian tourism dataset and integrate into PostgreSQL.
Similar to process_new_dataset.py but optimized for the Italian dataset structure.
"""

import json
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
        # Load DATABASE_URL from environment (should be Neon connection string)
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


def create_comprehensive_table(conn):
    """Create comprehensive attractions table with Italian dataset schema"""
    cursor = conn.cursor()

    # Drop existing table if needed
    cursor.execute("DROP TABLE IF EXISTS comprehensive_attractions_italy")

    create_table_sql = """
    CREATE TABLE comprehensive_attractions_italy (
        id SERIAL PRIMARY KEY,
        city VARCHAR(100) NOT NULL,
        name VARCHAR(500) NOT NULL,
        raw_name VARCHAR(500),
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        category VARCHAR(100),
        attraction_type VARCHAR(100),
        osm_id BIGINT,
        osm_type VARCHAR(20),
        wikidata VARCHAR(50),
        wikipedia TEXT,
        description TEXT,
        
        -- Image information
        image_thumb_url TEXT,
        image_original_url TEXT,
        image_creator TEXT,
        image_license VARCHAR(100),
        image_license_url TEXT,
        image_attribution TEXT,
        image_kv_key VARCHAR(100),
        
        -- Source tracking
        source_osm BOOLEAN DEFAULT FALSE,
        source_wikidata BOOLEAN DEFAULT FALSE,
        source_commons BOOLEAN DEFAULT FALSE,
        
        -- OSM tags (stored as JSONB for flexibility)
        osm_tags JSONB,
        
        -- Metadata
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX idx_comprehensive_italy_city ON comprehensive_attractions_italy(city);
    CREATE INDEX idx_comprehensive_italy_category ON comprehensive_attractions_italy(category);
    CREATE INDEX idx_comprehensive_italy_coords ON comprehensive_attractions_italy(latitude, longitude);
    CREATE INDEX idx_comprehensive_italy_images ON comprehensive_attractions_italy(image_original_url) WHERE image_original_url IS NOT NULL;
    CREATE INDEX idx_comprehensive_italy_wikidata ON comprehensive_attractions_italy(wikidata) WHERE wikidata IS NOT NULL;
    """

    cursor.execute(create_table_sql)
    conn.commit()
    print("✅ Created comprehensive_attractions_italy table with indexes")


def extract_attraction_type(category):
    """Extract attraction type from category"""
    if not category:
        return 'unknown'

    # Extract the main type after 'tourism:'
    if ':' in category:
        # Handle combined categories
        return category.split(':', 1)[1].split(';')[0]
    return category


def process_italian_dataset(file_path):
    """Process the Italian tourism dataset"""

    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return False

    try:
        # Create table
        create_comprehensive_table(conn)

        # Load and process data
        print(f"📂 Loading dataset from {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📊 Processing {len(data):,} attractions...")

        cursor = conn.cursor()
        processed = 0
        inserted = 0
        errors = 0

        insert_sql = """
        INSERT INTO comprehensive_attractions_italy (
            city, name, raw_name, latitude, longitude, category, attraction_type,
            osm_id, osm_type, wikidata, wikipedia, description,
            image_thumb_url, image_original_url, image_creator, image_license,
            image_license_url, image_attribution, image_kv_key,
            source_osm, source_wikidata, source_commons, osm_tags
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        batch_size = 100
        batch_data = []

        for item in data:
            try:
                processed += 1

                # Extract basic info
                city = item.get('city', 'Unknown')
                name = item.get('name', '')
                raw_name = item.get('rawName', name)

                # Coordinates
                coords = item.get('coords', {})
                latitude = coords.get('lat') if coords else None
                longitude = coords.get('lon') if coords else None

                # Category and type
                category = item.get('category', '')
                attraction_type = extract_attraction_type(category)

                # OSM data
                osm_id = item.get('osmId')
                osm_type = item.get('osmType')
                osm_tags = json.dumps(
                    item.get('tags', {})) if item.get('tags') else None

                # Wikidata/Wikipedia
                wikidata = item.get('wikidata')
                wikipedia = item.get('wikipedia')
                description = item.get('description', '')

                # Image data
                image = item.get('image', {})
                image_thumb_url = image.get(
                    'thumbUrl') if image.get('thumbUrl') else None
                image_original_url = image.get(
                    'originalUrl') if image.get('originalUrl') else None
                image_creator = image.get(
                    'creator') if image.get('creator') else None
                image_license = image.get(
                    'license') if image.get('license') else None
                image_license_url = image.get(
                    'licenseUrl') if image.get('licenseUrl') else None
                image_attribution = image.get(
                    'attribution') if image.get('attribution') else None
                image_kv_key = image.get(
                    'kvKey') if image.get('kvKey') else None

                # Source tracking
                source = item.get('source', {})
                source_osm = source.get('osm', False)
                source_wikidata = source.get('wikidata', False)
                source_commons = source.get('commons', False)

                # Prepare data for batch insert
                batch_data.append((
                    city, name, raw_name, latitude, longitude, category, attraction_type,
                    osm_id, osm_type, wikidata, wikipedia, description,
                    image_thumb_url, image_original_url, image_creator, image_license,
                    image_license_url, image_attribution, image_kv_key,
                    source_osm, source_wikidata, source_commons, osm_tags
                ))

                # Execute batch when full
                if len(batch_data) >= batch_size:
                    cursor.executemany(insert_sql, batch_data)
                    inserted += len(batch_data)
                    batch_data = []

                    if processed % 1000 == 0:
                        print(
                            f"🔄 Processed {processed:,} attractions, inserted {inserted:,}")
                        conn.commit()  # Commit every 1000 records

            except Exception as e:
                errors += 1
                if errors <= 10:  # Show first 10 errors
                    print(f"⚠️  Error processing item {processed}: {e}")

        # Insert remaining batch
        if batch_data:
            cursor.executemany(insert_sql, batch_data)
            inserted += len(batch_data)

        conn.commit()

        print(f"\n✅ PROCESSING COMPLETE!")
        print(f"📊 Total processed: {processed:,}")
        print(f"✅ Successfully inserted: {inserted:,}")
        print(f"⚠️  Errors: {errors}")

        # Generate statistics
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT city) as cities,
            COUNT(*) FILTER (WHERE image_original_url IS NOT NULL) as with_images,
            COUNT(*) FILTER (WHERE wikidata IS NOT NULL) as with_wikidata,
            COUNT(*) FILTER (WHERE source_commons = true) as from_commons,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) as with_coords
        FROM comprehensive_attractions_italy
        """)

        stats = cursor.fetchone()
        print(f"\n📈 DATABASE STATISTICS:")
        print(f"🏛️  Total attractions: {stats[0]:,}")
        print(f"🏙️  Cities: {stats[1]}")
        print(f"📸 With images: {stats[2]:,} ({stats[2]/stats[0]*100:.1f}%)")
        print(f"🔗 With Wikidata: {stats[3]:,} ({stats[3]/stats[0]*100:.1f}%)")
        print(f"📷 From Commons: {stats[4]:,} ({stats[4]/stats[0]*100:.1f}%)")
        print(
            f"🗺️  With coordinates: {stats[5]:,} ({stats[5]/stats[0]*100:.1f}%)")

        # Top cities
        cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM comprehensive_attractions_italy 
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT 10
        """)

        print(f"\n🏙️  TOP CITIES:")
        for city, count in cursor.fetchall():
            print(f"   {city}: {count:,} attractions")

        return True

    except Exception as e:
        print(f"❌ Error processing dataset: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if conn:
            conn.close()


def main():
    """Main execution function"""
    dataset_file = "dataset_tourism-it-attractions_2025-10-18_21-22-01-627.json"

    if not os.path.exists(dataset_file):
        print(f"❌ Dataset file not found: {dataset_file}")
        return

    print(f"🇮🇹 ITALIAN TOURISM DATASET PROCESSOR")
    print(f"=" * 50)
    print(f"📂 Processing: {dataset_file}")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success = process_italian_dataset(dataset_file)

    if success:
        print(f"\n🎉 SUCCESS! Italian tourism dataset integrated into PostgreSQL")
        print(
            f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n❌ FAILED to process Italian dataset")
        sys.exit(1)


if __name__ == "__main__":
    main()

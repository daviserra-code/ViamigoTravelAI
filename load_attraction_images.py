#!/usr/bin/env python3
"""
Quick test script to populate attraction_images table with sample Italian attraction images
"""
import os
import sys
import psycopg2
import requests
import hashlib
from pathlib import Path

# Read DATABASE_URL from .env file


def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    return line.strip().split('=', 1)[1].strip('"\'')
    return None


# Sample Italian attractions with Wikimedia Commons images
TEST_ATTRACTIONS = [
    {
        'city': 'Roma',
        'name': 'Colosseo',
        'qid': 'Q10285',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/800px-Colosseo_2020.jpg'
    },
    {
        'city': 'Milano',
        'name': 'Duomo di Milano',
        'qid': 'Q2043',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Milano_Duomo.jpg'
    },
    {
        'city': 'Venezia',
        'name': 'Basilica di San Marco',
        'qid': 'Q185692',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/b/b9/San_Marco_Square.jpg'
    },
    {
        'city': 'Firenze',
        'name': 'Duomo di Firenze',
        'qid': 'Q756346',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/f/fc/Firenze_-_Duomo_-_Facciata.jpg'
    },
    {
        'city': 'Napoli',
        'name': 'Vesuvio',
        'qid': 'Q8969',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/2/24/Mount_Vesuvius_from_Sorrento.jpg'
    }
]


def main():
    print('🚀 ViamigoTravelAI - Attraction Images Loader')
    print('=' * 50)

    # Load database URL
    db_url = load_env()
    if not db_url:
        print('❌ DATABASE_URL not found in .env file')
        return

    print(f'🔗 Connecting to database: {db_url[:30]}...')

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        print('✅ Database connected successfully')

        # Create table if not exists
        schema_sql = """
        CREATE TABLE IF NOT EXISTS attraction_images (
          id BIGSERIAL PRIMARY KEY,
          source VARCHAR(32) NOT NULL,
          source_id TEXT,
          attraction_qid TEXT,
          city TEXT,
          attraction_name TEXT,
          license TEXT,
          license_url TEXT,
          creator TEXT,
          attribution TEXT,
          original_url TEXT,
          thumb_url TEXT,
          fetched_at TIMESTAMPTZ DEFAULT now(),
          img_bytes BYTEA,
          mime_type TEXT,
          width INT,
          height INT,
          sha256 TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_attraction_images_city ON attraction_images (LOWER(city));
        CREATE UNIQUE INDEX IF NOT EXISTS uq_attraction_imgs_source_sid ON attraction_images (source, source_id);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_attraction_imgs_qid ON attraction_images (attraction_qid);
        """

        with conn.cursor() as cur:
            cur.execute(schema_sql)
        print('📊 Database schema ensured')

        # Insert sample attractions
        insert_sql = """
        INSERT INTO attraction_images (
            source, source_id, attraction_qid, city, attraction_name, 
            original_url, thumb_url, img_bytes, mime_type, sha256
        ) VALUES (
            %(source)s, %(source_id)s, %(attraction_qid)s, %(city)s, %(attraction_name)s,
            %(original_url)s, %(thumb_url)s, %(img_bytes)s, %(mime_type)s, %(sha256)s
        )
        ON CONFLICT (source, source_id) DO NOTHING
        """

        inserted_count = 0
        for attraction in TEST_ATTRACTIONS:
            print(
                f'📥 Processing {attraction["name"]} in {attraction["city"]}...')

            try:
                # Download image
                headers = {
                    'User-Agent': 'ViamigoTravelAI/1.0 (dev@viamigo.ai)'}
                response = requests.get(
                    attraction['image_url'], headers=headers, timeout=30)
                response.raise_for_status()

                img_bytes = response.content
                mime_type = response.headers.get('Content-Type', 'image/jpeg')
                sha256_hash = hashlib.sha256(img_bytes).hexdigest()

                # Insert into database
                source_id = f'viamigo_{attraction["name"].lower().replace(" ", "_")}'.replace(
                    "'", "")
                row = {
                    'source': 'wikimedia',
                    'source_id': source_id,
                    'attraction_qid': attraction['qid'],
                    'city': attraction['city'],
                    'attraction_name': attraction['name'],
                    'original_url': attraction['image_url'],
                    'thumb_url': attraction['image_url'],
                    'img_bytes': psycopg2.Binary(img_bytes),
                    'mime_type': mime_type,
                    'sha256': sha256_hash
                }

                with conn.cursor() as cur:
                    cur.execute(insert_sql, row)

                print(
                    f'✅ Inserted {attraction["name"]} ({len(img_bytes):,} bytes)')
                inserted_count += 1

            except Exception as e:
                print(f'❌ Failed to process {attraction["name"]}: {e}')

        # Show results
        with conn.cursor() as cur:
            cur.execute("""
                SELECT city, COUNT(*) as count, 
                       MIN(attraction_name) as sample_attraction,
                       SUM(LENGTH(img_bytes)) as total_bytes
                FROM attraction_images 
                GROUP BY city 
                ORDER BY city
            """)
            results = cur.fetchall()

        print('\n📊 FINAL RESULTS:')
        print('-' * 50)
        total_images = 0
        total_size = 0
        for city, count, sample, size in results:
            print(f'{city}: {count} images, {size:,} bytes (e.g., {sample})')
            total_images += count
            total_size += size

        print('-' * 50)
        print(
            f'TOTAL: {total_images} images, {total_size:,} bytes ({total_size/1024/1024:.1f} MB)')
        print(f'✅ Successfully inserted {inserted_count} new images')

        conn.close()
        print('\n🎉 Attraction images loading completed!')

    except Exception as e:
        print(f'❌ Error: {e}')


if __name__ == '__main__':
    main()

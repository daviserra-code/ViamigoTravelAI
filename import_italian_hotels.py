"""
Efficient Italian Hotels Importer from HuggingFace
Only downloads and processes Italian hotel data (no 8.7GB download!)

Strategy: Stream dataset and filter for Italy only, avoiding full download

Author: Viamigo Development Team
Date: November 7, 2025
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from datasets import load_dataset
from collections import defaultdict
import json


class ItalianHotelsImporter:
    """Import only Italian hotels from HuggingFace dataset"""

    def __init__(self):
        self.db_url = os.environ.get(
            'DATABASE_URL',
            'postgresql://neondb_owner:npg_r9e2PGORqsAx@ep-ancient-morning-a6us6om6.us-west-2.aws.neon.tech/neondb?sslmode=require'
        )

        # Target Italian cities
        self.target_cities = {
            'Milan': ['Milan', 'Milano'],
            'Rome': ['Rome', 'Roma'],
            'Florence': ['Florence', 'Firenze'],
            'Venice': ['Venice', 'Venezia'],
            'Turin': ['Turin', 'Torino'],
            'Bologna': ['Bologna'],
            'Genoa': ['Genoa', 'Genova'],
            'Naples': ['Naples', 'Napoli'],
            'Verona': ['Verona'],
            'Pisa': ['Pisa'],
            'Siena': ['Siena'],
            'Palermo': ['Palermo'],
            'Catania': ['Catania']
        }

    def get_connection(self):
        """Create database connection"""
        return psycopg2.connect(self.db_url)

    def load_existing_hotels(self):
        """Load existing hotels from database to avoid duplicates"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT LOWER(hotel_name), city FROM hotel_reviews WHERE country = 'Italy' GROUP BY LOWER(hotel_name), city;"
        cursor.execute(query)

        existing = set()
        for row in cursor.fetchall():
            existing.add((row[0], row[1]))  # (hotel_name_lower, city)

        cursor.close()
        conn.close()

        print(
            f"✅ Loaded {len(existing)} existing Italian hotels from database")
        return existing

    def extract_italian_hotels(self, max_records=None):
        """
        Extract ONLY Italian hotels from HuggingFace dataset using streaming
        This avoids downloading the full 8.7GB dataset!

        Args:
            max_records: Maximum number of TOTAL records to scan (None = all 21M)

        Returns:
            Dict of Italian hotels by city with aggregated review data
        """
        print(f"🔍 Loading HuggingFace Hotels Reviews dataset in STREAMING mode...")
        print(f"   (This avoids downloading the full 8.7GB!)")

        # Use streaming=True to avoid full download
        ds = load_dataset("guyhadad01/Hotels_reviews",
                          split="train", streaming=True)

        hotels_data = defaultdict(lambda: {
            'total_reviews': 0,
            'ratings_sum': 0.0,
            'sample_reviews': []  # Store a few sample reviews
        })

        # Map city variants to normalized names
        target_city_variants = {}
        for normalized, variants in self.target_cities.items():
            for variant in variants:
                target_city_variants[variant] = normalized

        count = 0
        italian_count = 0

        print(f"📥 Streaming dataset and filtering for Italy...")
        print(
            f"   Max records to scan: {max_records if max_records else 'ALL 21+ million'}")

        for record in ds:
            count += 1

            if max_records and count > max_records:
                break

            # Progress every 100K records
            if count % 100000 == 0:
                print(
                    f"   Scanned {count:,} records → Found {italian_count:,} Italian hotel reviews ({len(hotels_data)} unique hotels)...")

            # EARLY FILTER: Skip non-Italian records immediately
            if record['County'] != 'Italy':
                continue

            italian_count += 1

            # Get city and normalize
            city_in_dataset = record['City']
            normalized_city = target_city_variants.get(city_in_dataset)

            # If city not in our target list, still include it (expand coverage)
            if not normalized_city:
                normalized_city = city_in_dataset  # Use original name

            hotel_name = record['Name']
            if not hotel_name:
                continue

            # Create hotel key
            hotel_key = (hotel_name, normalized_city)

            # Aggregate review data
            hotels_data[hotel_key]['total_reviews'] += 1
            hotels_data[hotel_key]['ratings_sum'] += record['rating'] or 0.0

            # Store a few sample reviews (for future features)
            if len(hotels_data[hotel_key]['sample_reviews']) < 5:
                hotels_data[hotel_key]['sample_reviews'].append({
                    'date': record['date'],
                    'rating': record['rating'],
                    'title': record['title']
                })

        print(f"\n✅ Streaming complete:")
        print(f"   - Total records scanned: {count:,}")
        print(f"   - Italian hotel reviews found: {italian_count:,}")
        print(f"   - Unique Italian hotels: {len(hotels_data)}")

        return hotels_data

    def prepare_hotel_records(self, hotels_data, existing_hotels):
        """
        Prepare hotel records for database insertion

        Args:
            hotels_data: Dict of hotels with aggregated review data
            existing_hotels: Set of (hotel_name_lower, city) tuples already in DB

        Returns:
            List of tuples ready for insertion
        """
        records = []
        skipped = 0

        for (hotel_name, city), data in hotels_data.items():
            # Skip if already exists
            if (hotel_name.lower(), city) in existing_hotels:
                skipped += 1
                continue

            # Calculate aggregated stats
            total_reviews = data['total_reviews']
            average_score = data['ratings_sum'] / \
                total_reviews if total_reviews > 0 else 0.0

            record = (
                hotel_name,                    # hotel_name
                # hotel_address (not in HF dataset)
                None,
                city,                          # city
                'Italy',                       # country
                None,                          # latitude (need geocoding)
                None,                          # longitude (need geocoding)
                round(average_score, 1),       # average_score
                total_reviews                  # total_reviews
            )

            records.append(record)

        print(
            f"\n📊 Prepared {len(records)} hotels for insertion ({skipped} skipped as duplicates)")
        return records

    def insert_hotels(self, records):
        """Insert hotel records into database"""
        if not records:
            print("⚠️ No new records to insert")
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO hotel_reviews (
            hotel_name, hotel_address, city, country,
            latitude, longitude,
            average_score, total_reviews
        ) VALUES %s
        ON CONFLICT DO NOTHING;
        """

        try:
            execute_values(cursor, insert_query, records, page_size=500)
            conn.commit()
            print(
                f"✅ Successfully inserted {len(records)} new Italian hotel records")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error inserting hotels: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def import_hotels(self, max_records=None):
        """
        Main import function - EFFICIENT STREAMING MODE

        Args:
            max_records: Maximum records to SCAN (not download!)
                        Recommended: 5000000 for ~238K Italian reviews
                        Use None to scan all 21M (takes longer but complete)
        """
        print("🏨 " + "="*70)
        print("🏨 Efficient Italian Hotels Importer (Streaming Mode)")
        print("🏨 " + "="*70)
        print("🏨 Strategy: Stream dataset and filter for Italy (no 8.7GB download!)")
        print("🏨 " + "="*70 + "\n")

        # Step 1: Load existing hotels
        existing_hotels = self.load_existing_hotels()

        # Step 2: Extract Italian hotels from HuggingFace (STREAMING!)
        hotels_data = self.extract_italian_hotels(max_records=max_records)

        # Step 3: Prepare records
        records = self.prepare_hotel_records(hotels_data, existing_hotels)

        # Step 4: Insert into database
        if records:
            self.insert_hotels(records)

        # Step 5: Summary
        print(f"\n" + "="*70)
        print(f"📊 Import Summary:")
        print(f"   - Total unique Italian hotels: {len(hotels_data)}")
        print(f"   - New hotels inserted: {len(records)}")
        print(
            f"   - Total reviews aggregated: {sum(d['total_reviews'] for d in hotels_data.values()):,}")
        print(f"="*70)

        # Show breakdown by city
        city_breakdown = defaultdict(lambda: {'hotels': 0, 'reviews': 0})
        for (hotel_name, city), data in hotels_data.items():
            city_breakdown[city]['hotels'] += 1
            city_breakdown[city]['reviews'] += data['total_reviews']

        print(f"\n🏙️ City Breakdown (Top 20):")
        sorted_cities = sorted(city_breakdown.items(
        ), key=lambda x: x[1]['reviews'], reverse=True)[:20]
        for city, stats in sorted_cities:
            print(
                f"   {city:20} - {stats['hotels']:4} hotels, {stats['reviews']:7,} reviews")


def main():
    """Main execution"""
    import sys

    importer = ItalianHotelsImporter()

    # Parse command line arguments
    max_records = None
    if len(sys.argv) > 1:
        try:
            max_records = int(sys.argv[1])
            print(f"⚠️ Scanning first {max_records:,} records only")
        except ValueError:
            print(f"❌ Invalid max_records argument: {sys.argv[1]}")
            print(f"Usage: python {sys.argv[0]} [max_records]")
            print(
                f"Example: python {sys.argv[0]} 5000000  # Scan 5M records (~238K Italian reviews)")
            sys.exit(1)
    else:
        print("ℹ️ No max_records specified. Will scan ALL 21+ million records.")
        print("ℹ️ Recommended: Start with 5000000 for testing (5M records)")
        print("ℹ️ This will still be MUCH faster than downloading 8.7GB!")
        response = input("\nContinue with full scan? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Import cancelled")
            print(f"💡 Try: python {sys.argv[0]} 5000000")
            sys.exit(0)

    # Run import
    importer.import_hotels(max_records=max_records)


if __name__ == "__main__":
    main()

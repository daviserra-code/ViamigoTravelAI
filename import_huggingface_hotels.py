"""
HuggingFace Hotels Dataset Importer for Viamigo
Imports hotels and reviews from guyhadad01/Hotels_reviews dataset

Dataset: 21+ million hotel reviews worldwide
Italian cities: Milan, Rome, Florence, Venice, Turin, Bologna, Genoa, Naples, etc.

Author: Viamigo Development Team
Date: November 7, 2025
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from datasets import load_dataset
from collections import defaultdict
import json
from datetime import datetime


class HuggingFaceHotelsImporter:
    """Import hotels from HuggingFace dataset to PostgreSQL"""

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
            'Naples': ['Naples', 'Napoli']
        }

    def get_connection(self):
        """Create database connection"""
        return psycopg2.connect(self.db_url)

    def load_existing_hotels(self):
        """Load existing hotels from database to avoid duplicates"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT LOWER(hotel_name), city FROM hotel_reviews GROUP BY LOWER(hotel_name), city;"
        cursor.execute(query)

        existing = set()
        for row in cursor.fetchall():
            existing.add((row[0], row[1]))  # (hotel_name_lower, city)

        cursor.close()
        conn.close()

        print(f"✅ Loaded {len(existing)} existing hotels from database")
        return existing

    def extract_hotels_from_dataset(self, max_records=None):
        """
        Extract hotels from HuggingFace dataset

        Args:
            max_records: Maximum number of records to process (None = all)

        Returns:
            Dict of hotels by city with aggregated review data
        """
        print(f"🔍 Loading HuggingFace Hotels Reviews dataset...")
        ds = load_dataset("guyhadad01/Hotels_reviews",
                          split="train", streaming=True)

        hotels_data = defaultdict(lambda: {
            'reviews': [],
            'total_reviews': 0,
            'ratings_sum': 0.0,
            'property_scores': defaultdict(list)
        })

        target_city_variants = {}
        for normalized, variants in self.target_cities.items():
            for variant in variants:
                target_city_variants[variant] = normalized

        count = 0
        italian_count = 0
        target_count = 0

        print(f"📥 Processing dataset (max_records={max_records or 'ALL'})...")

        for record in ds:
            count += 1

            if max_records and count > max_records:
                break

            if count % 100000 == 0:
                print(
                    f"   Processed {count:,} records ({italian_count:,} Italian, {target_count:,} target cities)...")

            # Filter for Italian hotels
            if record['County'] != 'Italy':
                continue

            italian_count += 1

            # Check if city is in our target list
            city_in_dataset = record['City']
            if city_in_dataset not in target_city_variants:
                continue

            target_count += 1
            normalized_city = target_city_variants[city_in_dataset]
            hotel_name = record['Name']

            # Create hotel key
            hotel_key = (hotel_name, normalized_city)

            # Aggregate review data
            hotels_data[hotel_key]['total_reviews'] += 1
            hotels_data[hotel_key]['ratings_sum'] += record['rating'] or 0.0

            # Parse property dict if available
            if record['property_dict']:
                try:
                    prop_dict = json.loads(record['property_dict'])
                    for key, value in prop_dict.items():
                        if value is not None:
                            hotels_data[hotel_key]['property_scores'][key].append(
                                float(value))
                except:
                    pass

            # Store review details (optional - for future sentiment analysis)
            hotels_data[hotel_key]['reviews'].append({
                'date': record['date'],
                'rating': record['rating'],
                'title': record['title'],
                'text': record['text']
            })

        print(f"\n✅ Processing complete:")
        print(f"   - Total records processed: {count:,}")
        print(f"   - Italian hotels: {italian_count:,}")
        print(f"   - Target cities: {target_count:,}")
        print(f"   - Unique hotels found: {len(hotels_data)}")

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

            # Note: HuggingFace dataset doesn't have coordinates
            # We'll need to geocode these or leave as NULL

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
            print("⚠️ No records to insert")
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
            print(f"✅ Successfully inserted {len(records)} hotel records")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error inserting hotels: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def import_hotels(self, max_records=None):
        """
        Main import function

        Args:
            max_records: Maximum records to process (None = all 21M records)
        """
        print("🏨 " + "="*70)
        print("🏨 HuggingFace Hotels Dataset Importer")
        print("🏨 " + "="*70)

        # Step 1: Load existing hotels
        existing_hotels = self.load_existing_hotels()

        # Step 2: Extract hotels from HuggingFace
        hotels_data = self.extract_hotels_from_dataset(max_records=max_records)

        # Step 3: Prepare records
        records = self.prepare_hotel_records(hotels_data, existing_hotels)

        # Step 4: Insert into database
        if records:
            self.insert_hotels(records)

        # Step 5: Summary
        print(f"\n" + "="*70)
        print(f"📊 Import Summary:")
        print(f"   - Total hotels processed: {len(hotels_data)}")
        print(f"   - New hotels inserted: {len(records)}")
        print(f"   - Cities covered: {', '.join(self.target_cities.keys())}")
        print(f"="*70)

        # Show breakdown by city
        city_breakdown = defaultdict(lambda: {'hotels': 0, 'reviews': 0})
        for (hotel_name, city), data in hotels_data.items():
            city_breakdown[city]['hotels'] += 1
            city_breakdown[city]['reviews'] += data['total_reviews']

        print(f"\n🏙️ City Breakdown:")
        for city in sorted(city_breakdown.keys()):
            stats = city_breakdown[city]
            print(
                f"   {city:15} - {stats['hotels']:3} hotels, {stats['reviews']:6} reviews")


def main():
    """Main execution"""
    import sys

    importer = HuggingFaceHotelsImporter()

    # Parse command line arguments
    max_records = None
    if len(sys.argv) > 1:
        try:
            max_records = int(sys.argv[1])
            print(
                f"⚠️ Processing only first {max_records:,} records (test mode)")
        except ValueError:
            print(f"❌ Invalid max_records argument: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("⚠️ WARNING: No max_records specified. Will process ALL 21+ million records!")
        print("⚠️ This will take several hours and download ~8.7GB of data.")
        print("⚠️ Recommended: Run with max_records first, e.g.: python script.py 500000")
        response = input("Continue with full import? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Import cancelled")
            sys.exit(0)

    # Run import
    importer.import_hotels(max_records=max_records)


if __name__ == "__main__":
    main()

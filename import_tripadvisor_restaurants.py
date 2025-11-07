#!/usr/bin/env python3
"""
Import TripAdvisor Milano restaurants into PostgreSQL
Dataset: dataset_tripadvisor_2025-11-06_20-50-42-762.json
Records: 10 highly-rated Milano restaurants
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
    print(f"📂 Loading TripAdvisor dataset: {filename}")
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data)} restaurants")
    return data


def import_restaurants(data):
    """Import restaurants to comprehensive_attractions table"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("\n📊 Analyzing data before import...")

    # Count existing Milano records
    cursor.execute(
        "SELECT COUNT(*) FROM comprehensive_attractions WHERE city = 'Milano'")
    result = cursor.fetchone()
    existing_milano = result[0] if result else 0
    print(f"   Existing Milano attractions: {existing_milano}")

    # Load existing (city, name) pairs to avoid duplicates
    print("   Loading existing Milano attractions...")
    cursor.execute(
        "SELECT LOWER(name) FROM comprehensive_attractions WHERE city = 'Milano'")
    existing_names = set(row[0] for row in cursor.fetchall())
    print(f"   Loaded {len(existing_names)} existing names")

    # Process TripAdvisor data
    print("\n   Processing TripAdvisor restaurants...")
    records_dict = {}
    skipped = 0
    duplicates = 0

    for item in data:
        name = item.get('name')
        lat = item.get('latitude')
        lon = item.get('longitude')

        if not all([name, lat, lon]):
            skipped += 1
            continue

        # Check for duplicates (case-insensitive)
        name_lower = name.lower()
        if name_lower in existing_names:
            duplicates += 1
            continue

        if name_lower in records_dict:
            continue

        # Build description from review tags
        review_tags = item.get('reviewTags', [])
        top_tags = [tag['text'] for tag in review_tags[:5]]
        tags_text = ', '.join(top_tags) if top_tags else ''

        # Get cuisines
        cuisines = item.get('cuisines', [])
        cuisines_text = ', '.join(cuisines) if cuisines else 'Restaurant'

        # Build rich description
        description = item.get('description', '')
        if not description:
            rating = item.get('rating')
            reviews = item.get('numberOfReviews', 0)
            description = f"{cuisines_text} restaurant in Milano"
            if rating:
                description += f" - Rated {rating}/5"
            if reviews:
                description += f" with {reviews:,} reviews"
            if tags_text:
                description += f". Popular for: {tags_text}"

        # Determine category
        establishment_types = item.get('establishmentTypes', [])
        if 'Fine Dining' in establishment_types:
            category = 'fine_dining'
        elif any(x in cuisines_text.lower() for x in ['pizza', 'fast food', 'street']):
            category = 'casual_dining'
        else:
            category = 'restaurant'

        # Get image
        image_url = None
        if 'image' in item and isinstance(item['image'], dict):
            image_url = item['image'].get(
                'original') or item['image'].get('large')
        elif 'photos' in item and item['photos']:
            first_photo = item['photos'][0]
            if isinstance(first_photo, dict):
                image_url = first_photo.get(
                    'original') or first_photo.get('large')

        # Get address
        address_obj = item.get('addressObj', {})
        street = address_obj.get('street1', '') or item.get('address', '')
        postal = address_obj.get('postalcode', '')

        records_dict[name_lower] = (
            'Milano',  # city
            name,  # name
            name,  # raw_name
            description,  # description
            category,  # category
            float(lat),  # latitude
            float(lon),  # longitude
            None,  # osm_id
            None,  # osm_type
            json.dumps({
                'tripadvisor_id': item.get('id'),
                'rating': item.get('rating'),
                'reviews': item.get('numberOfReviews'),
                'price_level': item.get('priceLevel'),
                'cuisines': cuisines,
                'phone': item.get('phone'),
                'website': item.get('website'),
                'address': street,
                'postal_code': postal,
                'review_tags': top_tags
            }),  # osm_tags (storing TripAdvisor data)
            None,  # wikidata_id
            item.get('webUrl'),  # wikipedia_url (using TripAdvisor URL)
            bool(image_url),  # has_image
            image_url,  # image_url
            image_url,  # thumb_url
            image_url,  # original_url
            'TripAdvisor',  # image_creator
            'TripAdvisor',  # image_license
            'Photo courtesy of TripAdvisor',  # image_attribution
            False,  # source_osm
            False,  # source_wikidata
            False,  # source_commons
        )

    values = list(records_dict.values())

    print(f"   Valid unique restaurants to insert: {len(values)}")
    print(f"   Skipped (missing data): {skipped}")
    print(f"   Already in database: {duplicates}")

    if not values:
        print("\n⚠️  No new restaurants to insert!")
        cursor.close()
        conn.close()
        return

    # Bulk insert
    print(
        f"\n🚀 Inserting {len(values)} restaurants into comprehensive_attractions...")

    insert_query = """
        INSERT INTO comprehensive_attractions 
            (city, name, raw_name, description, category, 
             latitude, longitude, osm_id, osm_type, osm_tags,
             wikidata_id, wikipedia_url, has_image, image_url, 
             thumb_url, original_url, image_creator, image_license, 
             image_attribution, source_osm, source_wikidata, source_commons)
        VALUES %s
    """

    execute_values(cursor, insert_query, values, page_size=100)
    conn.commit()

    # Count after
    cursor.execute(
        "SELECT COUNT(*) FROM comprehensive_attractions WHERE city = 'Milano'")
    result = cursor.fetchone()
    new_milano = result[0] if result else 0

    print(f"✅ Import complete!")
    print(f"   Milano attractions before: {existing_milano}")
    print(f"   Milano attractions after: {new_milano}")
    print(f"   New restaurants added: {new_milano - existing_milano}")

    # Show imported restaurants
    print(f"\n🍽️  Imported restaurants:")
    for i, (_, name, *_) in enumerate(values, 1):
        print(f"   {i}. {name}")

    cursor.close()
    conn.close()


def main():
    """Main import process"""
    filename = 'dataset_tripadvisor_2025-11-06_20-50-42-762.json'

    if not os.path.exists(filename):
        print(f"❌ Error: File not found: {filename}")
        sys.exit(1)

    print("🍽️  TripAdvisor Milano Restaurants Import")
    print("=" * 60)

    # Load dataset
    data = load_dataset(filename)

    # Import restaurants
    import_restaurants(data)

    print("\n" + "=" * 60)
    print("✅ Import completed successfully!")
    print("\n💡 The new restaurants are now available for Milano routes.")


if __name__ == '__main__':
    main()

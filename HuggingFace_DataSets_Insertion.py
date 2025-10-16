"""
Load Hugging Face Hotel Reviews dataset into PostgreSQL
Dataset: 515k European Hotel Reviews
Purpose: Populate hotel data for RAG/cache with real reviews
"""

from datasets import load_dataset
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# 1. Load Hugging Face dataset
print("📊 Loading Hotel Reviews dataset...")
print("Dataset: 515k European Hotel Reviews")
print("Source: Dricz/515k-Hotel-Reviews-In-Europe")
print("🇮🇹 Filtering for ITALIAN hotels only")
print()

# Italian cities and identifiers
ITALIAN_CITIES = [
    'Rome', 'Roma', 'Milan', 'Milano', 'Florence', 'Firenze',
    'Venice', 'Venezia', 'Naples', 'Napoli', 'Turin', 'Torino',
    'Bologna', 'Genoa', 'Genova', 'Verona', 'Pisa', 'Bergamo',
    'Padua', 'Padova', 'Sicily', 'Sicilia', 'Siena', 'Palermo',
    'Catania', 'Bari', 'Perugia', 'Sorrento', 'Amalfi', 'Como',
    'Rimini', 'Trieste', 'Ravenna', 'Lucca', 'Capri', 'Positano'
]

# Load FULL dataset first (we'll filter after)
print("Loading full dataset (this may take a minute)...")
dataset = load_dataset(
    'csv',
    data_files='hf://datasets/Dricz/515k-Hotel-Reviews-In-Europe/Hotel_Reviews.csv',
    split='train'  # Load all data
)

print(f"✅ Loaded {len(dataset)} total hotel reviews")

# Filter for Italian hotels
print("🔍 Filtering for Italian hotels...")


def is_italian_hotel(address):
    """Check if hotel address is in Italy"""
    if not address:
        return False
    address_upper = address.upper()

    # Check for "Italy" in address
    if 'ITALY' in address_upper or 'ITALIA' in address_upper:
        return True

    # Check for Italian cities
    for city in ITALIAN_CITIES:
        if city.upper() in address_upper:
            return True

    return False


# Filter dataset
italian_indices = [i for i, address in enumerate(
    dataset['Hotel_Address']) if is_italian_hotel(address)]
dataset = dataset.select(italian_indices)

print(f"✅ Found {len(dataset)} Italian hotel reviews")
print()

# 2. Convert to pandas DataFrame
df = dataset.to_pandas()

print("📋 Dataset columns:")
for col in df.columns:
    print(f"  - {col}")
print()

# 3. Connect to PostgreSQL
print("🔌 Connecting to PostgreSQL...")
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
print("✅ Connected to database")
print()

# 4. Create hotel_reviews table
print("🏗️ Creating hotel_reviews table...")
create_table_query = """
CREATE TABLE IF NOT EXISTS hotel_reviews (
    id SERIAL PRIMARY KEY,
    hotel_name TEXT NOT NULL,
    hotel_address TEXT,
    city TEXT,
    country TEXT,
    latitude FLOAT,
    longitude FLOAT,
    average_score FLOAT,
    total_reviews INTEGER,
    reviewer_nationality TEXT,
    reviewer_score FLOAT,
    positive_review TEXT,
    negative_review TEXT,
    review_date DATE,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
cursor.execute(create_table_query)
conn.commit()
print("✅ Table created (or already exists)")
print()

# 5. Process and clean data
print("🧹 Processing Italian hotel data...")

# Extract city from address (improved for Italian addresses)


def extract_city(address):
    """Extract city from hotel address - Italian-aware"""
    if not address or pd.isna(address):
        return None

    address_clean = address.strip()
    
    # IMPORTANT: Get the word RIGHT BEFORE "Italy" to avoid false matches
    # Example: "Porta Romana 20135 Milan Italy" -> "Milan" not "Romana"
    if ' Italy' in address_clean or ' Italia' in address_clean:
        # Find the word before Italy/Italia
        parts = address_clean.split()
        italy_index = -1
        for i, word in enumerate(parts):
            if word in ['Italy', 'Italia']:
                italy_index = i
                break
        
        if italy_index > 0:
            potential_city = parts[italy_index - 1]
            
            # City name normalization
            city_map = {
                'Roma': 'Rome',
                'Milano': 'Milan',
                'Firenze': 'Florence',
                'Venezia': 'Venice',
                'Napoli': 'Naples',
                'Torino': 'Turin',
                'Genova': 'Genoa',
                'Padova': 'Padua'
            }
            
            # Return normalized name
            return city_map.get(potential_city, potential_city)
    
    return None


def extract_country(address):
    """Extract country from hotel address"""
    if not address or pd.isna(address):
        return None

    # For Italian hotels, always return Italy
    if 'Italy' in address or 'Italia' in address:
        return 'Italy'

    # Fallback
    parts = address.strip().split()
    if len(parts) >= 1:
        last_word = parts[-1]
        if last_word in ['Italy', 'Italia']:
            return 'Italy'
        return last_word

    return None


# Process data
processed_data = []
for idx, row in df.iterrows():
    try:
        # Parse tags (convert string representation of list to actual list)
        tags = []
        if pd.notna(row['Tags']) and row['Tags']:
            # Tags are already a string like "['Leisure trip', 'Couple']"
            try:
                import ast
                tags = ast.literal_eval(row['Tags']) if isinstance(
                    row['Tags'], str) else row['Tags']
            except:
                tags = [str(row['Tags'])]

        # Extract location
        city = extract_city(row['Hotel_Address'])
        country = extract_country(row['Hotel_Address'])

        processed_data.append((
            row['Hotel_Name'] if pd.notna(
                row['Hotel_Name']) else 'Unknown Hotel',
            row['Hotel_Address'] if pd.notna(row['Hotel_Address']) else '',
            city,
            country,
            float(row['lat']) if pd.notna(row['lat']) else None,
            float(row['lng']) if pd.notna(row['lng']) else None,
            float(row['Average_Score']) if pd.notna(
                row['Average_Score']) else None,
            int(row['Total_Number_of_Reviews']) if pd.notna(
                row['Total_Number_of_Reviews']) else 0,
            row['Reviewer_Nationality'] if pd.notna(
                row['Reviewer_Nationality']) else '',
            float(row['Reviewer_Score']) if pd.notna(
                row['Reviewer_Score']) else None,
            row['Positive_Review'] if pd.notna(row['Positive_Review']) else '',
            row['Negative_Review'] if pd.notna(row['Negative_Review']) else '',
            row['Review_Date'] if pd.notna(row['Review_Date']) else None,
            tags
        ))
    except Exception as e:
        print(f"⚠️ Skipping row {idx}: {e}")
        continue

print(f"✅ Processed {len(processed_data)} valid reviews")
print()

# 6. Insert data in batches
print("💾 Inserting data into PostgreSQL...")
insert_query = """
INSERT INTO hotel_reviews (
    hotel_name, hotel_address, city, country, 
    latitude, longitude, average_score, total_reviews,
    reviewer_nationality, reviewer_score, 
    positive_review, negative_review, review_date, tags
)
VALUES %s
ON CONFLICT DO NOTHING
"""

batch_size = 100
for i in range(0, len(processed_data), batch_size):
    batch = processed_data[i:i+batch_size]
    execute_values(cursor, insert_query, batch)
    conn.commit()
    print(f"  ✅ Inserted batch {i//batch_size + 1} ({len(batch)} reviews)")

print()
print(f"✅ Total inserted: {len(processed_data)} reviews")
print()

# 7. Create indexes for better query performance
print("🔍 Creating indexes...")
cursor.execute(
    "CREATE INDEX IF NOT EXISTS idx_hotel_name ON hotel_reviews(hotel_name);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON hotel_reviews(city);")
cursor.execute(
    "CREATE INDEX IF NOT EXISTS idx_country ON hotel_reviews(country);")
cursor.execute(
    "CREATE INDEX IF NOT EXISTS idx_score ON hotel_reviews(reviewer_score);")
conn.commit()
print("✅ Indexes created")
print()

# 8. Verify insertion and show stats
print("📊 Database Statistics:")
print("=" * 60)

cursor.execute("SELECT COUNT(*) FROM hotel_reviews;")
total_count = cursor.fetchone()[0]
print(f"Total reviews in database: {total_count:,}")

cursor.execute("SELECT COUNT(DISTINCT hotel_name) FROM hotel_reviews;")
unique_hotels = cursor.fetchone()[0]
print(f"Unique hotels: {unique_hotels:,}")

cursor.execute(
    "SELECT COUNT(DISTINCT city) FROM hotel_reviews WHERE city IS NOT NULL;")
unique_cities = cursor.fetchone()[0]
print(f"Unique cities: {unique_cities:,}")

cursor.execute(
    "SELECT AVG(reviewer_score) FROM hotel_reviews WHERE reviewer_score IS NOT NULL;")
avg_score = cursor.fetchone()[0]
print(
    f"Average reviewer score: {avg_score:.2f}" if avg_score else "Average reviewer score: N/A")

print()
print("🏨 Top 10 Hotels by Review Count:")
cursor.execute("""
    SELECT hotel_name, city, COUNT(*) as review_count, AVG(reviewer_score) as avg_score
    FROM hotel_reviews
    WHERE hotel_name IS NOT NULL
    GROUP BY hotel_name, city
    ORDER BY review_count DESC
    LIMIT 10
""")
for hotel_name, city, count, avg in cursor.fetchall():
    print(f"  - {hotel_name} ({city}): {count} reviews, avg score {avg:.2f}" if avg else f"  - {hotel_name} ({city}): {count} reviews")

print()
print("🌍 Top Cities by Hotel Count:")
cursor.execute("""
    SELECT city, COUNT(DISTINCT hotel_name) as hotel_count, COUNT(*) as review_count
    FROM hotel_reviews
    WHERE city IS NOT NULL
    GROUP BY city
    ORDER BY hotel_count DESC
    LIMIT 10
""")
for city, hotel_count, review_count in cursor.fetchall():
    print(f"  - {city}: {hotel_count} hotels, {review_count} reviews")

print()

# Close connections
cursor.close()
conn.close()

print("=" * 60)
print("✅ Done! Hotel reviews loaded successfully")
print()

# 9. PATH C (HYBRID): Sync hotels to place_cache for compatibility
print("=" * 60)
print("� PATH C: Syncing hotels to place_cache...")
print("This creates lightweight entries compatible with existing code")
print()

def sync_hotels_to_place_cache():
    """Convert hotel_reviews to place_cache format (Apify-compatible)"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get hotels grouped by city with aggregated data
    cursor.execute("""
        SELECT 
            city,
            hotel_name,
            hotel_address,
            AVG(latitude) as lat,
            AVG(longitude) as lng,
            AVG(reviewer_score) as avg_score,
            COUNT(*) as review_count,
            STRING_AGG(DISTINCT positive_review, ' | ') as highlights
        FROM hotel_reviews
        WHERE city IS NOT NULL 
        AND latitude IS NOT NULL 
        AND longitude IS NOT NULL
        GROUP BY city, hotel_name, hotel_address
        ORDER BY city, avg_score DESC
    """)
    
    hotels = cursor.fetchall()
    print(f"📍 Found {len(hotels)} unique hotels to sync")
    
    synced_count = 0
    for city, name, address, lat, lng, score, reviews, highlights in hotels:
        # Create cache_key in format: city_hotelname
        cache_key = f"{city.lower().replace(' ', '_')}_{name.lower().replace(' ', '_').replace('-', '_')[:50]}"
        
        # Create Apify-compatible JSON format
        place_data = {
            "title": name,
            "address": address,
            "location": {
                "lat": lat,
                "lng": lng
            },
            "rating": score if score else 0,
            "reviewsCount": reviews,
            "categoryName": "Hotel",
            "type": "hotel",
            "description": highlights[:500] if highlights else "",  # Truncate
            "source": "HuggingFace",
            "price": None,
            "website": None,
            "phone": None
        }
        
        # Insert into place_cache (compatible with existing system!)
        insert_cache_query = """
        INSERT INTO place_cache (
            cache_key, place_name, city, country, place_data, priority_level
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (cache_key) 
        DO UPDATE SET 
            place_data = EXCLUDED.place_data,
            last_accessed = NOW()
        """
        
        cursor.execute(insert_cache_query, (
            cache_key,
            name,
            city.lower(),
            'italy',  # All current hotels are Italian
            json.dumps(place_data),
            'medium'  # Priority level for hotels
        ))
        synced_count += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Synced {synced_count} hotels to place_cache")
    return synced_count

# Run the sync
try:
    synced = sync_hotels_to_place_cache()
    print()
    print("🎯 PATH C Benefits:")
    print("  ✅ hotel_reviews: Rich review data for AI context")
    print("  ✅ place_cache: Works with existing dynamic_routing.py")
    print("  ✅ Best of both worlds: Detailed + Compatible")
    print()
except Exception as e:
    print(f"⚠️ Sync failed: {e}")
    print("You can run this manually later")

print()
print("💡 Next steps:")
print("  1. Query hotels by city: SELECT * FROM hotel_reviews WHERE city = 'Milan' LIMIT 10;")
print("  2. Test cache: SELECT * FROM place_cache WHERE cache_key LIKE 'milan_%' LIMIT 5;")
print("  3. Update simple_rag_helper.py to use hotel_reviews for rich context")
print("  4. Use Apify for OTHER categories (cafe, museum, nightlife) - Point 5 Approach 2")


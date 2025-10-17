"""
Direct test of Safe_Data_Loader - Just Bergamo
"""

from Safe_Data_Loader import SafeTourismDataLoader
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Import the loader

print("🧪 Direct Test: Loading Bergamo Only\n")

# Initialize
loader = SafeTourismDataLoader()

# Load just Bergamo with a small bbox
print("Loading Bergamo...")
loader.load_city_data(
    city="Bergamo",
    bbox=(45.693, 9.66, 45.705, 9.68),  # Very small bbox around Città Alta
    load_attractions=True,
    load_restaurants=False  # Skip restaurants for faster test
)

# Commit explicitly
loader.pg_conn.commit()
print("\n✅ Explicitly committed transaction")

# Check immediately BEFORE closing
loader.pg_cursor.execute("""
    SELECT COUNT(*) FROM place_cache 
    WHERE cache_key LIKE 'osm:bergamo:%'
""")
count_before_close = loader.pg_cursor.fetchone()[0]
print(f"📊 Count BEFORE close: {count_before_close}")

# Close
loader.close()

# Open NEW connection to verify
DATABASE_URL = os.getenv('DATABASE_URL')
if '?' in DATABASE_URL:
    DATABASE_URL += '&sslmode=require'
else:
    DATABASE_URL += '?sslmode=require'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    SELECT COUNT(*) FROM place_cache 
    WHERE cache_key LIKE 'osm:bergamo:%'
""")
count_after = cur.fetchone()[0]
print(f"📊 Count AFTER close (new connection): {count_after}")

if count_after > 0:
    cur.execute("""
        SELECT cache_key, place_name
        FROM place_cache 
        WHERE cache_key LIKE 'osm:bergamo:%'
        LIMIT 5
    """)
    print("\n✅ Sample entries:")
    for key, name in cur.fetchall():
        print(f"  • {name} ({key})")
else:
    print("\n❌ NO DATA FOUND!")

cur.close()
conn.close()

print("\n🏁 Test complete")

# Quick Start: Safe Data Loader

## 🚀 One-Command Setup

```bash
# 1. Run the safe data loader
python Safe_Data_Loader.py
```

That's it! No API key needed, no registration, 100% safe.

---

## ✅ What It Does

1. Connects to your PostgreSQL database (uses `DATABASE_URL` from `.env`)
2. Connects to ChromaDB (uses `./chromadb_data` directory)
3. Fetches POI data from OpenStreetMap (Overpass API - 100% safe, free, no API key)
4. Loads 10 Italian cities:
   - **Bergamo** (your priority!)
   - Rome, Florence, Venice, Milan
   - Naples, Turin, Bologna, Genoa, Verona
5. Saves to `place_cache` table (cache_key: `osm:city:id`)
6. Adds to ChromaDB for RAG retrieval
7. Compatible with existing AI companion routes

---

## 📋 Prerequisites

### Required: .env File

```bash
# Your .env file should have:
DATABASE_URL=postgresql://user:password@host:port/dbname

# That's it! No API keys needed for OpenStreetMap
```

### Required: Dependencies

Should already be installed, but if not:

```bash
pip install sentence-transformers chromadb psycopg2-binary requests python-dotenv
```

---

## 🎯 Expected Output

```
🇮🇹 ViaMigo SAFE Data Loader - OpenStreetMap Integration 🇮🇹

✅ Using OpenStreetMap (Overpass API) - 100% Safe
✅ No suspicious APIs, No scam risks
✅ Community-maintained, Open Source data

📦 Loading embedding model (all-MiniLM-L6-v2)...
✅ Embedding model loaded
📚 Using ChromaDB collection: viamigo_travel_data
✅ place_cache table exists

============================================================
🚀 Starting SAFE data load for Bergamo (OpenStreetMap)
============================================================

🔍 Fetching attractions for Bergamo from OpenStreetMap...
✅ Found 87 attractions in Bergamo
✅ Saved attraction: Basilica di Santa Maria Maggiore
✅ Saved attraction: Accademia Carrara
✅ Saved attraction: Rocca di Bergamo
...

🍽️  Fetching restaurants for Bergamo from OpenStreetMap...
✅ Found 234 restaurants/cafes in Bergamo
✅ Saved restaurant: Ristorante Da Mimmo
✅ Saved restaurant: Trattoria Sant'Ambroeus
...

============================================================
✅ Bergamo SAFE Data Load Complete (OpenStreetMap)
============================================================
Total places inserted: 321
Source: OpenStreetMap (100% Safe)
============================================================

[... repeats for other cities ...]

🔒 Database connections closed

🎉 All done! Your place_cache and ChromaDB are now enriched with SAFE OpenStreetMap data!
💡 Tip: This data integrates seamlessly with cost_effective_scraping.py
✅ 100% Safe - No suspicious APIs - No scam risks
```

---

## ⏱️ How Long Does It Take?

- **Per city**: ~30-60 seconds
- **All 10 cities**: ~8-12 minutes
- **Rate limiting**: 2 second delay between cities (respectful to OSM servers)

---

## 🔍 Verify It Worked

### Check PostgreSQL

```bash
python -c "
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute(\"SELECT COUNT(*) FROM place_cache WHERE cache_key LIKE 'osm:%'\")
count = cur.fetchone()[0]
print(f'✅ Total OpenStreetMap places loaded: {count}')

cur.execute(\"SELECT COUNT(*) FROM place_cache WHERE cache_key LIKE 'osm:bergamo:%'\")
bergamo_count = cur.fetchone()[0]
print(f'✅ Bergamo places: {bergamo_count}')

cur.close()
conn.close()
"
```

Expected output:

```
✅ Total OpenStreetMap places loaded: 2847
✅ Bergamo places: 321
```

### Check ChromaDB

```bash
python -c "
import chromadb

client = chromadb.PersistentClient(path='./chromadb_data')
collection = client.get_collection('viamigo_travel_data')
count = collection.count()
print(f'✅ ChromaDB total documents: {count}')

# Query for Bergamo
results = collection.query(
    query_texts=['churches in Bergamo'],
    n_results=3,
    where={'city': 'Bergamo'}
)
print(f'✅ Example Bergamo results: {len(results[\"documents\"][0])} found')
for doc in results['documents'][0]:
    print(f'   - {doc[:100]}...')
"
```

---

## 🧪 Test with AI Companion

```bash
python -c "
from simple_rag_helper import get_city_context

context = get_city_context('Bergamo', limit=5)
print('✅ AI can now use OpenStreetMap data!')
print(f'   Found {len(context)} places in Bergamo')
"
```

---

## 🎨 Customize for Your Needs

### Load Specific City

```python
from Safe_Data_Loader import SafeTourismDataLoader

loader = SafeTourismDataLoader()

# Load just Bergamo
loader.load_city_data(
    city="Bergamo",
    bbox=(45.67, 9.64, 45.72, 9.70),  # South, West, North, East
    load_attractions=True,
    load_restaurants=True
)

loader.close()
```

### Load Different City

```python
# Find bounding box at: https://boundingbox.klokantech.com/
# Format: CSV → (south, west, north, east)

from Safe_Data_Loader import SafeTourismDataLoader

loader = SafeTourismDataLoader()

# Example: Pisa
loader.load_city_data(
    city="Pisa",
    bbox=(43.70, 10.38, 43.73, 10.41),
    load_attractions=True,
    load_restaurants=True
)

loader.close()
```

### Load Only Attractions (Skip Restaurants)

```python
from Safe_Data_Loader import SafeTourismDataLoader

loader = SafeTourismDataLoader()

loader.load_city_data(
    city="Bergamo",
    bbox=(45.67, 9.64, 45.72, 9.70),
    load_attractions=True,
    load_restaurants=False  # Skip restaurants
)

loader.close()
```

---

## 🐛 Troubleshooting

### "DATABASE_URL not found"

**Fix**: Add to `.env`:

```
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### "No module named 'sentence_transformers'"

**Fix**:

```bash
pip install sentence-transformers
```

### "Timeout" or "No elements found"

**Possible causes**:

1. Bounding box too large → reduce bbox size
2. Overpass API slow → try again later (it's free, sometimes congested)
3. Wrong bbox coordinates → verify at https://boundingbox.klokantech.com/

---

## 📚 More Documentation

- Full guide: `VIAMIGO_DATA_LOADER_GUIDE.md`
- Security info: `OPENTRIPMAP_WARNING.md`
- Comparison: `DATA_SOURCES_COMPARISON.md`
- Summary: `SAFE_DATA_LOADER_SUMMARY.md`

---

## ✅ Success!

After running the script, you'll have:

- ✅ ~3000 places from 10 Italian cities
- ✅ Stored in PostgreSQL `place_cache` table
- ✅ Indexed in ChromaDB for RAG
- ✅ Ready for AI companion queries
- ✅ 100% safe data source (OpenStreetMap)
- ✅ $0 cost (truly free, not "free trial")
- ✅ No API keys, no registration, no tracking

**🎉 Enjoy your safe, free tourism data!**

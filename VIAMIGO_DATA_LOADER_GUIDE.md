# ⚠️ DEPRECATED - OpenTripMap Scam Alert ⚠️

**DO NOT USE `Viamigo_Data_Loader_Fixed.py` - OpenTripMap has been identified as suspicious/scam**

## ✅ Use Safe Alternative: `Safe_Data_Loader.py`

Use **OpenStreetMap** instead - 100% safe, community-maintained, open source.

---

# Safe Tourism Data Loader - Integration Guide

## 🎯 Purpose

`Safe_Data_Loader.py` loads **FREE tourism data** from OpenStreetMap (Overpass API) into your existing PostgreSQL `place_cache` table and ChromaDB `viamigo_travel_data` collection. This enriches your AI companion with authentic POI data at **zero cost** from a **100% safe source**.

---

## ✅ What's Safe (OpenStreetMap vs OpenTripMap)

### ❌ OpenTripMap (AVOID - Suspicious/Scam)

Issues found:

- Suspicious API practices
- Identified as potential scam
- **DO NOT USE**

### ✅ OpenStreetMap (SAFE - Use This!)

Why it's safe:

- ✅ **Open Source** - Community-maintained since 2004
- ✅ **Transparent** - All data is publicly auditable
- ✅ **No API Key Required** - Completely free Overpass API
- ✅ **Trusted** - Used by Wikipedia, Apple Maps, Foursquare, etc.
- ✅ **Non-profit** - OpenStreetMap Foundation
- ✅ **Privacy-focused** - No tracking, no data collection

**Sources**:

- Overpass API: https://overpass-api.de/
- OpenStreetMap: https://www.openstreetmap.org/
- OSM Foundation: https://osmfoundation.org/

---

## 📋 Prerequisites

### No API Key Needed! 🎉

OpenStreetMap's Overpass API is **completely free** and requires **no registration**!

### 1. Add to `.env` File

```bash
# PostgreSQL (should already exist)
DATABASE_URL=postgresql://user:password@host:port/viamigo_db

# No OPENTRIPMAP_API_KEY needed - we're using OpenStreetMap!
```

### 2. Install Dependencies

All dependencies should already be installed:

```bash
pip install sentence-transformers chromadb psycopg2-binary requests python-dotenv
```

---

## 🚀 Usage

### Basic Usage (Load All Italian Cities)

```bash
python Safe_Data_Loader.py
```

This will load data for **10 Italian cities** including Bergamo from **OpenStreetMap**:

- Bergamo, Rome, Florence, Venice, Milan, Naples, Turin, Bologna, Genoa, Verona

### Custom Usage (Python Script)

```python
from Safe_Data_Loader import SafeTourismDataLoader

# Initialize (no API key needed!)
loader = SafeTourismDataLoader(chroma_path="./chromadb_data")

# Load specific city with bounding box (south, west, north, east)
loader.load_city_data(
    city="Bergamo",
    bbox=(45.67, 9.64, 45.72, 9.70),  # Bounding box coordinates
    load_attractions=True,  # Museums, monuments, churches
    load_restaurants=True   # Restaurants, cafes, bars
)

# Close connections
loader.close()
```

### Find Bounding Boxes

Use https://boundingbox.klokantech.com/

1. Search for your city
2. Select "CSV" format
3. Use the coordinates in order: south, west, north, east

## 📊 Data Flow

```
OpenStreetMap (Overpass API) - 100% SAFE & FREE
    ↓
1. Query bounding box → Get POIs (nodes + ways)
    ↓
2. Fetch attractions → Museums, monuments, churches, viewpoints
    ↓
3. Fetch restaurants → Restaurants, cafes, bars
    ↓
4. Transform to place_cache format → Compatible JSONB structure
    ↓
5. INSERT into PostgreSQL → place_cache table
    ↓
6. ADD to ChromaDB → viamigo_travel_data collection for RAG
    ↓
✅ Data ready for AI companion!
```

**Data Source**: Community-maintained OpenStreetMap database (millions of contributors worldwide)

---

## 🗃️ Database Integration

### PostgreSQL `place_cache` Table

**Cache Key Format**: `osm:{city}:{osm_id}`

Example:

```
cache_key: osm:bergamo:123456789
place_name: Basilica di Santa Maria Maggiore
city: Bergamo
place_data: {
    "name": "Basilica di Santa Maria Maggiore",
    "types": ["tourist_attraction", "place_of_worship", "christian"],
    "vicinity": "Piazza Duomo, Bergamo",
    "geometry": {"location": {"lat": 45.7035, "lng": 9.6593}},
    "rating": 0,
    "description": "Historic church. Architecture: romanesque. Wikipedia: https://en.wikipedia.org/wiki/...",
    "source": "openstreetmap",
    "osm_id": 123456789,
    "osm_type": "node",
    "wikipedia": "it:Basilica di Santa Maria Maggiore (Bergamo)",
    "wikidata": "Q2345678",
    "historic_type": "church",
    "religion": "christian",
    "fetched_at": "2025-10-16T10:30:00"
}
```

### ChromaDB `viamigo_travel_data` Collection

**Document Text**: Rich embedding-friendly text

```
"Basilica di Santa Maria Maggiore in Bergamo. Beautiful 12th-century basilica
with ornate interiors and stunning frescoes. Categories: churches, interesting_places.
Location: Piazza Duomo"
```

**Metadata**:

```json
{
  "city": "Bergamo",
  "place_name": "Basilica di Santa Maria Maggiore",
  "source": "opentripmap",
  "kinds": "churches, interesting_places",
  "rating": "4.8"
}
```

---

## 🔗 Integration with Existing System

### With `simple_rag_helper.py`

The loaded data is **immediately queryable** via existing RAG functions:

```python
from simple_rag_helper import get_city_context

# Query loaded data
context = get_city_context("Bergamo", limit=10)
# Returns places from place_cache including OpenTripMap data!
```

### With `cost_effective_scraping.py`

OpenTripMap data acts as a **fallback** when Apify is rate-limited:

```python
# In cost_effective_scraping.py logic:
# 1. Try Apify (paid, detailed reviews)
# 2. If rate-limited → Check place_cache
# 3. Return OpenTripMap data (free, good descriptions)
```

### With AI Companion Routes

The AI companion (`ai_companion_routes.py`) automatically uses this data:

```python
# Piano B endpoint queries place_cache
# Now includes OpenTripMap POIs for Bergamo!
response = requests.post('/api/ai-companion/piano-b', json={
    "city": "Bergamo",
    "interests": ["art", "history"]
})
# AI suggests: Basilica di Santa Maria Maggiore, Accademia Carrara, etc.
```

---

## 📈 Performance & Costs

| Metric               | Value                         |
| -------------------- | ----------------------------- |
| **API Cost**         | $0 (FREE tier)                |
| **Rate Limit**       | 1000 requests/day             |
| **POIs per Request** | Up to 100                     |
| **Request Delay**    | 0.3s (rate limiting)          |
| **Time per City**    | ~30-60 seconds (with details) |
| **10 Cities Total**  | ~10-15 minutes                |

**Cost Comparison**:

- Apify: $49/month for 200 searches
- OpenTripMap: **FREE** for 1000 requests/day
- **Savings**: 100% for basic POI data

---

## 🐛 Troubleshooting

### Error: `DATABASE_URL not found`

**Solution**: Add to `.env`:

```bash
DATABASE_URL=postgresql://user:password@host:port/viamigo_db
```

### Error: `OPENTRIPMAP_API_KEY not found`

**Solution**:

1. Get free key from https://opentripmap.io/
2. Add to `.env`:

```bash
OPENTRIPMAP_API_KEY=your_key_here
```

### Error: `place_cache table not found`

**Solution**: The script auto-creates it! Run:

```python
loader.ensure_place_cache_ready()
```

### No POIs Found for City

**Possible causes**:

1. City name spelling (try "Roma" instead of "Rome" for Italian cities)
2. Wrong country code (use "it" for Italy)
3. Radius too small (increase to 5000-8000m)

**Solution**:

```python
loader.load_city_data("Roma", "it", radius=8000, limit=100)
```

### Rate Limit Exceeded (429 Error)

**Solution**: Free tier = 1000 req/day. Either:

1. Wait 24 hours
2. Reduce `limit` parameter
3. Set `fetch_details=False` (uses fewer API calls)

---

## 🔍 Verify Data Loaded

### Check PostgreSQL

```sql
-- Count OpenTripMap entries
SELECT COUNT(*)
FROM place_cache
WHERE cache_key LIKE 'opentripmap:bergamo:%';

-- View sample data
SELECT place_name, city, place_data->>'rating' as rating
FROM place_cache
WHERE city = 'Bergamo'
  AND cache_key LIKE 'opentripmap:%'
LIMIT 10;
```

### Check ChromaDB

```python
import chromadb

client = chromadb.PersistentClient(path="./chromadb_data")
collection = client.get_collection("viamigo_travel_data")

# Count total documents
print(f"Total docs: {collection.count()}")

# Query Bergamo places
results = collection.query(
    query_texts=["historical churches in Bergamo"],
    n_results=5,
    where={"city": "Bergamo"}
)
print(results)
```

---

## 🎨 Customization

### Add More Cities

Edit the `italian_cities` list in `main()`:

```python
italian_cities = [
    {"city": "Bergamo", "country_code": "it", "radius": 5000, "limit": 50},
    {"city": "Siena", "country_code": "it", "radius": 4000, "limit": 40},
    {"city": "Pisa", "country_code": "it", "radius": 3000, "limit": 30},
    # Add more...
]
```

### Load Non-Italian Cities

```python
loader.load_city_data("Paris", "fr", radius=10000, limit=100)
loader.load_city_data("Barcelona", "es", radius=8000, limit=80)
loader.load_city_data("Berlin", "de", radius=8000, limit=80)
```

### Adjust POI Categories

Edit `kinds` parameter in `fetch_pois_in_radius()`:

```python
params = {
    "kinds": "museums,art_galleries,theatres,historic,monuments",  # Custom categories
    # ...
}
```

Available kinds: https://opentripmap.io/catalog

---

## 📚 Related Files

| File                           | Purpose                                      |
| ------------------------------ | -------------------------------------------- |
| `Viamigo_Data_Loader_Fixed.py` | Main data loader script (contextualized)     |
| `simple_rag_helper.py`         | RAG functions that query loaded data         |
| `cost_effective_scraping.py`   | Apify integration with fallback logic        |
| `ai_companion_routes.py`       | AI endpoints that use place_cache            |
| `POINT_5_APPROACH_2_GUIDE.md`  | Selective Apify strategy (47% savings)       |
| `CRITICAL_FINDINGS.md`         | ChromaDB analysis (not currently used by AI) |

---

## 🚀 Next Steps

1. ✅ **Get OpenTripMap API key** (free, takes 2 minutes)
2. ✅ **Add to `.env` file** (`OPENTRIPMAP_API_KEY=...`)
3. ✅ **Install sentence-transformers** (`pip install sentence-transformers`)
4. ✅ **Run the script**: `python Viamigo_Data_Loader_Fixed.py`
5. ✅ **Verify data loaded** (SQL queries above)
6. ✅ **Test AI companion** with Bergamo requests
7. ✅ **Enjoy FREE POI data!** 🎉

---

## 💡 Pro Tips

- **Start with Bergamo**: Test with one city before loading all 10
- **Use `fetch_details=True`**: Richer data for better AI responses
- **Check rate limits**: 1000 req/day = plenty for daily updates
- **Combine with Apify**: Use OpenTripMap for discovery, Apify for detailed reviews
- **Update periodically**: Run monthly to refresh POI data

---

## 📞 Support

If you encounter issues:

1. Check `.env` file has both variables
2. Verify PostgreSQL connection works
3. Test OpenTripMap API key: https://opentripmap.io/product
4. Review logs for specific error messages
5. Check ChromaDB path: `./chromadb_data` exists

---

**✨ Congratulations! You now have a FREE, unlimited source of tourism data for your AI companion!**

# 🎯 Point 5 Approach 2: Selective Apify for Bergamo

## Strategy Overview

**Path C (Hybrid) + Selective Apify = Maximum Value, Minimum Cost**

Instead of using Apify for ALL categories (~$0.75), we use:

- ✅ **HuggingFace hotels** (FREE - already loaded)
- ✅ **Existing data** (restaurants, attractions - already cached)
- 💰 **Apify for gaps** (cafes, museums, monuments, nightlife, bars, bakeries)

**Estimated Cost**: ~$0.40 instead of ~$0.75 (47% savings!)

---

## Step 1: Check Current Bergamo Data

```bash
# Check what's already cached for Bergamo
curl -X GET "http://localhost:5001/admin/cache-status?city=bergamo"
```

**Expected Result**:

```json
{
  "city": "bergamo",
  "categories": {
    "restaurant": {
      "count": 170,
      "expires_at": "2025-10-23T..."
    },
    "tourist_attraction": {
      "count": 20,
      "expires_at": "2025-10-23T..."
    }
  }
}
```

---

## Step 2: Sync HuggingFace Hotels First

Before using Apify, let's add hotels from our HuggingFace dataset:

```bash
# Run the hotel sync
cd /workspaces/ViamigoTravelAI
python HuggingFace_DataSets_Insertion.py
```

This will:

1. Load 38,105 Italian hotel reviews
2. **Sync hotels to `place_cache`** (Path C hybrid approach)
3. Make hotels available in Bergamo (if any Italian hotels in dataset)

**Note**: Current dataset has Milan (161 hotels) and Rome (8 hotels). We may need to expand to include Bergamo-specific hotels later.

---

## Step 3: Selective Apify Population

Now populate ONLY the missing categories via Apify:

```bash
# Populate Bergamo with NON-HOTEL categories
curl -X POST "http://localhost:5001/admin/populate-city" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: viamigo_admin_2024" \
  -d '{
    "city": "bergamo",
    "categories": ["cafe", "museum", "monument", "nightlife", "bar", "bakery"],
    "force_refresh": false,
    "use_free_tier": false
  }'
```

### Category Breakdown

| Category              | Why Apify?                             | Expected Cost |
| --------------------- | -------------------------------------- | ------------- |
| ✅ restaurant         | **SKIP** - Already cached (170 places) | $0            |
| ✅ tourist_attraction | **SKIP** - Already cached (20 places)  | $0            |
| ✅ hotel              | **SKIP** - HuggingFace data available  | $0            |
| 💰 cafe               | Need - Not cached                      | ~$0.06        |
| 💰 museum             | Need - Cultural data important         | ~$0.06        |
| 💰 monument           | Need - Historical context              | ~$0.06        |
| 💰 nightlife          | Need - Evening recommendations         | ~$0.06        |
| 💰 bar                | Need - Social venues                   | ~$0.06        |
| 💰 bakery             | Need - Local food culture              | ~$0.06        |

**Total Estimated Cost**: 6 categories × ~$0.06 = **~$0.36-$0.40**

**Savings vs Full Apify**: $0.75 - $0.40 = **$0.35 saved (47%)**

---

## Step 4: Verify the Hybrid Data

After population, check what we have:

```bash
# Check updated cache status
curl -X GET "http://localhost:5001/admin/cache-status?city=bergamo"
```

**Expected Result** (after selective population):

```json
{
  "city": "bergamo",
  "categories": {
    "restaurant": { "count": 170, "source": "apify" },
    "tourist_attraction": { "count": 20, "source": "apify" },
    "hotel": { "count": X, "source": "huggingface" },
    "cafe": { "count": 50-100, "source": "apify" },
    "museum": { "count": 10-20, "source": "apify" },
    "monument": { "count": 15-30, "source": "apify" },
    "nightlife": { "count": 20-40, "source": "apify" },
    "bar": { "count": 30-60, "source": "apify" },
    "bakery": { "count": 20-40, "source": "apify" }
  },
  "total_places": 335-540
}
```

---

## Step 5: Test Route Quality

Generate a Bergamo route to verify hybrid data quality:

```bash
# Test route generation
curl -X POST "http://localhost:5001/api/routes/instant" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Bergamo, Italy",
    "duration": "full-day",
    "preferences": {
      "interests": ["culture", "food", "local"],
      "pace": "moderate"
    }
  }'
```

**Quality Checks**:

- ✅ No repetition of places
- ✅ Multiple categories used (restaurants, cafes, museums, monuments)
- ✅ Hotels suggested from HuggingFace data (with reviews!)
- ✅ Rich details from all sources
- ✅ Cache hit logs in console

---

## Path C Benefits Verification

### 1. Check hotel_reviews Table

```sql
SELECT city, COUNT(*) as hotels, AVG(reviewer_score) as avg_score
FROM hotel_reviews
WHERE city IN ('Milan', 'Rome', 'Bergamo')
GROUP BY city;
```

### 2. Check place_cache Table

```sql
SELECT city, category, COUNT(*) as count
FROM place_cache
WHERE city = 'bergamo'
GROUP BY city, category
ORDER BY category;
```

### 3. Test RAG Helper

```bash
python -c "
from simple_rag_helper import get_city_context_prompt, get_hotel_context_prompt

# Test place context
place_context = get_city_context_prompt('Bergamo', ['restaurant', 'cafe', 'museum'])
print(place_context)

# Test hotel context (if Bergamo hotels exist)
hotel_context = get_hotel_context_prompt('Milan', min_score=8.5, limit=3)
print(hotel_context)
"
```

---

## Alternative: Free Tier Test

If you want to test WITHOUT spending money first:

```bash
# Use free APIs (OSM + Geoapify) instead of Apify
curl -X POST "http://localhost:5001/admin/populate-city" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: viamigo_admin_2024" \
  -d '{
    "city": "bergamo",
    "categories": ["cafe", "museum", "monument", "park", "church"],
    "force_refresh": false,
    "use_free_tier": true
  }'
```

**Pros**:

- ✅ FREE
- ✅ Good coverage for basic categories
- ✅ Fast testing

**Cons**:

- ❌ Less detailed than Apify
- ❌ May miss some niche places
- ❌ No reviews/ratings from Google Maps

---

## Cost Comparison Table

| Approach               | Categories                | Source                       | Cost   |
| ---------------------- | ------------------------- | ---------------------------- | ------ |
| **Full Apify**         | 12 categories             | Google Maps scraping         | ~$0.75 |
| **Point 5 Approach 2** | 9 total (3 free + 6 paid) | HuggingFace + Apify          | ~$0.40 |
| **Free Tier Only**     | 9 categories              | HuggingFace + OSM + Geoapify | $0     |

**Recommendation**: Use **Point 5 Approach 2** for best quality-to-cost ratio.

---

## Next Steps After Population

1. **Test AI Companion** with Milan/Rome (we have hotel data!)

   ```bash
   # Piano B test
   curl -X POST "http://localhost:5001/api/ai-companion/piano-b" \
     -H "Content-Type: application/json" \
     -d '{
       "itinerary": [...],
       "context": "Milano city center, rainy weather"
     }'
   ```

2. **Verify hotel integration**

   - Check if AI suggests hotels with real reviews
   - Verify no hallucinations
   - Confirm hotel descriptions match HuggingFace data

3. **Generate Bergamo routes**

   - Test with different preferences
   - Verify category diversity
   - Check route quality

4. **Expand HuggingFace dataset** (optional)
   - Load more Italian cities
   - Filter for Bergamo-specific hotels
   - Increase coverage beyond Milan/Rome

---

## Troubleshooting

### Hotels not showing in place_cache?

```bash
# Re-run the sync function
python -c "
import os
from dotenv import load_dotenv
import psycopg2
import json

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Check if hotels are in hotel_reviews
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute('SELECT city, COUNT(*) FROM hotel_reviews GROUP BY city')
print('Hotels in hotel_reviews:', cur.fetchall())

# Check if hotels are in place_cache
cur.execute(\"SELECT city, COUNT(*) FROM place_cache WHERE category = 'hotel' GROUP BY city\")
print('Hotels in place_cache:', cur.fetchall())
cur.close()
conn.close()
"
```

### Apify population failing?

- Check `APIFY_API_KEY` in `.env`
- Verify admin token: `viamigo_admin_2024`
- Check Apify account balance
- Review logs for specific errors

### RAG not returning hotel context?

```bash
# Test RAG helper directly
python -c "
from simple_rag_helper import rag_helper

# Test get_hotel_context
result = rag_helper.get_hotel_context('Milan', min_score=8.0, limit=5)
print(f'Hotels found: {result.get(\"count\", 0)}')
print(f'Cities: {[h[\"name\"] for h in result.get(\"hotels\", [])]}')
"
```

---

## Success Criteria

✅ **Path C Hybrid working**:

- hotel_reviews has rich data (38K+ reviews)
- place_cache has lightweight hotel entries
- Both sources accessible via RAG

✅ **Cost Optimization**:

- Spending ~$0.40 instead of ~$0.75
- HuggingFace hotels integrated (free)
- Only paying for gaps

✅ **Quality Maintained**:

- Multiple categories (9+ total)
- Rich hotel reviews available
- No hallucinations in AI responses
- Route diversity improved

✅ **Ready for Production**:

- Bergamo fully populated
- AI Companion using real data
- Hotel recommendations with reviews
- Scalable to other cities

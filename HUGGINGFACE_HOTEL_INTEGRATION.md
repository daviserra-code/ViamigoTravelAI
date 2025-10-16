# 🏨 HuggingFace Hotel Reviews Integration

## Overview

Successfully integrated **515K European Hotel Reviews** dataset from HuggingFace into PostgreSQL for RAG-powered hotel recommendations.

**Dataset**: `Dricz/515k-Hotel-Reviews-In-Europe`  
**Records**: 515,738 hotel reviews  
**Coverage**: European hotels (Amsterdam, London, Paris, Barcelona, etc.)

---

## ✅ What Works

### 1. Data Loading

- ✅ Loads hotel reviews from HuggingFace
- ✅ Processes 1000 reviews in test mode
- ✅ Extracts city/country from addresses
- ✅ Parses review tags and scores

### 2. Database Schema

```sql
CREATE TABLE hotel_reviews (
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
```

### 3. Indexes

- ✅ `hotel_name` - Fast hotel lookup
- ✅ `city` - Query by location
- ✅ `country` - Regional filtering
- ✅ `reviewer_score` - Find top-rated hotels

---

## 🧪 Test Results

**Test Run** (1000 reviews):

```
Total reviews: 1,000
Unique hotels: 3
Unique cities: 2
Average score: 8.31/10

Top Hotels:
  - K K Hotel George (London): 566 reviews, 8.60 avg
  - Hotel Arena (Amsterdam): 405 reviews, 7.84 avg
  - Apex Temple Court Hotel (London): 29 reviews, 9.05 avg

Cities:
  - London: 2 hotels, 595 reviews
  - Amsterdam: 1 hotel, 405 reviews
```

---

## 📊 Sample Data

```python
Hotel: Hotel Arena
Score: 7.5/10
Location: Amsterdam, Netherlands
Coordinates: 52.36°N, 4.92°E

Positive Review:
"No real complaints the hotel was great great location
surroundings rooms amenities and service..."

Negative Review:
"No Negative"

Tags: ['Leisure trip', 'Couple', 'Duplex Double Room', 'Stayed 6 nights']
```

---

## 🚀 Usage

### Run Full Import (515K reviews)

```bash
# Edit line 22 in HuggingFace_DataSets_Insertion.py:
# Change: split='train[:1000]'  # Test with 1000
# To: split='train'  # Full dataset

python HuggingFace_DataSets_Insertion.py
```

**Note**: Full import will take ~10-15 minutes

### Query Examples

#### Get Top Hotels in Amsterdam

```sql
SELECT hotel_name, AVG(reviewer_score) as avg_score, COUNT(*) as review_count
FROM hotel_reviews
WHERE city = 'Amsterdam'
GROUP BY hotel_name
ORDER BY avg_score DESC
LIMIT 10;
```

#### Find High-Rated Hotels

```sql
SELECT DISTINCT hotel_name, city, average_score, latitude, longitude
FROM hotel_reviews
WHERE reviewer_score >= 9.0
AND city IS NOT NULL
ORDER BY average_score DESC
LIMIT 20;
```

#### Get Reviews for Specific Hotel

```sql
SELECT reviewer_score, positive_review, negative_review, review_date
FROM hotel_reviews
WHERE hotel_name LIKE '%Arena%'
AND city = 'Amsterdam'
ORDER BY review_date DESC
LIMIT 10;
```

---

## 🧠 RAG Integration Ideas

### 1. Hotel Recommendations

```python
def get_hotel_recommendations(city: str, min_score: float = 8.0):
    """Get top-rated hotels for RAG context"""
    query = """
        SELECT hotel_name, city, average_score,
               latitude, longitude,
               STRING_AGG(DISTINCT positive_review, ' | ') as highlights
        FROM hotel_reviews
        WHERE city = %s AND reviewer_score >= %s
        GROUP BY hotel_name, city, average_score, latitude, longitude
        ORDER BY average_score DESC
        LIMIT 5
    """
    # Use in AI prompts for hotel suggestions
```

### 2. Review Sentiment Analysis

```python
def analyze_hotel_sentiment(hotel_name: str):
    """Aggregate positive/negative sentiment for AI context"""
    query = """
        SELECT
            AVG(reviewer_score) as avg_score,
            COUNT(CASE WHEN reviewer_score >= 8 THEN 1 END) as positive_count,
            COUNT(CASE WHEN reviewer_score < 8 THEN 1 END) as negative_count,
            ARRAY_AGG(positive_review ORDER BY reviewer_score DESC LIMIT 5) as top_positives,
            ARRAY_AGG(negative_review ORDER BY reviewer_score ASC LIMIT 3) as top_negatives
        FROM hotel_reviews
        WHERE hotel_name = %s
    """
    # Feed to AI for balanced recommendations
```

### 3. Location-Based Context

```python
def get_nearby_hotels(lat: float, lng: float, radius_km: float = 2.0):
    """Find hotels near attractions for itinerary planning"""
    query = """
        SELECT DISTINCT ON (hotel_name)
            hotel_name, hotel_address, average_score,
            latitude, longitude,
            (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) *
             cos(radians(longitude) - radians(%s)) +
             sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
        FROM hotel_reviews
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        HAVING distance_km <= %s
        ORDER BY hotel_name, average_score DESC
        LIMIT 10
    """
    # Include in route planning with attractions
```

---

## 🔗 Integration with Existing System

### Option 1: Extend Place Cache

Add hotel reviews to existing `place_cache` table:

```python
# In apify_integration.py
def enrich_hotel_with_reviews(city: str, hotel_name: str) -> Dict:
    """Add real reviews from HuggingFace dataset"""
    query = """
        SELECT AVG(reviewer_score) as avg_score,
               COUNT(*) as review_count,
               STRING_AGG(positive_review, ' | ') as highlights
        FROM hotel_reviews
        WHERE city = %s AND hotel_name LIKE %s
        LIMIT 100
    """
    # Merge with Apify hotel data
```

### Option 2: RAG Context Injection

Use in `simple_rag_helper.py`:

```python
def get_hotel_context(city: str) -> str:
    """Get hotel context for AI prompts"""
    query = """
        SELECT hotel_name, average_score,
               COUNT(*) as reviews,
               STRING_AGG(DISTINCT tags::text, ', ') as common_tags
        FROM hotel_reviews
        WHERE city = %s
        GROUP BY hotel_name, average_score
        ORDER BY average_score DESC
        LIMIT 5
    """
    # Format for AI companion prompts
```

### Option 3: ChromaDB Embeddings

Index reviews for semantic search:

```python
from app.services.chromadb_service import ChromaDBService

def index_hotel_reviews():
    """Add hotel reviews to ChromaDB for semantic search"""
    reviews = fetch_hotel_reviews()

    for review in reviews:
        document = f"""
        Hotel: {review['hotel_name']}
        Location: {review['city']}, {review['country']}
        Rating: {review['average_score']}/10
        Review: {review['positive_review']}
        Tags: {', '.join(review['tags'])}
        """
        chromadb_service.add_document(document, metadata=review)
```

---

## 📈 Next Steps

### Immediate

1. ✅ Script tested with 1000 reviews
2. ✅ Table created with indexes
3. ✅ Sample queries working

### Short-Term

1. **Decide on integration approach**:

   - Extend `place_cache` table?
   - Separate `hotel_reviews` table?
   - Feed into ChromaDB for RAG?

2. **Load full dataset** (515K reviews):

   ```bash
   # Change split='train[:1000]' to split='train'
   python HuggingFace_DataSets_Insertion.py
   ```

3. **Create helper functions** in `simple_rag_helper.py`:
   - `get_hotel_reviews_context(city)`
   - `get_top_rated_hotels(city, min_score)`
   - `get_hotel_highlights(hotel_name)`

### Long-Term

1. **Semantic Search**: Index reviews in ChromaDB
2. **Sentiment Analysis**: Classify positive/negative patterns
3. **Recommendation Engine**: Use reviews for personalized suggestions
4. **Multi-language**: Dataset has reviews in multiple languages

---

## 💡 Benefits for Viamigo

### 1. Real Hotel Data

- **Before**: AI hallucinates hotel names
- **After**: AI uses real hotels with verified reviews

### 2. Rich Context

- **Before**: Generic "top hotels in [city]"
- **After**: "Hotel Arena (7.8/10, 405 reviews) - guests love the park location"

### 3. Personalization

- **Tags**: Identify family-friendly, couples, business hotels
- **Reviews**: Match user preferences with review sentiment
- **Location**: Find hotels near planned attractions

### 4. Quality Assurance

- **Ratings**: Only suggest hotels with 8+ scores
- **Review Count**: Prioritize well-reviewed hotels
- **Recent Data**: Filter by review recency

---

## 🎯 Integration with Point 5 (Bergamo Test)

When ready to test Bergamo:

1. **Check if Bergamo hotels in dataset**:

   ```sql
   SELECT COUNT(*) FROM hotel_reviews WHERE city = 'Bergamo';
   ```

2. **If yes, use for route context**:

   ```python
   # In dynamic_routing.py
   bergamo_hotels = get_hotel_reviews_context('Bergamo')
   # Include in itinerary with attractions + restaurants
   ```

3. **Test RAG with real data**:
   - Generate Bergamo route
   - AI companion gets: restaurants (170) + attractions (20) + hotels (from reviews)
   - Verify diverse, non-repetitive suggestions

---

**Status**: ✅ WORKING  
**Test**: PASSED (1000 reviews)  
**Ready**: For full import & RAG integration

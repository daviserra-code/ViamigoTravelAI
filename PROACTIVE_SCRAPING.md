# 🚀 Proactive Scraping System

## Overview

The Proactive Scraping System intelligently manages background data collection using Apify actors to build a comprehensive local database. This reduces real-time API calls, improves response times, and cuts costs.

## Key Features

### 1. **Intelligent Cache Management**
- Automatically identifies cities with missing, old, or insufficient data
- Prioritizes cities based on user access patterns
- Maintains fresh data for popular destinations

### 2. **Multi-Strategy Scraping**

#### Strategy A: User-Driven
- Analyzes which cities users request most frequently
- Pre-caches data for high-traffic destinations
- Focuses on places users actually need

#### Strategy B: Gap-Filling
- Finds missing data in the database
- Refreshes old cache entries (>30-90 days)
- Ensures comprehensive coverage of popular cities

### 3. **Smart Coverage Analysis**
- Tracks database health metrics
- Provides actionable recommendations
- Monitors cache freshness and completeness

## Architecture

```
┌─────────────────────────────────────────────────────┐
│          User Requests Travel Data                  │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│     Check PostgreSQL Cache First                    │
│     (Fast, Free, Always Available)                  │
└───────────┬────────────────┬────────────────────────┘
            │                │
    Cache HIT ✅            Cache MISS ❌
            │                │
            │                ▼
            │    ┌─────────────────────────────┐
            │    │   Call Apify Actor          │
            │    │   (Real-time scraping)      │
            │    └───────┬─────────────────────┘
            │            │
            │            ▼
            │    ┌─────────────────────────────┐
            │    │   Save to PostgreSQL        │
            │    │   (Build local buffer)      │
            │    └───────┬─────────────────────┘
            │            │
            └────────────┴─────────────────────┐
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │  Return Data     │
                                    └──────────────────┘

┌─────────────────────────────────────────────────────┐
│        Background: Proactive Scraping               │
│                                                     │
│  • Runs periodically (hourly/daily)                │
│  • Scrapes popular cities before users request     │
│  • Refreshes old cache entries                     │
│  • Fills gaps in coverage                          │
└─────────────────────────────────────────────────────┘
```

## Implementation Guide

### Step 1: Enable Proactive Scraping

Add to your `run.py` or `main.py`:

```python
from proactive_scraping import ProactiveScrapingManager, schedule_proactive_scraping
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize scheduler
scheduler = BackgroundScheduler()

# Schedule proactive scraping every 6 hours
scheduler.add_job(
    func=schedule_proactive_scraping,
    trigger="interval",
    hours=6,
    id='proactive_scraping'
)

scheduler.start()
```

### Step 2: Add Admin Routes

Add to your Flask app:

```python
from proactive_scraping import register_proactive_routes

# Register admin routes
register_proactive_routes(app)
```

### Step 3: Manual Triggering

You can manually trigger scraping from Python:

```python
from proactive_scraping import ProactiveScrapingManager

manager = ProactiveScrapingManager()

# Scrape up to 10 city-category pairs
result = manager.run_proactive_scraping(
    max_scrapes=10,
    prioritize_users=True
)

print(f"✅ Scraped {result['successful']} cities successfully")
```

## API Endpoints

### GET `/admin/scraping/status`
Get current database health status

**Response:**
```json
{
  "status": "healthy",
  "stats": {
    "total_cities": 45,
    "total_places": 823,
    "average_age_days": 12.5
  },
  "cities_needing_refresh": 8,
  "recommendations": []
}
```

### POST `/admin/scraping/run`
Manually trigger scraping

**Request:**
```json
{
  "max_scrapes": 10,
  "prioritize_users": true
}
```

**Response:**
```json
{
  "total_attempted": 10,
  "successful": 8,
  "failed": 2
}
```

### GET `/admin/scraping/coverage`
Get detailed coverage statistics

**Response:**
```json
{
  "total_cities": 45,
  "total_places": 823,
  "coverage_by_city": {
    "London": {
      "places": 45,
      "categories": 2
    },
    "Paris": {
      "places": 38,
      "categories": 2
    }
  },
  "average_age_days": 12.5
}
```

## Cost Optimization Strategies

### 1. **Smart Cache Duration**
- **Popular cities** (London, Paris): 24 hours
- **Medium cities**: 7 days  
- **Rare cities**: 30 days

### 2. **Rate Limiting**
- Max 5-10 scrapes per scheduled run
- Prioritize user-requested cities
- Spread scraping across day to avoid peaks

### 3. **Batch Processing**
- Group similar cities by region
- Scrape during off-peak hours
- Use Apify's bulk pricing when available

### 4. **Intelligent Prioritization**
```
Priority 1: Missing data (no cache at all)
Priority 2: Insufficient data (<5 places)
Priority 3: Old data (>90 days)
Priority 4: Medium-old data (>30 days)
```

## Advanced Features (Future Enhancements)

### 1. **Machine Learning Predictions**
```python
class PredictiveScrapingEngine:
    def predict_next_destinations(self, user_id):
        # Analyze user patterns
        # Predict likely destinations
        # Pre-cache before user searches
        pass
```

### 2. **Seasonal Intelligence**
```python
def get_seasonal_cities(month):
    if month in [6, 7, 8]:  # Summer
        return ['Sardinia', 'Sicily', 'Amalfi Coast']
    elif month in [12, 1, 2]:  # Winter
        return ['Alps', 'Dolomites', 'Val d\'Aosta']
```

### 3. **Real-time Analytics Dashboard**
- Live scraping status
- Cost tracking
- Cache hit/miss ratios
- Data freshness heatmap

### 4. **Smart Data Validation**
```python
def validate_scraped_data(places):
    # Check for:
    # - Missing coordinates
    # - Duplicate entries
    # - Suspicious ratings
    # - Data quality issues
    pass
```

### 5. **Multi-Source Aggregation**
```python
# Combine data from multiple sources
apify_data = scrape_apify('London')
tripadvisor_data = scrape_tripadvisor('London')
google_data = scrape_google('London')

# Merge and deduplicate
final_data = merge_sources([apify_data, tripadvisor_data, google_data])
```

## Monitoring & Alerts

### Set up monitoring:

```python
from proactive_scraping import get_database_health_report

def check_database_health():
    health = get_database_health_report()
    
    if health['status'] == 'needs_attention':
        send_alert(f"Database needs refresh: {health['cities_needing_refresh']} cities")
    
    if health['stats']['average_age_days'] > 60:
        send_alert("Cache is getting stale - schedule refresh")
```

## Best Practices

1. **Start Small**: Begin with 5-10 scrapes per run
2. **Monitor Costs**: Track Apify usage and adjust frequency
3. **Prioritize Users**: Always prioritize cities users actually request
4. **Gradual Expansion**: Add more cities as your user base grows
5. **Quality Over Quantity**: Better to have 20 well-cached cities than 100 partial ones

## Troubleshooting

### Issue: Apify billing errors
**Solution**: The system automatically falls back to cached data

### Issue: Slow scraping
**Solution**: Reduce `max_scrapes` or increase interval between runs

### Issue: Duplicate data
**Solution**: The system uses `cache_key` to prevent duplicates

### Issue: Missing data
**Solution**: Check `get_cities_needing_refresh()` to see what needs scraping

## Example Workflow

```python
from proactive_scraping import ProactiveScrapingManager

# 1. Initialize manager
manager = ProactiveScrapingManager()

# 2. Check what needs scraping
needs_refresh = manager.get_cities_needing_refresh(max_age_days=30)
print(f"Cities needing refresh: {len(needs_refresh)}")

# 3. Run proactive scraping
result = manager.run_proactive_scraping(max_scrapes=5)
print(f"Success rate: {result['successful']}/{result['total_attempted']}")

# 4. Check coverage
stats = manager.get_coverage_stats()
print(f"Total cities: {stats['total_cities']}")
print(f"Total places: {stats['total_places']}")

# 5. Get user-driven insights
user_cities = manager.get_user_requested_cities(days=7)
print(f"Popular cities: {[(c, count) for c, _, count in user_cities[:5]]}")
```

## Integration Checklist

- [ ] Install APScheduler: `pip install apscheduler`
- [ ] Add `proactive_scraping.py` to your project
- [ ] Configure scheduler in `run.py`
- [ ] Register admin routes
- [ ] Set up monitoring/logging
- [ ] Test with manual trigger
- [ ] Monitor Apify costs
- [ ] Adjust scraping frequency based on usage

## ROI Analysis

### Without Proactive Scraping:
- Every user request = 1 Apify call
- 1000 requests/day = 1000 Apify calls
- Cost: ~$50-100/month

### With Proactive Scraping:
- Background: 5 cities × 4 times/day = 20 Apify calls
- User requests: 80% cache hit = 200 Apify calls
- Total: 220 Apify calls/month
- Cost: ~$10-20/month
- **Savings: 70-80%**

## Conclusion

The Proactive Scraping System transforms your Apify integration from reactive to proactive, significantly reducing costs while improving user experience through faster response times and better data coverage.

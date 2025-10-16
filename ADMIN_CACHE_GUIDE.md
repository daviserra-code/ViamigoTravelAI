# Admin Cache Population Guide

## Overview

This guide explains how to pre-populate the PostgreSQL database with high-quality Apify data for instant route responses.

## Supported Categories

The system now supports **12 categories** for comprehensive itineraries:

### Core Categories (Default)
- ✅ `restaurant` - Best restaurants and trattorias
- ✅ `tourist_attraction` - Top attractions and sights
- ✅ `hotel` - Hotels and accommodations
- ✅ `cafe` - Cafes and coffee shops
- ✅ `museum` - Museums and galleries

### Additional Categories
- ✅ `monument` - Monuments and landmarks
- ✅ `park` - Parks and gardens
- ✅ `shopping` - Shopping centers and markets
- ✅ `nightlife` - Nightclubs and entertainment
- ✅ `bar` - Bars and pubs
- ✅ `bakery` - Bakeries and pastry shops
- ✅ `church` - Churches and religious sites

**To check supported categories programmatically**:
```bash
curl http://localhost:3000/admin/supported-categories
```

## Why Pre-populate?

**Problem**: Apify calls take 60-70 seconds each
**Solution**: Pre-populate cache once, serve instantly forever

## Setup

1. **Set Admin Secret** in `.env`:

   ```bash
   ADMIN_SECRET=your-super-secret-admin-key-here
   BASE_URL=http://localhost:3000  # or your production URL
   ```

2. **Make script executable**:
   ```bash
   chmod +x populate_cache.py
   ```

## Usage

### Option 1: Check Current Cache Status

```bash
python populate_cache.py --status
```

Output:

```
📊 Current Cache Status
Total cached cities: 3
Total cache entries: 6

Bergamo:
  - tourist_attraction: 15 places (age: 0.5h)
  - restaurant: 10 places (age: 0.5h)
```

### Option 2: Populate a Single City

```bash
python populate_cache.py --city Bergamo
```

Output:

```
📍 Populating Bergamo...
✅ Success!
   Duration: 65.3s
   tourist_attraction: 15 places (newly cached)
   restaurant: 10 places (newly cached)
```

### Option 3: Batch Populate All Italian Cities

```bash
python populate_cache.py --batch --delay 5
```

This will populate 25 common Italian cities:

- Bergamo, Bologna, Verona, Firenze, Pisa, Siena, Lucca, Perugia...
- Estimated time: ~33 minutes
- Creates ~50 cache entries (2 categories × 25 cities)

### Option 4: Custom Cities List

Create a file `my_cities.txt`:

```
Bergamo
Bologna
Verona
```

Then run:

```bash
python populate_cache.py --cities-file my_cities.txt --delay 5
```

## API Endpoints

All admin endpoints require the `X-Admin-Secret` header.

### 1. Populate Single City

```bash
curl -X POST http://localhost:3000/admin/populate-city \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: your-secret-key" \
  -d '{
    "city": "Bergamo",
    "categories": ["tourist_attraction", "restaurant", "hotel", "cafe", "museum"],
    "force_refresh": false
  }'
```

**Parameters**:

- `city` (required): City name
- `categories` (optional): Array of categories (default: `["restaurant", "tourist_attraction", "hotel", "cafe", "museum"]`)
  - See **Supported Categories** section above for full list
- `force_refresh` (optional): Force re-fetch even if cached (default: `false`)

**Response**:

```json
{
  "success": true,
  "city": "Bergamo",
  "results": {
    "tourist_attraction": {
      "cached": false,
      "count": 15,
      "sample": "Città Alta"
    },
    "restaurant": {
      "cached": false,
      "count": 10,
      "sample": "Ristorante Da Mimmo"
    },
    "hotel": {
      "cached": false,
      "count": 8,
      "sample": "Hotel Excelsior San Marco"
    },
    "cafe": {
      "cached": false,
      "count": 5,
      "sample": "Caffè del Tasso"
    },
    "museum": {
      "cached": false,
      "count": 3,
      "sample": "Accademia Carrara"
    }
  },
  "duration_seconds": 120.5
}
```

### 2. Batch Populate Multiple Cities

```bash
curl -X POST http://localhost:3000/admin/populate-cities-batch \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: your-secret-key" \
  -d '{
    "cities": ["Bergamo", "Bologna", "Verona"],
    "categories": ["restaurant", "tourist_attraction", "hotel", "cafe", "museum"],
    "delay_seconds": 5
  }'
```

**Parameters**:

- `cities` (required): Array of city names
- `categories` (optional): Array of categories (default: core 5 categories)
- `delay_seconds` (optional): Delay between API calls (default: `5`)

### 3. Check Cache Status

```bash
curl http://localhost:3000/admin/cache-status \
  -H "X-Admin-Secret: your-secret-key"
```

**Response**:

```json
{
  "success": true,
  "total_cached_cities": 3,
  "total_entries": 6,
  "cities": {
    "bergamo": {
      "tourist_attraction": {
        "count": 15,
        "cache_age_hours": 0.5,
        "created_at": "2025-10-16T17:00:00"
      },
      "restaurant": {
        "count": 10,
        "cache_age_hours": 0.5,
        "created_at": "2025-10-16T17:01:05"
      }
    }
  }
}
```

### 4. Clear Cache

```bash
# Clear specific city + category
curl -X POST http://localhost:3000/admin/clear-cache \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: your-secret-key" \
  -d '{"city": "Bergamo", "category": "tourist_attraction"}'

# Clear all data for a city
curl -X POST http://localhost:3000/admin/clear-cache \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: your-secret-key" \
  -d '{"city": "Bergamo"}'

# Clear ALL cache (use with caution!)
curl -X POST http://localhost:3000/admin/clear-cache \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: your-secret-key" \
  -d '{}'
```

## Workflow

### Initial Setup (One-time)

1. **Populate priority cities** (high traffic):

   ```bash
   python populate_cache.py --city Bergamo
   python populate_cache.py --city Bologna
   python populate_cache.py --city Verona
   ```

2. **Batch populate remaining cities**:

   ```bash
   python populate_cache.py --batch
   ```

3. **Verify**:
   ```bash
   python populate_cache.py --status
   ```

### Ongoing Maintenance

- **Cache Duration**: 7 days (configurable in `apify_integration.py`)
- **Auto-refresh**: Cache expires after 7 days, will be re-fetched on next request
- **Manual refresh**: Use `force_refresh: true` to update stale data

### Performance Benefits

**Before** (no cache):

- First request: 70 seconds ❌
- All requests: 70 seconds ❌

**After** (with pre-populated cache):

- First request: 2-3 seconds ✅ (from PostgreSQL)
- Subsequent requests: < 1 second ✅ (cached)
- Cache hits: Instant ⚡

## Security

- **Never commit** `.env` with real `ADMIN_SECRET`
- **Change default secret** in production
- **Restrict access** to admin endpoints (firewall, VPN, etc.)
- **Monitor usage** of admin endpoints
- **Rate limit** admin endpoints in production

## Troubleshooting

### "Unauthorized" Error

- Check `ADMIN_SECRET` in `.env` matches header value
- Verify header is `X-Admin-Secret` (case-sensitive)

### "Apify is not configured"

- Check `APIFY_API_TOKEN` in `.env`
- Verify Apify account has active billing

### Timeout Errors

- Increase timeout in `populate_cache.py`
- Reduce `delay_seconds` (but watch rate limits)
- Populate cities one-by-one instead of batch

### Poor Quality Data

- Use `force_refresh: true` to re-fetch
- Check Apify actor status at console.apify.com
- Verify city name spelling

## Future Enhancements

1. **Background async refresh**: Auto-refresh cache before expiry
2. **Smart prioritization**: Populate cities based on request frequency
3. **Multi-language support**: Cache data in multiple languages
4. **CDN integration**: Serve cached data from edge locations
5. **Monitoring dashboard**: Track cache hit rates, stale entries

## Summary

With pre-populated cache:

- ✅ **Instant responses** (< 1 second)
- ✅ **High-quality data** (from Google Maps via Apify)
- ✅ **Cost-effective** (pay once, serve millions)
- ✅ **Scalable** (works for any city worldwide)
- ✅ **User-friendly** (no waiting, no timeouts)

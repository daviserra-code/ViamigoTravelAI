# 🏨 Hotels Integration - Implementation Guide

**Date:** November 6, 2025  
**Status:** ✅ Fully Operational

## 📋 Overview

Successfully integrated 161 Milano hotels with 37,138 reviews into ViamigoTravelAI. The system provides comprehensive hotel search, recommendations, and route integration capabilities.

---

## 🎯 Features Implemented

### 1. Hotels as POIs on Routes ✅

Add hotels as accommodation stops in route itineraries.

**Use Cases:**

- Multi-day itineraries with overnight stays
- Lunch/coffee breaks at hotel restaurants
- Starting points for day tours

### 2. Hotels as Starting/Ending Points ✅

Use hotels as route origins or destinations instead of generic addresses.

**Benefits:**

- Better for tourists staying at specific hotels
- Accurate coordinates and names
- Integration with hotel details

### 3. Nearby Hotels for Attractions ✅

Show hotels near any attraction or location.

**Features:**

- Distance-based search (radius in km)
- Rating filters (luxury, premium, mid-range, budget)
- Review count sorting

### 4. Top Hotels Lists ✅

Generate curated hotel lists by category and neighborhood.

**Categories:**

- **Luxury:** 9.0+ rating (25 hotels in Milano)
- **Premium:** 8.5+ rating (36 hotels)
- **Mid-Range:** 8.0+ rating (67 hotels)
- **Budget:** 7.0+ rating (33 hotels)

### 6. Smart Route Optimization ✅

Optimize routes to start/end near user's hotel location.

---

## 🔌 API Endpoints

### Base URL

```
http://localhost:3000/api/hotels
```

### 1. Search Hotels

```http
GET /api/hotels/search
```

**Query Parameters:**

- `city` - City name (default: Milan)
- `q` - Search query (hotel name or address)
- `min_rating` - Minimum rating (default: 8.0)
- `limit` - Max results (default: 10)

**Example:**

```bash
curl "http://localhost:3000/api/hotels/search?city=Milan&q=Gallia"
```

**Response:**

```json
{
  "success": true,
  "count": 2,
  "hotels": [
    {
      "name": "Excelsior Hotel Gallia Luxury Collection Hotel",
      "address": "Piazza Duca D Aosta 9 Central Station 20124 Milan Italy",
      "city": "Milan",
      "latitude": 45.4857027,
      "longitude": 9.2020127,
      "rating": 9.4,
      "review_count": 310,
      "type": "hotel"
    }
  ]
}
```

---

### 2. Nearby Hotels

```http
GET /api/hotels/nearby
```

**Query Parameters:**

- `lat` - Latitude (required)
- `lng` - Longitude (required)
- `radius` - Radius in km (default: 1.0)
- `min_rating` - Minimum rating (default: 8.0)
- `limit` - Max results (default: 10)

**Example:**

```bash
# Hotels near Duomo di Milano
curl "http://localhost:3000/api/hotels/nearby?lat=45.464&lng=9.190&radius=0.5"
```

**Response:**

```json
{
  "success": true,
  "count": 3,
  "hotels": [
    {
      "name": "Room Mate Giulia",
      "rating": 9.3,
      "distance_km": 0.13,
      "review_count": 521
    }
  ],
  "center": { "lat": 45.464, "lng": 9.19 },
  "radius_km": 0.5
}
```

---

### 3. Top Hotels by City

```http
GET /api/hotels/top/{city}
```

**Query Parameters:**

- `category` - luxury/premium/mid-range/budget/all (default: all)
- `limit` - Max results (default: 20)

**Example:**

```bash
curl "http://localhost:3000/api/hotels/top/Milan?category=luxury&limit=5"
```

**Response:**

```json
{
  "success": true,
  "city": "Milan",
  "category": "luxury",
  "count": 5,
  "hotels": [
    {
      "name": "Excelsior Hotel Gallia Luxury Collection",
      "rating": 9.4,
      "review_count": 310,
      "category": "luxury"
    }
  ]
}
```

---

### 4. Hotel Details

```http
GET /api/hotels/details/{hotel_name}
```

**Query Parameters:**

- `city` - City name (optional but recommended)

**Example:**

```bash
curl "http://localhost:3000/api/hotels/details/Hotel%20Berna?city=Milan"
```

**Response:**

```json
{
  "success": true,
  "hotel": {
    "name": "Hotel Berna",
    "address": "Via Napo Torriani 18 Central Station 20124 Milan Italy",
    "city": "Milan",
    "latitude": 45.4826692,
    "longitude": 9.2034371,
    "rating": 9.2,
    "review_count": 1052
  }
}
```

---

### 5. Accommodation Suggestions

```http
POST /api/hotels/accommodation-suggestions
```

**Request Body:**

```json
{
  "lat": 45.464,
  "lng": 9.19,
  "city": "Milan"
}
```

**Response:**

```json
{
  "success": true,
  "count": 5,
  "suggestions": [
    {
      "title": "Nearby: Room Mate Giulia",
      "name": "Room Mate Giulia",
      "description": "Rated 9.3/10 with 521 reviews",
      "latitude": 45.4651,
      "longitude": 9.1895,
      "type": "hotel_suggestion"
    }
  ]
}
```

---

### 6. City Statistics

```http
GET /api/hotels/stats/{city}
```

**Example:**

```bash
curl "http://localhost:3000/api/hotels/stats/Milan"
```

**Response:**

```json
{
  "success": true,
  "city": "Milan",
  "stats": {
    "total_hotels": 161,
    "total_reviews": 37138,
    "average_rating": 8.4,
    "max_rating": 9.4,
    "min_rating": 5.2,
    "by_category": {
      "luxury": 25,
      "premium": 36,
      "mid-range": 67,
      "budget": 33
    }
  }
}
```

---

### 7. Categories Info

```http
GET /api/hotels/categories
```

**Response:**

```json
{
  "success": true,
  "categories": {
    "luxury": {
      "name": "Luxury",
      "min_rating": 9.0,
      "description": "Five-star luxury hotels with exceptional service"
    },
    "premium": {
      "name": "Premium",
      "min_rating": 8.5,
      "description": "High-quality hotels with excellent amenities"
    }
  }
}
```

---

## 💻 Python Integration

### Using the HotelsIntegration Class

```python
from hotels_integration import HotelsIntegration

# Initialize
hotels = HotelsIntegration()

# 1. Get hotels near Duomo
duomo_hotels = hotels.get_hotels_near_location(
    latitude=45.464,
    longitude=9.190,
    radius_km=1.0,
    min_rating=8.5,
    limit=5
)

# 2. Get specific hotel
hotel = hotels.get_hotel_by_name('Hotel Berna', 'Milan')

# 3. Get top luxury hotels
luxury_hotels = hotels.get_top_hotels_by_city(
    city='Milan',
    category='luxury',
    limit=10
)

# 4. Search hotels
results = hotels.search_hotels(
    city='Milan',
    search_term='Gallia',
    min_rating=8.0
)
```

### Adding Hotels to Routes

```python
from hotels_integration import add_hotel_to_route, get_accommodation_suggestions

# Add hotel as starting point
route_with_hotel = add_hotel_to_route(
    route_data=existing_route,
    hotel_name='Hotel Berna',
    city='Milan',
    position='start'
)

# Get accommodation suggestions for a location
suggestions = get_accommodation_suggestions(
    latitude=45.464,
    longitude=9.190,
    city='Milan'
)
```

---

## 📊 Milano Hotels Database

### Statistics

- **Total Hotels:** 161
- **Total Reviews:** 37,138
- **Average Rating:** 8.4/10
- **Coverage:** 100% with coordinates

### Top 10 Hotels by Rating

| #   | Hotel                                    | Rating | Reviews |
| --- | ---------------------------------------- | ------ | ------- |
| 1   | Excelsior Hotel Gallia Luxury Collection | 9.4    | 310     |
| 2   | Room Mate Giulia                         | 9.3    | 521     |
| 3   | UNA Maison Milano                        | 9.3    | 320     |
| 4   | Hotel Spadari Al Duomo                   | 9.3    | 243     |
| 5   | Palazzo Parigi Hotel Grand Spa           | 9.3    | 122     |
| 6   | Hotel Berna                              | 9.2    | 1,052   |
| 7   | Hotel Manzoni                            | 9.2    | 206     |
| 8   | The Yard Milano                          | 9.2    | 181     |
| 9   | Hotel Santa Marta Suites                 | 9.2    | 177     |
| 10  | Armani Hotel Milano                      | 9.2    | 156     |

---

## 🎯 Use Case Examples

### 1. Tourist Arriving at Hotel

```javascript
// User arrives at "Hotel Berna"
// Get hotel coordinates
const hotel = await fetch("/api/hotels/details/Hotel Berna?city=Milan").then(
  (r) => r.json()
);

// Plan route from hotel to Duomo
planRoute({
  start: `${hotel.hotel.latitude},${hotel.hotel.longitude}`,
  startName: hotel.hotel.name,
  end: "Duomo di Milano",
});
```

### 2. Show Nearby Hotels for Attraction

```javascript
// User viewing Duomo di Milano attraction
const nearbyHotels = await fetch(
  "/api/hotels/nearby?lat=45.464&lng=9.190&radius=1.0&limit=5"
).then((r) => r.json());

// Display as "Where to stay nearby" panel
```

### 3. Filter Route by Hotel Category

```javascript
// Planning luxury tour starting from premium hotel
const premiumHotels = await fetch(
  "/api/hotels/top/Milan?category=premium&limit=10"
).then((r) => r.json());

// Let user choose starting hotel
```

### 4. Multi-Day Itinerary

```javascript
// Day 1: Start from Hotel Berna, visit attractions
// Day 2: Different starting point or same hotel
// Show accommodation suggestions for overnight stays
```

---

## 🔧 Technical Details

### Files Created

1. **`hotels_integration.py`** - Core integration module
2. **`hotels_routes.py`** - Flask API endpoints
3. **Updated `run.py`** - Registered hotels blueprint

### Database Schema

**Table:** `hotel_reviews`

- `hotel_name` (text)
- `hotel_address` (text)
- `city` (text)
- `latitude` (double precision)
- `longitude` (double precision)
- `average_score` (double precision)
- `total_reviews` (integer)
- And 9 more review-related columns

### Distance Calculation

Uses **Haversine formula** for accurate distance calculation:

```sql
6371 * acos(
    cos(radians(lat1)) * cos(radians(lat2)) *
    cos(radians(lng2) - radians(lng1)) +
    sin(radians(lat1)) * sin(radians(lat2))
) as distance_km
```

---

## 🚀 Next Steps & Enhancements

### Frontend Integration (TODO)

- [ ] Add hotel search widget to route planner
- [ ] Show hotel markers on map with custom icons
- [ ] "Start from my hotel" button on dashboard
- [ ] "Nearby hotels" panel on attraction detail pages
- [ ] Hotel category filters in UI

### Backend Enhancements (TODO)

- [ ] Cache frequent hotel queries
- [ ] Add hotel photos integration
- [ ] Booking links integration (Booking.com API)
- [ ] Save user's hotel in profile
- [ ] Multi-day itinerary with hotel suggestions

### Review Sentiment Analysis (POSTPONED)

- Extract insights from positive/negative reviews
- Generate neighborhood descriptions from reviews
- Identify trending hotel amenities

---

## ✅ Testing Results

All API endpoints tested and working:

- ✅ Search hotels by name
- ✅ Get nearby hotels with distance
- ✅ Filter by category (luxury/premium/mid-range/budget)
- ✅ Get hotel details
- ✅ City statistics
- ✅ Accommodation suggestions

**Flask app running:** Process ID varies (check with `ps aux | grep python`)  
**API base URL:** `http://localhost:3000/api/hotels`

---

**Implementation completed:** November 6, 2025, 21:57 UTC  
**Status:** Ready for frontend integration 🎉

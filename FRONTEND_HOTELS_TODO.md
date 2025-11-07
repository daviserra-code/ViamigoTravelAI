# 🏨 Frontend Hotels Integration - TODO List

**Target City:** Milano (Testing Phase)  
**Date:** November 7, 2025  
**API Base URL:** `http://localhost:3000/api/hotels`

---

## ⚠️ CRITICAL DESIGN REQUIREMENTS

### 1. Viamigo Identity

**Hotels are ONE feature among many in an AI Intelligent Travel Companion**

- 🚫 **DO NOT** make hotels the primary focus of any page
- ✅ **DO** integrate hotels subtly as a helpful add-on
- ✅ **DO** maintain focus on AI-powered route planning and travel companion features
- ✅ **DO** position hotels as convenience features, not the main product

### 2. Graceful Degradation for Cities Without Hotel Data

**MANDATORY:** All hotel features must check data availability first

```javascript
// Example: Check if city has hotel data before showing features
const checkHotelAvailability = async (city) => {
  const stats = await hotelsAPI.stats(city);
  return stats.success && stats.stats.total_hotels > 0;
};

// Use before showing hotel features
const hasHotels = await checkHotelAvailability("Milan");
if (!hasHotels) {
  // Hide hotel widgets OR show informational message
  showMessage("Hotel data not yet available for this city. Stay tuned!");
}
```

**Implementation Rules:**

- [ ] **Before showing hotel search widget:** Check if city has hotels
- [ ] **Before displaying "Start from Hotel":** Verify city in hotel database
- [ ] **On nearby hotels button:** Disable if city has no data
- [ ] **Accommodation suggestions:** Return empty gracefully with message
- [ ] **Map markers:** Only show hotel layer if data exists

**Warning Messages (Non-Intrusive):**

```
ℹ️ Hotel recommendations available for: Milan, Rome
   More cities coming soon!
```

```
💡 Hotels feature currently limited to Milan
   Exploring [CurrentCity] without accommodation suggestions
```

### 3. Current Look & Feel Compliance

**MANDATORY:** All new components must match existing Viamigo design system

- [ ] **Color Palette:** Use exact colors from current theme
- [ ] **Typography:** Match existing font families, sizes, weights
- [ ] **Icons:** Use same icon library (FontAwesome/Material/Heroicons)
- [ ] **Spacing:** Follow existing margin/padding patterns
- [ ] **Buttons:** Same style, hover states, and corner radius
- [ ] **Cards:** Match existing card component design
- [ ] **Modals:** Use existing modal component structure
- [ ] **Animations:** Replicate transition speeds and easing
- [ ] **Responsive Breakpoints:** Use same mobile/tablet/desktop breakpoints

**Before Starting Development:**

1. [ ] Extract design tokens from existing components (colors.css, theme.js)
2. [ ] Document current component patterns (Button, Card, Modal, etc.)
3. [ ] Create hotel components using existing base components
4. [ ] Review with design lead before implementing

---

## 📋 Phase 1: Core Hotel Search Widget (Milano Only)

### 1.1 Hotel Search Component

- [ ] Create `HotelSearchWidget.js` component
  - [ ] **⚠️ MANDATORY:** Check city data availability FIRST
  - [ ] Call `GET /api/hotels/stats/{city}` before rendering
  - [ ] If `total_hotels === 0`: Show disabled state with info message
  - [ ] If has hotels: Enable full search functionality
  - [ ] Search input field with autocomplete
  - [ ] City selector (default: Milan, read-only during testing)
  - [ ] Rating filter dropdown (All/Luxury/Premium/Mid-Range/Budget)
  - [ ] Results display with cards (name, rating, reviews, distance)
  - [ ] "Select Hotel" button on each result card
  - [ ] **Design:** Reuse existing Viamigo input/card/button components

**API Endpoints:**

- `GET /api/hotels/stats/{city}` ← **CHECK THIS FIRST**
- `GET /api/hotels/search?city=Milan&q={query}&min_rating={rating}`

**UI Mockup (With Data):**

```
┌─────────────────────────────────────┐
│  🔍 Search Hotels in Milan          │
│  [Hotel Berna____________] [Search] │
│                                     │
│  Category: [All ▼]                  │
│                                     │
│  📋 Results (3 found):              │
│  ┌─────────────────────────────┐   │
│  │ Hotel Berna            9.2⭐ │   │
│  │ 1,052 reviews                │   │
│  │ Central Station              │   │
│  │ [Select as Start Point]      │   │
│  └─────────────────────────────┘   │
```

**UI Mockup (No Data - Graceful Degradation):**

```
┌─────────────────────────────────────┐
│  🔍 Search Hotels in Florence       │
│  ┌─────────────────────────────┐   │
│  │ ℹ️  Hotel data not yet       │   │
│  │    available for Florence    │   │
│  │                              │   │
│  │    Currently supported:      │   │
│  │    • Milan (161 hotels)      │   │
│  │    • Rome (coming soon)      │   │
│  │                              │   │
│  │    [Explore Florence Anyway] │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 1.2 Hotel Details Modal

- [ ] Create `HotelDetailsModal.js` component
  - [ ] Display full hotel information (name, address, rating, reviews)
  - [ ] Show location on mini map preview
  - [ ] Display distance from current location (if available)
  - [ ] Action buttons: "Start Route Here" / "End Route Here" / "View Nearby Attractions"
  - [ ] Close button

**API Endpoint:** `GET /api/hotels/details/{hotel_name}?city=Milan`

**UI Mockup:**

```
┌─────────────────────────────────────────────┐
│  Hotel Berna                          [✕]   │
├─────────────────────────────────────────────┤
│  ⭐ 9.2/10  •  1,052 reviews                │
│  📍 Via Napo Torriani 18, Milano            │
│  🗺️ [Mini map showing hotel location]       │
│                                             │
│  Distance from you: 2.3 km                  │
│                                             │
│  [🚀 Start Route From Here]                 │
│  [🏁 End Route Here]                        │
│  [🎯 View Nearby Attractions]               │
└─────────────────────────────────────────────┘
```

---

## 📋 Phase 2: Map Integration

### 2.1 Hotel Markers on Map

- [ ] Add hotel markers to existing map component
  - [ ] Custom hotel icon (🏨 or custom SVG)
  - [ ] Different colors by category (luxury=gold, premium=blue, mid-range=green, budget=gray)
  - [ ] Marker clustering for many hotels
  - [ ] Rating badge on hover (9.2⭐)
  - [ ] Click to open hotel details modal

**API Endpoint:** `GET /api/hotels/search?city=Milan&limit=100` (get all hotels for map)

### 2.2 "Show Nearby Hotels" Feature

- [ ] Add button to attraction detail pages: "🏨 Show Nearby Hotels"
  - [ ] When clicked, fetch hotels within 1km radius
  - [ ] Display markers on map with distance lines
  - [ ] List results in sidebar panel
  - [ ] Sort by distance (closest first)

**API Endpoint:** `GET /api/hotels/nearby?lat={lat}&lng={lng}&radius=1.0`

**UI Mockup:**

```
┌──────────────────┬──────────────────────┐
│  🏛️ Duomo Milano │  🗺️ [Map with pins] │
│                  │                      │
│  Description...  │  🏨 Hotel markers    │
│                  │  📍 Duomo marker     │
│  [🏨 Show Hotels]│  ───── distance lines│
│                  │                      │
│  📋 Nearby:      │                      │
│  • Hotel 1 (0.2km)                     │
│  • Hotel 2 (0.5km)                     │
└──────────────────┴──────────────────────┘
```

---

## 📋 Phase 3: Route Planning Integration

### 3.1 "Start from My Hotel" Feature

- [ ] Add dropdown in route planner header
  - [ ] "📍 Starting Point: [Select Hotel ▼]"
  - [ ] Populate with top 20 hotels (sorted by rating)
  - [ ] When selected, auto-fill start coordinates
  - [ ] Show selected hotel name and icon

**API Endpoint:** `GET /api/hotels/top/Milan?limit=20`

**UI Mockup:**

```
┌─────────────────────────────────────────┐
│  Plan Your Milano Route                 │
├─────────────────────────────────────────┤
│  📍 Start: [Hotel Berna ▼] [📍 or GPS] │
│  🎯 End:   [Duomo di Milano ▼]          │
│                                         │
│  ✅ Include: [Attractions] [Restaurants]│
│                                         │
│  [🚀 Generate Route]                    │
└─────────────────────────────────────────┘
```

### 3.2 "End at Hotel" Feature

- [ ] Add hotel selector for route ending point
  - [ ] Same dropdown as start point
  - [ ] Option to "End at same hotel" checkbox
  - [ ] Display on map with different icon (🏁)

### 3.3 Accommodation Suggestions in Route

- [ ] After generating route, show "Where to Stay" panel
  - [ ] Display 5 recommended hotels near route
  - [ ] Calculate average distance from all route stops
  - [ ] Show "Best positioned for your route" badge
  - [ ] Click to add as start/end point and regenerate

**API Endpoint:** `POST /api/hotels/accommodation-suggestions` with route coordinates

**UI Mockup:**

```
┌─────────────────────────────────────────┐
│  Your Milano Route (6 stops)            │
├─────────────────────────────────────────┤
│  1. Duomo → 2. Castello → 3. Brera...  │
│                                         │
│  💡 Where to Stay Near Your Route:      │
│  ┌───────────────────────────────────┐ │
│  │ ⭐ Room Mate Giulia        9.3/10 │ │
│  │ 📍 0.3km avg from route stops     │ │
│  │ 🏆 Best positioned for your route │ │
│  │ [Use as Starting Point]           │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 📋 Phase 4: Category Filtering & Discovery

### 4.1 "Top Hotels" Page

- [ ] Create dedicated page: `/hotels/milan`
  - [ ] Category tabs: All | Luxury | Premium | Mid-Range | Budget
  - [ ] Display category definition (rating thresholds)
  - [ ] Grid view with hotel cards (6 per row)
  - [ ] Pagination (20 hotels per page)
  - [ ] Sort options: Rating | Reviews | Distance from center

**API Endpoints:**

- `GET /api/hotels/top/Milan?category=luxury`
- `GET /api/hotels/categories` (for definitions)

**UI Mockup:**

```
┌─────────────────────────────────────────────────┐
│  🏨 Top Hotels in Milano                        │
├─────────────────────────────────────────────────┤
│  [All] [Luxury] [Premium] [Mid-Range] [Budget] │
│                                                 │
│  Showing: Luxury Hotels (9.0+ rating)           │
│  Found: 25 hotels                               │
│                                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │Hotel │ │Hotel │ │Hotel │ │Hotel │          │
│  │  1   │ │  2   │ │  3   │ │  4   │          │
│  │ 9.4⭐│ │ 9.3⭐│ │ 9.3⭐│ │ 9.3⭐│          │
│  └──────┘ └──────┘ └──────┘ └──────┘          │
│                                                 │
│  [1] 2 3 ... 5 →                                │
└─────────────────────────────────────────────────┘
```

### 4.2 Hotel Statistics Dashboard

- [ ] Add Milano stats widget to dashboard
  - [ ] Display total hotels count
  - [ ] Show average rating
  - [ ] Category breakdown pie chart
  - [ ] Total reviews count
  - [ ] Link to full hotels page

**API Endpoint:** `GET /api/hotels/stats/Milan`

**UI Mockup:**

```
┌──────────────────────────┐
│  🏨 Milano Hotels        │
├──────────────────────────┤
│  Total: 161 hotels       │
│  Average: ⭐ 8.4/10      │
│  Reviews: 37,138         │
│                          │
│  [Pie Chart]             │
│  • Luxury: 25 (15%)      │
│  • Premium: 36 (22%)     │
│  • Mid-Range: 67 (42%)   │
│  • Budget: 33 (21%)      │
│                          │
│  [Explore Hotels →]      │
└──────────────────────────┘
```

---

## 📋 Phase 5: User Experience Enhancements

### 5.1 Save Favorite Hotels

- [ ] Add "❤️ Save" button to hotel cards
  - [ ] Store in localStorage (or user profile if logged in)
  - [ ] Display saved hotels in dedicated section
  - [ ] Quick access from route planner

### 5.2 Hotel Comparison Tool

- [ ] Allow selecting 2-3 hotels for side-by-side comparison
  - [ ] Compare: Rating, Reviews, Distance, Price (if available)
  - [ ] Visual table layout
  - [ ] "Choose this one" button

### 5.3 Distance Calculator

- [ ] Show distance from hotel to all major attractions
  - [ ] Table view: "Distance from [Hotel Name]"
  - [ ] Sorted by distance
  - [ ] Walking time estimates (5 km/h average)
  - [ ] Transit options (if available)

**Calculation:** Use existing hotel coordinates + attraction coordinates

---

## 📋 Phase 6: Mobile Optimization

### 6.1 Mobile Hotel Search

- [ ] Responsive design for search widget
  - [ ] Full-screen modal on mobile
  - [ ] Swipeable hotel cards
  - [ ] Bottom sheet for filters
  - [ ] "Call Hotel" button (tel: link)

### 6.2 Location-Based Search

- [ ] "Find Hotels Near Me" button
  - [ ] Request user location permission
  - [ ] Fetch nearby hotels within 2km
  - [ ] Sort by distance
  - [ ] Show walking directions

**API Endpoint:** `GET /api/hotels/nearby?lat={user_lat}&lng={user_lng}&radius=2.0`

---

## 🧪 Phase 7: Testing Checklist (Milano Only)

### 7.1 Functional Testing

- [ ] Test search with various hotel names (exact match, partial match)
- [ ] Verify category filtering (luxury, premium, mid-range, budget)
- [ ] Test nearby hotels with different radii (0.5km, 1km, 2km)
- [ ] Confirm route planning with hotel start/end points
- [ ] Test accommodation suggestions for 5 different routes
- [ ] Verify map markers display correctly with clustering
- [ ] Test hotel details modal with all 161 Milano hotels

### 7.2 Performance Testing

- [ ] Load time for hotel search results (<500ms)
- [ ] Map rendering with 161 hotel markers (<1s)
- [ ] Nearby hotels query response time (<300ms)
- [ ] Mobile responsiveness on 3 devices (phone, tablet, desktop)

### 7.3 Edge Cases

- [ ] Search with no results (e.g., "Zzzzz Hotel")
- [ ] Nearby hotels with radius covering no hotels
- [ ] Hotels with missing coordinates (should not exist, verify)
- [ ] Hotels with very long names (test UI overflow)
- [ ] Unicode characters in hotel names (e.g., "Château")

### 7.4 Data Validation

- [ ] Verify all 161 Milano hotels appear in search
- [ ] Confirm rating range (5.2 to 9.4)
- [ ] Check total reviews sum (37,138)
- [ ] Validate category counts (25+36+67+33 = 161)
- [ ] Test with top 10 hotels from documentation

---

## 🚀 Phase 8: Scaling to Other Cities (Future)

### 8.1 Database Expansion

- [ ] **Import Rome hotels** (835 reviews already in DB)

  - [ ] Verify coordinates coverage
  - [ ] Test API with `city=Rome`
  - [ ] Update category thresholds if needed

- [ ] **Import other Italian cities:**
  - [ ] Torino (need data import)
  - [ ] Genova (need data import)
  - [ ] Bologna (need data import)
  - [ ] Firenze (need data import)
  - [ ] Venezia (need data import)
  - [ ] Napoli (need data import)

### 8.2 Multi-City Support

- [ ] Make city selector functional (not read-only)
- [ ] Add city autocomplete in search widget
- [ ] Update "Top Hotels" page with city tabs
- [ ] Create city comparison feature
- [ ] Add "Hotels in [City]" landing pages

### 8.3 API Adjustments

- [ ] Verify all endpoints work with city parameter
- [ ] Add `/api/hotels/cities` endpoint (list available cities)
- [ ] Create stats comparison: `GET /api/hotels/stats/compare?cities=Milan,Rome`

---

## 📝 Technical Implementation Notes

### Required Frontend Files

```
src/
  components/
    hotels/
      HotelSearchWidget.js          ← Phase 1.1
      HotelDetailsModal.js           ← Phase 1.2
      HotelMarker.js                 ← Phase 2.1
      NearbyHotelsPanel.js           ← Phase 2.2
      HotelDropdown.js               ← Phase 3.1
      AccommodationSuggestions.js    ← Phase 3.3
      TopHotelsPage.js               ← Phase 4.1
      HotelStatsWidget.js            ← Phase 4.2
  services/
    hotelsAPI.js                     ← API client wrapper
  utils/
    hotelHelpers.js                  ← Distance calc, formatting
```

### API Client Wrapper Example

```javascript
// services/hotelsAPI.js
const BASE_URL = "http://localhost:3000/api/hotels";

export const hotelsAPI = {
  search: (city, query, minRating = 8.0) =>
    fetch(
      `${BASE_URL}/search?city=${city}&q=${query}&min_rating=${minRating}`
    ).then((r) => r.json()),

  nearby: (lat, lng, radius = 1.0) =>
    fetch(`${BASE_URL}/nearby?lat=${lat}&lng=${lng}&radius=${radius}`).then(
      (r) => r.json()
    ),

  top: (city, category = "all", limit = 20) =>
    fetch(`${BASE_URL}/top/${city}?category=${category}&limit=${limit}`).then(
      (r) => r.json()
    ),

  details: (hotelName, city) =>
    fetch(
      `${BASE_URL}/details/${encodeURIComponent(hotelName)}?city=${city}`
    ).then((r) => r.json()),

  stats: (city) => fetch(`${BASE_URL}/stats/${city}`).then((r) => r.json()),

  suggestions: (coordinates, city) =>
    fetch(`${BASE_URL}/accommodation-suggestions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lat: coordinates.lat,
        lng: coordinates.lng,
        city,
      }),
    }).then((r) => r.json()),
};
```

---

## 🎯 Success Metrics

### Phase 1-3 (Core Features)

- [ ] 90% of users can find and select their hotel
- [ ] Average search completion time <10 seconds
- [ ] "Start from hotel" usage >30% of all routes
- [ ] Nearby hotels feature used >20% on attraction pages

### Phase 4-5 (Discovery)

- [ ] Top Hotels page gets >50 visits per week
- [ ] Average session time on hotels page >2 minutes
- [ ] Category filtering used >40% of searches
- [ ] Saved hotels feature adoption >15%

### Phase 6 (Mobile)

- [ ] Mobile hotel search completion rate >85%
- [ ] Location-based search usage >25% on mobile
- [ ] Mobile bounce rate <30%

---

## 🐛 Known Issues & Limitations (Milano Testing Phase)

1. **City Name Mismatch:**

   - Database uses "Milan" (English)
   - Some users might search "Milano" (Italian)
   - **Solution:** Add city name aliases in frontend

2. **No Hotel Photos:**

   - Hotels currently have no images
   - **Solution:** Phase 9 - integrate Booking.com/TripAdvisor images

3. **No Price Information:**

   - Database doesn't include hotel prices
   - **Solution:** Future integration with booking APIs

4. **Limited Cities:**

   - Only Milan fully tested, Rome has partial data
   - **Solution:** Phase 8 - expand to all major Italian cities

5. **No Real-Time Availability:**
   - Cannot check if hotel has rooms available
   - **Solution:** Add booking.com affiliate links

---

## 📅 Suggested Timeline

**Week 1:** Phase 1 (Core Search) + Phase 2.1 (Map Markers)  
**Week 2:** Phase 2.2 (Nearby Hotels) + Phase 3.1 (Start from Hotel)  
**Week 3:** Phase 3.2-3.3 (End at Hotel + Suggestions)  
**Week 4:** Phase 4 (Category Filtering + Stats)  
**Week 5:** Phase 5 (UX Enhancements) + Phase 6 (Mobile)  
**Week 6:** Phase 7 (Testing & Bug Fixes)  
**Week 7+:** Phase 8 (Scale to Other Cities)

---

## ✅ Quick Start for Developers

1. **Test API endpoints first:**

```bash
# Search hotels
curl "http://localhost:3000/api/hotels/search?city=Milan&q=Berna"

# Get stats
curl "http://localhost:3000/api/hotels/stats/Milan"

# Get nearby (Duomo coordinates)
curl "http://localhost:3000/api/hotels/nearby?lat=45.464&lng=9.190&radius=1.0"
```

2. **Create API wrapper:**

   - Copy `services/hotelsAPI.js` example above
   - Test all 7 endpoints

3. **Start with simplest component:**

   - Build `HotelSearchWidget.js` first
   - Add to existing route planner page
   - Test with real API data

4. **Iterate:**
   - Get user feedback early
   - Prioritize most-used features
   - Monitor API performance

---

**Created:** November 7, 2025  
**Status:** Ready for Frontend Implementation 🚀  
**Test City:** Milano (161 hotels, 37,138 reviews)

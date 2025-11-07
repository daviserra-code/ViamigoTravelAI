# 🎯 Hotels Quick Reference - Developer Cheat Sheet

## ⚡ Before You Code: The 3 Golden Rules

1. **🔍 ALWAYS check availability first**

   ```javascript
   const { available } = await fetch(`/api/hotels/availability/${city}`).then(
     (r) => r.json()
   );
   if (!available) return null; // Hide feature
   ```

2. **🎨 ALWAYS match existing design**

   ```javascript
   // Reuse existing components
   import { Button, Card, Modal } from "../shared";
   // Don't create new styles
   ```

3. **🤖 Hotels = Supporting Feature (not hero)**
   ```javascript
   // ❌ Bad: <h1>Find the Best Hotels</h1>
   // ✅ Good: Small "Start from hotel ▼" dropdown
   ```

---

## 🔌 API Endpoints Quick Reference

```javascript
// 1. CHECK THIS FIRST! (Required before showing any hotel UI)
GET /api/hotels/availability/{city}
→ {available: true/false, hotel_count: 161}

// 2. List all supported cities
GET /api/hotels/supported-cities
→ {cities: [{city: "Milan", hotel_count: 37138}, ...]}

// 3. Search hotels
GET /api/hotels/search?city=Milan&q=Berna&min_rating=8.0
→ {hotels: [{name: "Hotel Berna", rating: 9.2}, ...]}

// 4. Nearby hotels (use attraction coordinates)
GET /api/hotels/nearby?lat=45.464&lng=9.190&radius=1.0
→ {hotels: [{name: "...", distance_km: 0.5}, ...]}

// 5. Top hotels by category
GET /api/hotels/top/Milan?category=luxury&limit=20
→ {hotels: [...], category: "luxury"}

// 6. Hotel details
GET /api/hotels/details/Hotel%20Berna?city=Milan
→ {hotel: {name: "...", address: "...", rating: 9.2}}

// 7. Stats for city
GET /api/hotels/stats/Milan
→ {total_hotels: 161, avg_rating: 8.4, by_category: {...}}
```

---

## 🛠️ Code Snippets (Copy-Paste Ready)

### City Name Normalizer

```javascript
// utils/cityNormalizer.js
const aliases = {
  Milano: "Milan",
  Roma: "Rome",
  Firenze: "Florence",
  Venezia: "Venice",
  Torino: "Turin",
  Napoli: "Naples",
};
export const normalizeCity = (city) => aliases[city] || city;
```

### Availability Hook

```javascript
// hooks/useHotelAvailability.js
import { useState, useEffect } from "react";

export function useHotelAvailability(city) {
  const [available, setAvailable] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/hotels/availability/${city}`)
      .then((r) => r.json())
      .then((data) => setAvailable(data.available))
      .finally(() => setLoading(false));
  }, [city]);

  return { available, loading };
}
```

### Conditional Hotel Dropdown

```javascript
// Example: Route Planner Component
function StartPointSelector({ city }) {
  const { available } = useHotelAvailability(city);

  return (
    <select>
      <option>📍 GPS Location</option>
      <option>📫 Enter Address</option>
      {available && <option>🏨 My Hotel</option>}
    </select>
  );
}
```

### Graceful No-Data Message

```javascript
// Show info when city has no hotels
function HotelSection({ city }) {
  const { available, loading } = useHotelAvailability(city);

  if (loading) return <Spinner />;
  if (!available) {
    return <InfoBox>ℹ️ Hotels available in: Milan, Rome</InfoBox>;
  }

  return <HotelSearch city={city} />;
}
```

---

## 🎨 UI Patterns (Match Existing Design!)

### Pattern 1: Subtle Integration

```javascript
// Hotels as PART of route planner, not separate page
<RoutePlanner>
  <StartPoint>
    <LocationPicker />
    {hasHotels && <HotelPicker />} ← Small addition
  </StartPoint>
</RoutePlanner>
```

### Pattern 2: Collapsible Section

```javascript
// On attraction detail page
<AttractionDetails>
  <Title>Duomo di Milano</Title>
  <Description>...</Description>
  <OpeningHours>...</OpeningHours>

  {hasHotels && (
    <Collapsible title="Nearby Hotels (5)">
      <HotelList />
    </Collapsible>
  )}
</AttractionDetails>
```

### Pattern 3: Info Badge (No Data)

```javascript
// Small, non-intrusive message
<RoutePlanner city="Florence">
  {!hasHotels && (
    <Badge variant="info" size="small">
      🏨 Hotels: Milan, Rome
    </Badge>
  )}
</RoutePlanner>
```

---

## ✅ Pre-Launch Checklist

### Before Committing Code

- [ ] Checked availability in component (`useHotelAvailability`)
- [ ] Tested with Milan (has data) ✓
- [ ] Tested with Florence (no data) ✓
- [ ] Normalized city names (Milano → Milan)
- [ ] Reused existing UI components (Button, Card, Modal)
- [ ] Matched color palette, fonts, spacing
- [ ] Added loading states
- [ ] Added error handling
- [ ] Mobile responsive (tested on 320px width)
- [ ] No console errors or warnings

### Testing Matrix

| City     | Has Data | Expected Behavior                |
| -------- | -------- | -------------------------------- |
| Milan    | ✅ Yes   | Show all hotel features          |
| Milano   | ✅ Yes\* | Normalize to "Milan", then show  |
| Rome     | ✅ Yes   | Show all hotel features          |
| Florence | ❌ No    | Hide features OR show info badge |
| Venice   | ❌ No    | Hide features OR show info badge |

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake #1: Not Checking Availability

```javascript
// BAD - Will crash on Florence
function HotelSearch({ city }) {
  const hotels = await fetchHotels(city); // Fails if no data!
  return <List items={hotels} />;
}
```

### ✅ Fix: Always check first

```javascript
function HotelSearch({ city }) {
  const { available } = useHotelAvailability(city);
  if (!available) return null;

  const hotels = await fetchHotels(city);
  return <List items={hotels} />;
}
```

---

### ❌ Mistake #2: Hotel-Centric UI

```javascript
// BAD - Makes hotels the main feature
<Header>
  <Logo />
  <HotelSearchBar /> ← Too prominent!
  <Nav>Hotels | Deals | Book Now</Nav>
</Header>
```

### ✅ Fix: AI Companion First

```javascript
<Header>
  <Logo>Viamigo AI Travel Companion</Logo>
  <Nav>Plan Route | Explore | My Trips</Nav>
  {/* Hotels hidden in route planning flow */}
</Header>
```

---

### ❌ Mistake #3: Hardcoded City Names

```javascript
// BAD - Won't work for "Milano"
if (city === "Milan") {
  showHotels();
}
```

### ✅ Fix: Normalize first

```javascript
const normalized = normalizeCity(city);
if (normalized === "Milan") {
  showHotels();
}
```

---

## 📊 Current Data Status (November 2025)

| City      | Status  | Hotels | Reviews | Avg Rating |
| --------- | ------- | ------ | ------- | ---------- |
| **Milan** | ✅ Full | 37,138 | 129M    | 8.4⭐      |
| **Rome**  | ✅ Full | 835    | 891K    | 8.1⭐      |
| Florence  | ❌ None | 0      | 0       | -          |
| Venice    | ❌ None | 0      | 0       | -          |
| Bologna   | ❌ None | 0      | 0       | -          |
| Turin     | ❌ None | 0      | 0       | -          |

**City Name Mapping:**

- Milano → Milan ✅
- Roma → Rome ✅
- Firenze → Florence ⚠️ (but no data yet)

---

## 🔗 Related Documentation

- **Full API Docs:** `HOTELS_INTEGRATION_GUIDE.md`
- **Implementation Guidelines:** `HOTELS_IMPLEMENTATION_GUIDELINES.md`
- **Frontend TODO:** `FRONTEND_HOTELS_TODO.md`
- **Backend Code:** `hotels_integration.py`, `hotels_routes.py`

---

## 💡 Quick Tips

1. **Start Small:** Implement "Start from hotel" dropdown first
2. **Test Early:** Test with Florence (no data) before Milan
3. **Reuse Components:** Don't reinvent Button, Card, Modal
4. **Hide Gracefully:** No error messages, just hide features
5. **Focus on AI:** Hotels enhance the travel companion, not replace it

---

**Questions?** Check `HOTELS_IMPLEMENTATION_GUIDELINES.md` for detailed examples!

**Ready to Code?** Start with `useHotelAvailability` hook! 🚀

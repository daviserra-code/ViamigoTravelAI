#!/usr/bin/env python3
"""Test specifico per Chiavari - geocoding e routing"""

from dynamic_routing import dynamic_router

def test_chiavari_geocoding():
    """Testa il geocoding per Chiavari"""
    print("🔍 TEST GEOCODING CHIAVARI")
    print("=" * 40)
    
    # Test coordinate base Chiavari
    coords = dynamic_router._geocode_location("piazza roma", "chiavari")
    print(f"📍 Piazza Roma, Chiavari: {coords}")
    
    coords = dynamic_router._geocode_location("piazza del mercato", "chiavari") 
    print(f"📍 Piazza del Mercato, Chiavari: {coords}")
    
    coords = dynamic_router._geocode_location("porto", "chiavari")
    print(f"📍 Porto, Chiavari: {coords}")
    
    # Test riconoscimento città
    city = dynamic_router._detect_city_from_coords([44.3177, 9.3241])
    print(f"🏙️ Città detectata da coordinate Chiavari: {city}")

def test_chiavari_itinerary():
    """Testa itinerario per Chiavari"""
    print("\n🗺️ TEST ITINERARIO CHIAVARI")
    print("=" * 40)
    
    itinerary = dynamic_router.generate_personalized_itinerary(
        "Piazza Roma", "Piazza del Mercato", "Chiavari"
    )
    
    if itinerary:
        print(f"✅ Generato itinerario con {len(itinerary)} tappe")
        for step in itinerary:
            if step.get('type') == 'tip':
                print(f"   💡 {step['title']}: {step['description']}")
            else:
                time = step.get('time', 'N/A')
                title = step.get('title', 'N/A')
                coords = step.get('coordinates', [0,0])
                print(f"   {time} - {title}")
                print(f"       📍 [{coords[0]:.4f}, {coords[1]:.4f}]")
    else:
        print("❌ Nessun itinerario generato")

if __name__ == "__main__":
    test_chiavari_geocoding()
    test_chiavari_itinerary()
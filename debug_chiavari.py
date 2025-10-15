#!/usr/bin/env python3
"""Debug completo del sistema Chiavari"""

from routes import detect_city_from_locations
from dynamic_routing import dynamic_router

def debug_city_detection():
    """Debug del riconoscimento città"""
    print("🕵️ DEBUG RICONOSCIMENTO CITTÀ")
    print("=" * 40)
    
    test_cases = [
        ("lungomare", "chiavari"),
        ("piazza roma", "chiavari"), 
        ("piazza del mercato", "chiavari"),
        ("lungomare,chiavari", "piazza roma,chiavari"),
        ("chiavari centro", "chiavari porto")
    ]
    
    for start, end in test_cases:
        detected = detect_city_from_locations(start, end)
        print(f"'{start}' → '{end}' = '{detected}'")

def debug_geocoding():
    """Debug del geocoding"""
    print("\n📍 DEBUG GEOCODING")
    print("=" * 40)
    
    test_locations = [
        ("lungomare", "chiavari"),
        ("piazza roma", "chiavari"),
        ("piazza del mercato", "chiavari"),
        ("centro", "chiavari")
    ]
    
    for location, city in test_locations:
        coords = dynamic_router._geocode_location(location, city)
        print(f"📍 {location}, {city} → {coords}")

def debug_full_itinerary():
    """Debug dell'itinerario completo"""
    print("\n🗺️ DEBUG ITINERARIO COMPLETO")
    print("=" * 40)
    
    # Simula la richiesta come arriva dal frontend
    start = "lungomare,chiavari"
    end = "piazza roma,chiavari"
    
    # Step 1: riconoscimento città
    city = detect_city_from_locations(start, end)
    print(f"1. Città riconosciuta: '{city}'")
    
    # Step 2: geocoding
    start_coords = dynamic_router._geocode_location(start, city)
    end_coords = dynamic_router._geocode_location(end, city)
    print(f"2. Start coords: {start_coords}")
    print(f"   End coords: {end_coords}")
    
    # Step 3: generazione itinerario
    itinerary = dynamic_router.generate_personalized_itinerary(start, end, city)
    
    if itinerary:
        print(f"3. Itinerario generato con {len(itinerary)} tappe:")
        for i, step in enumerate(itinerary[:3]):
            if step.get('type') != 'tip':
                title = step.get('title', 'N/A')
                coords = step.get('coordinates', [0,0])
                print(f"   {i+1}. {title} → [{coords[0]:.4f}, {coords[1]:.4f}]")
    else:
        print("3. ❌ Nessun itinerario generato")

if __name__ == "__main__":
    debug_city_detection()
    debug_geocoding()
    debug_full_itinerary()
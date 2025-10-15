#!/usr/bin/env python3
"""
Italian Cities Data Seeding Script
Seeds PostgreSQL database with comprehensive Italian attraction data
to minimize AI hallucinations when Apify actors are down.

Strategy: Tier-based approach
- Tier 1: Major cities (50+ places each)
- Tier 2: Regional capitals (30+ places each)  
- Tier 3: Tourist destinations (20+ places each)
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import json

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

db_url = os.environ.get('DATABASE_URL')
engine = create_engine(db_url)

# TIER 1: Major Italian Cities Data
ITALY_TIER1_DATA = {
    'Milano': [
        {'name': 'Duomo di Milano', 'type': 'attraction', 'lat': 45.4642, 'lon': 9.1900},
        {'name': 'Galleria Vittorio Emanuele II', 'type': 'attraction', 'lat': 45.4656, 'lon': 9.1901},
        {'name': 'Castello Sforzesco', 'type': 'attraction', 'lat': 45.4703, 'lon': 9.1794},
        {'name': 'Teatro alla Scala', 'type': 'attraction', 'lat': 45.4673, 'lon': 9.1896},
        {'name': 'Navigli', 'type': 'attraction', 'lat': 45.4502, 'lon': 9.1812},
        {'name': 'Brera', 'type': 'attraction', 'lat': 45.4721, 'lon': 9.1881},
        {'name': 'Santa Maria delle Grazie', 'type': 'attraction', 'lat': 45.4659, 'lon': 9.1707},
        {'name': 'Pinacoteca di Brera', 'type': 'attraction', 'lat': 45.4721, 'lon': 9.1879},
        {'name': 'Corso Buenos Aires', 'type': 'attraction', 'lat': 45.4812, 'lon': 9.2067},
        {'name': 'Parco Sempione', 'type': 'attraction', 'lat': 45.4729, 'lon': 9.1759},
        {'name': 'Trattoria Milanese', 'type': 'restaurant', 'lat': 45.4654, 'lon': 9.1859},
        {'name': 'Luini Panzerotti', 'type': 'restaurant', 'lat': 45.4654, 'lon': 9.1901},
        {'name': 'Peck', 'type': 'restaurant', 'lat': 45.4638, 'lon': 9.1881},
    ],
    'Roma': [
        {'name': 'Colosseo', 'type': 'attraction', 'lat': 41.8902, 'lon': 12.4922},
        {'name': 'Fontana di Trevi', 'type': 'attraction', 'lat': 41.9009, 'lon': 12.4833},
        {'name': 'Pantheon', 'type': 'attraction', 'lat': 41.8986, 'lon': 12.4769},
        {'name': 'Piazza Navona', 'type': 'attraction', 'lat': 41.8992, 'lon': 12.4731},
        {'name': 'Vaticano', 'type': 'attraction', 'lat': 41.9029, 'lon': 12.4534},
        {'name': 'Cappella Sistina', 'type': 'attraction', 'lat': 41.9029, 'lon': 12.4545},
        {'name': 'Piazza di Spagna', 'type': 'attraction', 'lat': 41.9058, 'lon': 12.4823},
        {'name': 'Fori Imperiali', 'type': 'attraction', 'lat': 41.8926, 'lon': 12.4863},
        {'name': 'Trastevere', 'type': 'attraction', 'lat': 41.8894, 'lon': 12.4681},
        {'name': 'Campo de Fiori', 'type': 'attraction', 'lat': 41.8954, 'lon': 12.4721},
        {'name': 'Villa Borghese', 'type': 'attraction', 'lat': 41.9142, 'lon': 12.4843},
        {'name': 'Castel Sant Angelo', 'type': 'attraction', 'lat': 41.9031, 'lon': 12.4663},
        {'name': 'Da Enzo al 29', 'type': 'restaurant', 'lat': 41.8885, 'lon': 12.4691},
        {'name': 'Roscioli', 'type': 'restaurant', 'lat': 41.8953, 'lon': 12.4724},
    ],
    'Venezia': [
        {'name': 'Piazza San Marco', 'type': 'attraction', 'lat': 45.4341, 'lon': 12.3381},
        {'name': 'Basilica di San Marco', 'type': 'attraction', 'lat': 45.4345, 'lon': 12.3405},
        {'name': 'Palazzo Ducale', 'type': 'attraction', 'lat': 45.4338, 'lon': 12.3405},
        {'name': 'Ponte di Rialto', 'type': 'attraction', 'lat': 45.4381, 'lon': 12.3358},
        {'name': 'Canal Grande', 'type': 'attraction', 'lat': 45.4371, 'lon': 12.3326},
        {'name': 'Ponte dei Sospiri', 'type': 'attraction', 'lat': 45.4340, 'lon': 12.3409},
        {'name': 'Teatro La Fenice', 'type': 'attraction', 'lat': 45.4336, 'lon': 12.3346},
        {'name': 'Gallerie dell Accademia', 'type': 'attraction', 'lat': 45.4314, 'lon': 12.3282},
        {'name': 'Burano', 'type': 'attraction', 'lat': 45.4854, 'lon': 12.4172},
        {'name': 'Murano', 'type': 'attraction', 'lat': 45.4591, 'lon': 12.3534},
        {'name': 'Osteria alle Testiere', 'type': 'restaurant', 'lat': 45.4371, 'lon': 12.3431},
        {'name': 'Antiche Carampane', 'type': 'restaurant', 'lat': 45.4378, 'lon': 12.3301},
    ],
    'Firenze': [
        {'name': 'Duomo di Firenze', 'type': 'attraction', 'lat': 43.7731, 'lon': 11.2560},
        {'name': 'Galleria degli Uffizi', 'type': 'attraction', 'lat': 43.7686, 'lon': 11.2558},
        {'name': 'Ponte Vecchio', 'type': 'attraction', 'lat': 43.7680, 'lon': 11.2530},
        {'name': 'Galleria dell Accademia', 'type': 'attraction', 'lat': 43.7769, 'lon': 11.2590},
        {'name': 'Piazzale Michelangelo', 'type': 'attraction', 'lat': 43.7629, 'lon': 11.2650},
        {'name': 'Palazzo Pitti', 'type': 'attraction', 'lat': 43.7651, 'lon': 11.2498},
        {'name': 'Giardino di Boboli', 'type': 'attraction', 'lat': 43.7624, 'lon': 11.2500},
        {'name': 'Piazza della Signoria', 'type': 'attraction', 'lat': 43.7695, 'lon': 11.2558},
        {'name': 'Basilica di Santa Croce', 'type': 'attraction', 'lat': 43.7686, 'lon': 11.2625},
        {'name': 'Mercato Centrale', 'type': 'attraction', 'lat': 43.7797, 'lon': 11.2531},
        {'name': 'Trattoria Mario', 'type': 'restaurant', 'lat': 43.7800, 'lon': 11.2530},
        {'name': 'All Antico Vinaio', 'type': 'restaurant', 'lat': 43.7692, 'lon': 11.2568},
    ],
    'Napoli': [
        {'name': 'Castel dell Ovo', 'type': 'attraction', 'lat': 40.8283, 'lon': 14.2474},
        {'name': 'Vesuvio', 'type': 'attraction', 'lat': 40.8212, 'lon': 14.4264},
        {'name': 'Pompei', 'type': 'attraction', 'lat': 40.7489, 'lon': 14.4850},
        {'name': 'Museo Archeologico Nazionale', 'type': 'attraction', 'lat': 40.8533, 'lon': 14.2508},
        {'name': 'Spaccanapoli', 'type': 'attraction', 'lat': 40.8481, 'lon': 14.2554},
        {'name': 'Cappella Sansevero', 'type': 'attraction', 'lat': 40.8481, 'lon': 14.2556},
        {'name': 'Piazza del Plebiscito', 'type': 'attraction', 'lat': 40.8353, 'lon': 14.2490},
        {'name': 'Castel Nuovo', 'type': 'attraction', 'lat': 40.8387, 'lon': 14.2526},
        {'name': 'Quartieri Spagnoli', 'type': 'attraction', 'lat': 40.8435, 'lon': 14.2468},
        {'name': 'L Antica Pizzeria da Michele', 'type': 'restaurant', 'lat': 40.8506, 'lon': 14.2610},
        {'name': 'Sorbillo', 'type': 'restaurant', 'lat': 40.8506, 'lon': 14.2567},
    ]
}

def seed_place_data(city, places):
    """Seed place data for a specific city"""
    with engine.begin() as conn:
        for place in places:
            cache_key = f"{city.lower()}_{place['name'].lower().replace(' ', '_')}"
            
            place_data = {
                'name': place['name'],
                'city': city,
                'country': 'Italia',
                'type': place['type'],
                'coordinates': {
                    'lat': place['lat'],
                    'lon': place['lon']
                },
                'priority': 'high',  # Tier 1 data
                'source': 'manual_seed_tier1'
            }
            
            # Check if exists
            result = conn.execute(text(
                "SELECT id FROM place_cache WHERE cache_key = :key"
            ), {'key': cache_key})
            
            if result.fetchone():
                # Update existing
                conn.execute(text("""
                    UPDATE place_cache 
                    SET place_data = :data,
                        city = :city,
                        country = 'Italia',
                        priority_level = 'high',
                        last_accessed = NOW()
                    WHERE cache_key = :key
                """), {
                    'key': cache_key,
                    'data': json.dumps(place_data),
                    'city': city
                })
                print(f"  ✅ Updated: {place['name']}")
            else:
                # Insert new
                conn.execute(text("""
                    INSERT INTO place_cache 
                    (cache_key, place_name, city, country, place_data, priority_level, created_at, last_accessed)
                    VALUES (:key, :name, :city, 'Italia', :data, 'high', NOW(), NOW())
                """), {
                    'key': cache_key,
                    'name': place['name'],
                    'city': city,
                    'data': json.dumps(place_data)
                })
                print(f"  ✅ Inserted: {place['name']}")

def main():
    print("🇮🇹 ITALIAN CITIES DATA SEEDING")
    print("=" * 80)
    print("\n📍 TIER 1: Major Cities (Milano, Roma, Venezia, Firenze, Napoli)")
    print("-" * 80)
    
    for city, places in ITALY_TIER1_DATA.items():
        print(f"\n🏛️  Seeding {city} ({len(places)} places)...")
        seed_place_data(city, places)
        print(f"✅ {city} completed!")
    
    print("\n" + "=" * 80)
    print("✅ TIER 1 SEEDING COMPLETE!")
    print("\nNext steps:")
    print("  - Run audit_db_coverage.py to verify")
    print("  - Add Tier 2 cities (Bologna, Torino, Genova, etc.)")
    print("  - Add Tier 3 tourist destinations")
    print("=" * 80)

if __name__ == "__main__":
    main()

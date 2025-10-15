#!/usr/bin/env python3
"""
Audit PostgreSQL database coverage for Italian and European cities
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

db_url = os.environ.get('DATABASE_URL')
engine = create_engine(db_url)

print('🔍 VIAMIGO DATABASE COVERAGE AUDIT')
print('=' * 80)

with engine.begin() as conn:
    # Check places by city
    result = conn.execute(text('''
        SELECT 
            city, 
            COUNT(*) as place_count,
            STRING_AGG(DISTINCT place_name, ', ' ORDER BY place_name) as sample_places
        FROM place_cache 
        WHERE city IS NOT NULL
        GROUP BY city 
        ORDER BY place_count DESC;
    '''))
    
    places = result.fetchall()
    
    print('\n📍 PLACES BY CITY:')
    print('-' * 80)
    total_places = 0
    italian_cities = []
    european_cities = []
    
    for row in places:
        city, count, samples = row
        total_places += count
        
        # Categorize cities
        if city and city.lower() in ['milano', 'roma', 'venezia', 'firenze', 'napoli', 'torino', 
                             'bologna', 'genova', 'palermo', 'verona', 'pisa', 'siena']:
            italian_cities.append((city, count))
        else:
            european_cities.append((city, count))
        
        print(f'\n{city.upper() if city else "UNKNOWN"}: {count} places')
        if samples:
            sample_list = samples.split(', ')[:5]  # Show first 5
            for sample in sample_list:
                print(f'   - {sample}')
    
    print('\n' + '=' * 80)
    print(f'TOTAL PLACES: {total_places}')
    print(f'Italian cities covered: {len(italian_cities)}')
    print(f'European cities covered: {len(european_cities)}')
    
    # Show detailed breakdown
    if italian_cities:
        print('\nItalian cities with data:')
        for city, count in italian_cities:
            print(f'  {city}: {count} places')
    
    if european_cities:
        print('\nEuropean cities with data:')
        for city, count in european_cities[:10]:  # Top 10
            print(f'  {city}: {count} places')

print('=' * 80)

# Define Italian coverage targets
print('\n\n🇮🇹 ITALIAN COVERAGE STRATEGY:')
print('=' * 80)

italy_tier1 = ['Milano', 'Roma', 'Venezia', 'Firenze', 'Napoli']
italy_tier2 = ['Torino', 'Bologna', 'Genova', 'Palermo', 'Verona', 'Catania', 'Bari']
italy_tier3 = ['Pisa', 'Siena', 'Padova', 'Trieste', 'Perugia', 'Como', 'Amalfi', 
               'Sorrento', 'Cinque Terre', 'Portofino']

print('\nTIER 1 (Major Cities - Target: 50+ attractions each):')
for city in italy_tier1:
    coverage = next((c for c, _ in italian_cities if c.lower() == city.lower()), None)
    status = '✅' if coverage else '❌'
    print(f'{status} {city}')

print('\nTIER 2 (Regional Capitals - Target: 30+ attractions each):')
for city in italy_tier2:
    coverage = next((c for c, _ in italian_cities if c.lower() == city.lower()), None)
    status = '✅' if coverage else '❌'
    print(f'{status} {city}')

print('\nTIER 3 (Tourist Destinations - Target: 20+ attractions each):')
for city in italy_tier3:
    coverage = next((c for c, _ in italian_cities if c.lower() == city.lower()), None)
    status = '✅' if coverage else '❌'
    print(f'{status} {city}')

print('\n' + '=' * 80)

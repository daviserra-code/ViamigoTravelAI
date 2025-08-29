"""
Sistema di scraping economico per Viamigo
Combina API gratuite + Scrapingdog come fallback costoso
"""
import requests
import json
from typing import List, Dict, Optional

class CostEffectiveDataProvider:
    def __init__(self):
        # API gratuite prima
        self.openstreetmap_base = "https://overpass-api.de/api/interpreter"
        self.geoapify_key = None  # 3000 free credits/day
        self.opentripmap_key = None  # Free tourist attractions
        
        # Scraping economico solo se necessario  
        self.scrapingdog_key = None  # $0.33/1K vs $4-12 Apify
        
    def get_places_data(self, city: str, category: str = "restaurant") -> List[Dict]:
        """
        Strategia a cascata: FREE APIs → Economico scraping solo se necessario
        """
        # 1. GRATIS: OpenStreetMap + Overpass API
        osm_data = self._get_osm_places(city, category)
        if len(osm_data) >= 5:  # Abbastanza dati
            print(f"✅ Dati sufficienti da OSM gratuito: {len(osm_data)} luoghi")
            return osm_data
            
        # 2. GRATIS: Geoapify (3000 crediti/giorno)
        if self.geoapify_key:
            geo_data = self._get_geoapify_places(city, category)
            if len(geo_data) >= 5:
                print(f"✅ Dati sufficienti da Geoapify: {len(geo_data)} luoghi")
                return geo_data
        
        # 3. ECONOMICO: Scrapingdog (solo se necessario)
        if self.scrapingdog_key and len(osm_data) < 3:
            print(f"⚠️ Dati insufficienti ({len(osm_data)}), usando Scrapingdog economico")
            return self._get_scrapingdog_places(city, category)
            
        # 4. Fallback: Dati OSM anche se pochi
        print(f"💰 Nessun scraping costoso - usando {len(osm_data)} luoghi OSM")
        return osm_data
    
    def _get_osm_places(self, city: str, category: str) -> List[Dict]:
        """OpenStreetMap Overpass API - Completamente GRATUITO"""
        try:
            # Mappa categorie a tag OSM
            osm_tags = {
                'restaurant': 'amenity="restaurant"',
                'tourist_attraction': 'tourism="attraction"',
                'hotel': 'tourism="hotel"'
            }
            
            tag = osm_tags.get(category, 'amenity="restaurant"')
            
            # Query Overpass CORRETTA per città mondiali
            if "new york" in city.lower():
                # Per New York specifico
                query = f"""
                [out:json][timeout:15];
                (
                  node[{tag}](bbox:40.6,-74.1,40.8,-73.9);
                  way[{tag}](bbox:40.6,-74.1,40.8,-73.9);
                );
                out center;
                """
            else:
                # Query generica con bounding box
                query = f"""
                [out:json][timeout:15];
                area[name="{city}"][admin_level~"^(4|5|6|7|8)$"];
                (
                  node[{tag}](area);
                  way[{tag}](area);
                );
                out center;
                """
            
            response = requests.post(
                self.openstreetmap_base,
                data={'data': query},
                timeout=15
            )
            
            if response.ok:
                data = response.json()
                places = []
                
                for element in data.get('elements', [])[:10]:  # Max 10
                    place = {
                        'name': element.get('tags', {}).get('name', 'Unknown'),
                        'latitude': element.get('lat') or element.get('center', {}).get('lat'),
                        'longitude': element.get('lon') or element.get('center', {}).get('lon'),
                        'description': f"Luogo di interesse a {city}",
                        'source': 'openstreetmap_free',
                        'category': category
                    }
                    
                    if place['latitude'] and place['longitude']:
                        places.append(place)
                
                return places
                
        except Exception as e:
            print(f"❌ Errore OSM: {e}")
            return []
    
    def _get_geoapify_places(self, city: str, category: str) -> List[Dict]:
        """Geoapify API - 3000 crediti/giorno GRATUITI"""
        if not self.geoapify_key:
            return []
            
        try:
            # Mappa categorie
            geo_categories = {
                'restaurant': 'catering.restaurant',
                'tourist_attraction': 'tourism.sights',
                'hotel': 'accommodation.hotel'
            }
            
            cat = geo_categories.get(category, 'catering.restaurant')
            
            url = f"https://api.geoapify.com/v2/places"
            params = {
                'categories': cat,
                'filter': f'place:{city}',
                'limit': 10,
                'apiKey': self.geoapify_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                places = []
                
                for feature in data.get('features', []):
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    
                    if len(coords) >= 2:
                        place = {
                            'name': props.get('name', 'Unknown'),
                            'latitude': coords[1],
                            'longitude': coords[0],
                            'description': props.get('formatted', f"Luogo a {city}"),
                            'source': 'geoapify_free',
                            'category': category
                        }
                        places.append(place)
                
                return places
                
        except Exception as e:
            print(f"❌ Errore Geoapify: {e}")
            return []
    
    def _get_scrapingdog_places(self, city: str, category: str) -> List[Dict]:
        """Scrapingdog - Economico ($0.33/1K vs $4-12 Apify)"""
        if not self.scrapingdog_key:
            return []
            
        try:
            # Solo quando veramente necessario
            print(f"💰 COSTO: Usando Scrapingdog per {city} - $0.0033 per 10 luoghi")
            
            url = "https://api.scrapingdog.com/google_maps"
            params = {
                'api_key': self.scrapingdog_key,
                'query': f'{category} in {city}',
                'max_results': 10
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.ok:
                data = response.json()
                places = []
                
                for item in data.get('results', []):
                    place = {
                        'name': item.get('title', 'Unknown'),
                        'latitude': item.get('latitude'),
                        'longitude': item.get('longitude'),
                        'description': item.get('snippet', f"Recensioni: {item.get('rating', 'N/A')}"),
                        'rating': item.get('rating'),
                        'source': 'scrapingdog_paid',
                        'category': category
                    }
                    
                    if place['latitude'] and place['longitude']:
                        places.append(place)
                
                return places
                
        except Exception as e:
            print(f"❌ Errore Scrapingdog: {e}")
            return []


# Esempio di costi mensili per Viamigo
def calculate_monthly_costs():
    """
    Calcolo costi mensili per 1000 utenti che fanno 5 ricerche/mese = 5000 ricerche totali
    """
    print("💰 CONFRONTO COSTI MENSILI - 5000 ricerche/mese:")
    print()
    print("❌ APIFY ATTUALE:")
    print("   5000 ricerche × $0.004 = $20/mese + $39 abbonamento = $59/mese")
    print()
    print("✅ SISTEMA ECONOMICO:")
    print("   4000 ricerche → OSM/Geoapify GRATUITO = $0")
    print("   1000 ricerche → Scrapingdog = $0.33")
    print("   TOTALE = $0.33/mese (vs $59)")
    print("   RISPARMIO = 99.4% 🎉")

if __name__ == "__main__":
    calculate_monthly_costs()
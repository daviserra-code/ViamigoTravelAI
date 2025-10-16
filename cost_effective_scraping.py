"""
Sistema di scraping economico per Viamigo
Combina API gratuite + Scrapingdog come fallback costoso
"""
import os
import requests
import json
from typing import List, Dict, Optional


class CostEffectiveDataProvider:
    def __init__(self):
        # API gratuite prima
        self.openstreetmap_base = "https://overpass-api.de/api/interpreter"
        self.geoapify_key = os.environ.get(
            "GEOAPIFY_KEY")  # 3000 free credits/day
        self.opentripmap_key = None  # Free tourist attractions

        # Scraping economico solo se necessario
        self.scrapingdog_key = os.environ.get(
            "SCRAPINGDOG_KEY")  # $0.33/1K vs $4-12 Apify

    def get_places_data(self, city: str, category: str = "restaurant") -> List[Dict]:
        """
        Strategia a cascata: PostgreSQL Cache → FREE APIs → Economico scraping solo se necessario
        """
        # 🚀 PRIORITY 0: Check PostgreSQL cache FIRST (instant + highest quality)
        try:
            from apify_integration import apify_travel
            cached_data = apify_travel.get_cached_places(city, category)
            if cached_data and len(cached_data) >= 3:
                print(
                    f"⚡ CACHE HIT! Using {len(cached_data)} places from PostgreSQL cache for {city}/{category}")
                return cached_data
            else:
                print(
                    f"💾 Cache miss or insufficient data for {city}/{category} (found: {len(cached_data) if cached_data else 0})")
        except Exception as e:
            print(f"⚠️ Cache check failed: {e}")

        # 1. PRIORITÀ: Geoapify (3000 crediti/giorno) - Dati più ricchi
        if self.geoapify_key:
            geo_data = self._get_geoapify_places(city, category)
            if geo_data and len(geo_data) >= 3:  # Soglia più bassa per Geoapify
                print(
                    f"✅ Dati ricchi da Geoapify: {len(geo_data)} luoghi con dettagli")
                return geo_data

        # 2. FALLBACK: OpenStreetMap + Overpass API
        osm_data = self._get_osm_places(city, category)
        if len(osm_data) >= 3:  # Abbastanza dati
            print(f"✅ Dati base da OSM gratuito: {len(osm_data)} luoghi")
            return osm_data

        # 3. ECONOMICO: ScrapingDog (10-30x più economico di Apify!)
        if self.scrapingdog_key and len(osm_data) < 3:
            print(
                f"💰 Dati insufficienti ({len(osm_data)}), usando ScrapingDog economico")
            scraping_data = self._get_scrapingdog_places(city, category)
            if scraping_data and len(scraping_data) >= 2:
                print(
                    f"✅ Dati premium da ScrapingDog: {len(scraping_data)} luoghi ricchi")
                return scraping_data

        # 4. Fallback: Dati OSM anche se pochi (meglio di niente!)
        combined_data = osm_data
        if len(combined_data) == 0:
            combined_data = [{'name': f'Centro {city}', 'latitude': 0, 'longitude': 0,
                              'description': f'Esplora il centro di {city}', 'source': 'fallback', 'category': category}]

        print(f"💰 Usando {len(combined_data)} luoghi disponibili")
        return combined_data

    def _get_osm_places(self, city: str, category: str) -> List[Dict]:
        """OpenStreetMap Overpass API - Completamente GRATUITO"""
        try:
            # 🎯 MULTI-CATEGORY SUPPORT: Mappa categorie a tag OSM
            osm_tags = {
                'restaurant': 'amenity="restaurant"',
                'tourist_attraction': 'tourism="attraction"',
                'hotel': 'tourism="hotel"',
                'cafe': 'amenity="cafe"',
                'museum': 'tourism="museum"',
                'monument': 'historic="monument"',
                'park': 'leisure="park"',
                'shopping': 'shop',
                'nightlife': 'amenity="bar"',
                'bar': 'amenity="bar"',
                'bakery': 'shop="bakery"',
                'church': 'amenity="place_of_worship"'
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
                    lat = element.get('lat') or element.get(
                        'center', {}).get('lat')
                    lon = element.get('lon') or element.get(
                        'center', {}).get('lon')

                    # ✅ FILTRO GEOGRAFICO: Validate coordinates are reasonable
                    if lat is None or lon is None:
                        continue
                    # Basic sanity check for global coordinates
                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        continue

                    tags = element.get('tags', {})
                    name = tags.get('name', 'Unknown')

                    # Filter out garbage data
                    if 'F-84' in name or 'aircraft' in name.lower() or 'thunderstreak' in name.lower():
                        continue
                    if name == 'Unknown' or len(name) < 3:
                        continue

                    # Descrizione più ricca
                    description = f"Luogo di interesse a {city}"
                    if tags.get('cuisine'):
                        description = f"Cucina {tags['cuisine']} a {city}"
                    elif tags.get('tourism'):
                        description = f"Attrazione turistica a {city}"
                    elif tags.get('amenity'):
                        description = f"{tags['amenity'].title()} a {city}"

                    place = {
                        'name': name,
                        'latitude': lat,
                        'longitude': lon,
                        'description': description,
                        'source': 'openstreetmap_free',
                        'category': category,
                        'address': tags.get('addr:street', ''),
                        'rating': tags.get('stars', 'N/A')
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
            # 🎯 MULTI-CATEGORY SUPPORT: Mappa categorie Geoapify
            geo_categories = {
                'restaurant': 'catering.restaurant',
                'tourist_attraction': 'tourism.sights',
                'hotel': 'accommodation.hotel',
                'cafe': 'catering.cafe',
                'museum': 'entertainment.museum',
                'monument': 'tourism.sights',
                'park': 'leisure.park',
                'shopping': 'commercial.shopping_mall',
                'nightlife': 'entertainment.nightclub',
                'bar': 'catering.bar',
                'bakery': 'catering.bakery',
                'church': 'religion.place_of_worship'
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
                        # 🌟 DATI RICCHI da Geoapify
                        datasource = props.get('datasource', {})

                        place = {
                            'name': props.get('name', 'Unknown'),
                            'latitude': coords[1],
                            'longitude': coords[0],
                            'description': props.get('formatted', f"Luogo a {city}"),
                            'source': 'geoapify_premium',
                            'category': category,
                            # 🏆 DETTAGLI EXTRA da Geoapify
                            'address': props.get('address_line2', ''),
                            'district': props.get('district', ''),
                            'postcode': props.get('postcode', ''),
                            'website': props.get('website', ''),
                            'phone': props.get('phone', ''),
                            'opening_hours': datasource.get('raw', {}).get('opening_hours', ''),
                            'cuisine': datasource.get('raw', {}).get('cuisine', ''),
                            'rating': datasource.get('raw', {}).get('rating', ''),
                            'price_level': datasource.get('raw', {}).get('price_level', ''),
                            'place_rank': props.get('rank', {}).get('popularity', 0)
                        }
                        places.append(place)

                return places

        except Exception as e:
            print(f"❌ Errore Geoapify per {city}: {e}")
            return []

    def _get_scrapingdog_places(self, city: str, category: str) -> List[Dict]:
        """Scrapingdog - Economico ($0.33/1K vs $4-12 Apify)"""
        if not self.scrapingdog_key:
            return []

        try:
            # Solo quando veramente necessario
            print(
                f"💰 COSTO: Usando ScrapingDog per {city} - $0.0033 per 10 luoghi")

            url = "https://api.scrapingdog.com/scrape"
            params = {
                'api_key': self.scrapingdog_key,
                'url': f'https://www.google.com/maps/search/{category}+in+{city.replace(" ", "+")}',
                'dynamic': 'false'
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

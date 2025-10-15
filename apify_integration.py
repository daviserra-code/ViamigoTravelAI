"""
VIAMIGO - Integrazione Apify per dati turistici autentici mondiali
Sistema scalabile per qualsiasi destinazione con fallback intelligente
"""
import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from apify_client import ApifyClient
from cost_effective_scraping import CostEffectiveDataProvider
from models import db, PlaceCache
from datetime import datetime, timedelta
from api_error_handler import resilient_api_call, with_cache, cache_apify


class ApifyTravelIntegration:
    """Sistema di integrazione Apify per dati turistici reali"""

    def __init__(self):
        self.api_token = os.environ.get('APIFY_API_TOKEN')
        self.client = ApifyClient(self.api_token) if self.api_token else None
        self.cache_duration = timedelta(days=7)  # Cache per 7 giorni

    def is_available(self) -> bool:
        """Verifica se Apify è configurato e disponibile"""
        available = self.client is not None and self.api_token is not None and len(
            self.api_token) > 10
        print(
            f"🔍 Apify is_available check: client={self.client is not None}, token_exists={bool(self.api_token)}, token_length={len(self.api_token) if self.api_token else 0}, result={available}")
        return available

    def get_cached_places(self, city: str, category: str = 'tourist_attraction') -> List[Dict]:
        """Recupera luoghi dal cache locale con cache più aggressivo per Londra"""
        try:
            # Usa cache_key invece di city + category separati
            cache_key = f"{city.lower()}_{category}"
            cached = PlaceCache.query.filter_by(cache_key=cache_key).first()

            # Per Londra, usa cache più lungo (24 ore) per evitare chiamate Apify lente
            cache_duration = timedelta(hours=24) if city.lower(
            ) == 'london' else self.cache_duration

            if cached and cached.created_at > datetime.now() - cache_duration:
                place_data = json.loads(cached.place_data)
                # Check if we have sufficient data - riduci threshold per Londra
                min_places = 2 if city.lower() == 'london' else 3
                if isinstance(place_data, list) and len(place_data) >= min_places:
                    print(
                        f"✅ Cache hit per {city} - {len(place_data)} luoghi trovati (cache {cache_duration})")
                    return place_data
                else:
                    print(
                        f"⚠️ Cache insufficient per {city} - solo {len(place_data) if isinstance(place_data, list) else 1} luoghi")
                    # Per Londra, mantieni cache anche se insufficiente per evitare Apify lento
                    if city.lower() == 'london' and isinstance(place_data, list) and len(place_data) > 0:
                        print(
                            f"🚀 Using existing London cache to avoid slow Apify call")
                        return place_data
                    # Delete insufficient cache per altre città
                    PlaceCache.query.filter_by(cache_key=cache_key).delete()
                    db.session.commit()
                    return []
            return []
        except Exception as e:
            print(f"⚠️ Errore cache lookup: {e}")
            return []

    def cache_places(self, city: str, category: str, places: List[Dict]) -> None:
        """Salva luoghi nel cache locale"""
        try:
            # Usa cache_key unico invece di fields separati
            cache_key = f"{city.lower()}_{category}"

            # Rimuovi cache vecchio
            PlaceCache.query.filter_by(cache_key=cache_key).delete()

            # Salva come singolo entry JSON
            if places:
                cache_entry = PlaceCache(
                    cache_key=cache_key,
                    place_name=f"{city}_{category}",
                    city=city.lower(),
                    country='IT',
                    place_data=json.dumps(places),
                    priority_level=1,
                    access_count=1,
                    last_accessed=datetime.now(),
                    created_at=datetime.now()
                )
                db.session.add(cache_entry)

            db.session.commit()
            print(
                f"💾 Cache aggiornato per {city} - {len(places)} luoghi salvati")

        except Exception as e:
            print(f"⚠️ Errore cache per {city}: {e}")
            db.session.rollback()

    @resilient_api_call('apify', timeout=45, fallback_data=[])
    @with_cache(cache_apify, lambda self, city, category, max_results: f"apify_gmaps_{city}_{category}_{max_results}")
    def search_google_maps_places(self, city: str, category: str = 'tourist attraction', max_results: int = 15) -> List[Dict]:
        """Cerca luoghi su Google Maps tramite Apify"""
        print(
            f"🔍 APIFY SEARCH CALLED: city='{city}', category='{category}', available={self.is_available()}")

        if not self.is_available():
            print(
                f"❌ APIFY NOT AVAILABLE: client={self.client is not None}, token={bool(self.api_token)}")
            return []

        try:
            # 🌍 TRADUZIONE: Assicura che i codici paese_città siano tradotti
            city_translations = {
                'usa washington d': 'Washington DC, USA',
                'japan tokyo': 'Tokyo, Japan',
                'germany berlin': 'Berlin, Germany',
                'england london': 'London, UK',
                'france paris': 'Paris, France',
                'spain madrid': 'Madrid, Spain',
                'london': 'London, UK',
                'washington dc': 'Washington DC, USA'
            }

            translated_city = city_translations.get(city.lower(), city)

            # Better search queries for different categories
            if category == 'tourist_attraction':
                search_query = f"top attractions {translated_city}"
            elif category == 'restaurant':
                search_query = f"best restaurants {translated_city}"
            else:
                search_query = f"{category} in {translated_city}"

            print(
                f"🔍 Searching Google Maps: {search_query} (tradotto da: {city})")

            # Updated input format for dtrungtin/google-maps-scraper
            run_input = {
                "searchQueries": [search_query],
                # Ensure we get enough results
                "maxCrawledPlacesPerSearch": max(max_results, 20),
                "language": "en",  # Use English for better international results
                "maxReviews": 5,  # Limit reviews to speed up scraping
                "maxImages": 1,   # Minimal images to save time
            }

            print(f"🚀 CALLING APIFY with query: {search_query}")
            print(f"🔧 APIFY INPUT: {run_input}")

            # Use dtrungtin/google-maps-scraper - more reliable and well-maintained
            run = self.client.actor(
                "dtrungtin/google-maps-scraper").call(run_input=run_input)
            print(f"📡 APIFY RUN STARTED: {run.get('id', 'unknown')}")
            print(f"📡 APIFY RUN STATUS: {run}")

            dataset_items = list(self.client.dataset(
                run["defaultDatasetId"]).iterate_items())
            print(f"📊 APIFY RETURNED: {len(dataset_items)} raw items")

            # Debug first few items
            for i, item in enumerate(dataset_items[:2]):
                print(
                    f"📊 APIFY ITEM {i}: {item.get('title', item.get('name', 'Unknown'))} at {item.get('latitude', 'no-lat')}, {item.get('longitude', 'no-lon')}")

            places = []
            for item in dataset_items:
                try:
                    # dtrungtin/google-maps-scraper output format
                    # Fields: title, address, rating, reviewsCount, location (lat/lng), categoryName, website, phoneNumber
                    lat = item.get('latitude') or item.get('lat')
                    lng = item.get('longitude') or item.get(
                        'lng') or item.get('lon')

                    # Check nested location object (dtrungtin format)
                    if not lat or not lng:
                        location = item.get('location', {})
                        lat = lat or location.get(
                            'lat') or location.get('latitude')
                        lng = lng or location.get(
                            'lng') or location.get('longitude')

                    # Convert to float if they're strings
                    try:
                        lat = float(lat) if lat is not None else None
                        lng = float(lng) if lng is not None else None
                    except (ValueError, TypeError):
                        lat = lng = None

                    # Build description from available data
                    description = "Luogo di interesse"
                    reviews_count = item.get(
                        'reviewsCount') or item.get('reviews')
                    rating = item.get('rating') or item.get('totalScore')

                    if reviews_count and rating:
                        description = f"Rating {rating} ⭐ ({reviews_count} recensioni)"
                    elif item.get('address'):
                        description = f"Indirizzo: {item.get('address')}"

                    place = {
                        'name': item.get('title') or item.get('name') or 'Unknown Location',
                        'description': description,
                        'latitude': lat,
                        'longitude': lng,
                        'rating': rating,
                        'address': item.get('address', ''),
                        'category': item.get('categoryName') or item.get('category', category),
                        'website': item.get('website', ''),
                        'phone': item.get('phoneNumber') or item.get('phone', ''),
                        'source': 'google_maps_dtrungtin'
                    }

                    # Validate coordinates before adding
                    if lat is not None and lng is not None and lat != 0 and lng != 0:
                        places.append(place)
                    else:
                        print(
                            f"⚠️ Scartato {place['name']} - coordinate mancanti: lat={lat}, lng={lng}")

                except Exception as item_error:
                    print(
                        f"⚠️ Errore processing item: {item_error}, item: {item}")
                    continue

            print(f"✅ Google Maps: {len(places)} luoghi trovati per {city}")
            return places

        except Exception as e:
            print(f"❌ Errore Google Maps search per {city}: {e}")
            return []

    def search_tripadvisor_places(self, city: str, category: str = 'hotels', max_results: int = 5) -> List[Dict]:
        """Cerca luoghi su TripAdvisor tramite Apify"""
        if not self.is_available():
            return []

        try:
            search_query = f"{city} {category}"
            print(f"🔍 Searching TripAdvisor: {search_query}")

            run_input = {
                "search": search_query,
                "maxItems": max_results,
                "includeReviews": False
            }

            # Usa il TripAdvisor Scraper di Apify
            run = self.client.actor(
                "curious_coder/tripadvisor-scraper").call(run_input=run_input)
            dataset_items = list(self.client.dataset(
                run["defaultDatasetId"]).iterate_items())

            places = []
            for item in dataset_items:
                place = {
                    'name': item.get('name', 'Unknown'),
                    'description': item.get('description', '') or f"Rating {item.get('rating', 'N/A')}",
                    'latitude': item.get('latitude'),
                    'longitude': item.get('longitude'),
                    'rating': item.get('rating'),
                    'address': item.get('address'),
                    'category': category,
                    'source': 'tripadvisor'
                }
                if place['latitude'] and place['longitude']:
                    places.append(place)

            print(f"✅ TripAdvisor: {len(places)} luoghi trovati per {city}")
            return places

        except Exception as e:
            print(f"❌ Errore TripAdvisor search per {city}: {e}")
            return []

    def get_authentic_places(self, city: str, categories: List[str] = None) -> Dict[str, List[Dict]]:
        """Ottiene luoghi autentici per una città usando cache + Apify"""
        if categories is None:
            categories = ['tourist_attraction', 'restaurant', 'hotel']

        result = {}

        # Force refresh for London if we detect insufficient data
        if city.lower() in ['london', 'england london']:
            print(f"🔄 Force refresh for {city} - clearing old cache")
            try:
                from models import PlaceCache
                PlaceCache.query.filter(
                    PlaceCache.city.ilike(f'%{city}%')).delete()
                db.session.commit()
            except Exception as e:
                print(f"⚠️ Cache clear error: {e}")

        for category in categories:
            # 1. Prova cache prima
            cached_places = self.get_cached_places(city, category)
            if cached_places and len(cached_places) >= 3:  # Ensure sufficient data
                result[category] = cached_places
                continue

            # 2. Se no cache, cerca con Apify
            places = []

            # Google Maps per attrazioni e ristoranti
            if category in ['tourist_attraction', 'restaurant']:
                places = self.search_google_maps_places(
                    city, category, max_results=8)

            # TripAdvisor per hotel
            elif category == 'hotel':
                places = self.search_tripadvisor_places(
                    city, 'hotels', max_results=5)

            # Cache i risultati
            if places:
                self.cache_places(city, category, places)
                result[category] = places
            else:
                result[category] = []

        return result

    def generate_authentic_waypoints(self, start: str, end: str, city: str) -> List[Dict]:
        """Genera waypoints autentici usando dati Apify"""
        print(
            f"🌍 APIFY CHIAMATO: Generazione waypoints autentici per {city} ({start} → {end})")
        print(
            f"🌍 APIFY STATUS: Available={self.is_available()}, Token={bool(self.api_token)}")

        # 🌍 TRADUZIONE: Codici paese_città → Nomi città reali per Google Maps
        city_translations = {
            'usa washington d': 'Washington DC',
            'japan tokyo': 'Tokyo',
            'germany berlin': 'Berlin',
            'england london': 'London',
            'france paris': 'Paris',
            'spain madrid': 'Madrid'
        }

        # Usa la traduzione se disponibile, altrimenti il nome originale
        search_city = city_translations.get(city.lower(), city)
        print(
            f"🔍 Traduzione query: '{city}' → '{search_city}' per Google Maps")

        # Ottieni luoghi reali usando il nome città tradotto
        places_data = self.get_authentic_places(
            search_city, ['tourist_attraction', 'restaurant'])

        waypoints = []

        # Punto di partenza
        waypoints.append({
            'time': '09:00',
            'title': start,
            'description': f'Punto di partenza: {start.lower()}',
            'coordinates': self._get_city_center_coords(city),
            'context': f'{start.lower().replace(" ", "_")}_{city.lower()}',
            'transport': 'start'
        })

        # Aggiungi attrazioni autentiche se disponibili
        attractions = places_data.get('tourist_attraction', [])
        restaurants = places_data.get('restaurant', [])

        if not attractions and not restaurants:
            print(
                f"⚠️ ZERO luoghi autentici trovati per {search_city} - fallback semplice")
            # Fallback semplice senza Apify
            return [
                {
                    'time': '09:00',
                    'title': start,
                    'description': f'Punto di partenza: {start.lower()}',
                    'coordinates': self._get_city_center_coords(search_city),
                    'context': f'{start.lower().replace(" ", "_")}_{city.lower()}',
                    'transport': 'start'
                },
                {
                    'time': '15:30',
                    'title': end,
                    'description': f'Destinazione finale: {end.lower()}',
                    'coordinates': self._get_city_center_coords(search_city),
                    'context': f'{end.lower().replace(" ", "_")}_{city.lower()}',
                    'transport': 'walking'
                }
            ]

        print(
            f"✅ Dati autentici: {len(attractions)} attrazioni, {len(restaurants)} ristoranti per {search_city}")

        # Aggiungi attrazioni autentiche
        if attractions:
            # Max 3 attrazioni
            for i, attraction in enumerate(attractions[:3]):
                time_slot = f"{10 + i*2}:00"
                waypoints.append({
                    'time': time_slot,
                    'title': attraction['name'],
                    'description': attraction['description'],
                    'coordinates': [attraction['latitude'], attraction['longitude']],
                    'context': f"{attraction['name'].lower().replace(' ', '_')}_{city.lower()}",
                    'transport': 'walking'
                })

        # Punto finale
        final_coords = self._get_city_center_coords(city)
        if attractions:
            # Usa coordinate dell'ultima attrazione se disponibile
            final_coords = [attractions[-1]['latitude'],
                            attractions[-1]['longitude']]

        waypoints.append({
            'time': '15:30',
            'title': end,
            'description': f'Destinazione finale: {end.lower()}',
            'coordinates': final_coords,
            'context': f'{end.lower().replace(" ", "_")}_{city.lower()}',
            'transport': 'walking'
        })

        # Tip finale
        waypoints.append({
            'type': 'tip',
            'title': f'💡 {city.title()}',
            'description': f'Itinerario autentico per {city.title()} con dati reali da Google Maps e TripAdvisor'
        })

        print(f"✅ {len(waypoints)} waypoints autentici generati per {city}")
        return waypoints

    def _get_city_center_coords(self, city: str) -> List[float]:
        """Ottiene coordinate centro città (fallback)"""
        # Fallback coordinates per città principali
        city_coords = {
            'roma': [41.9028, 12.4964],
            'milano': [45.4642, 9.1900],
            'napoli': [40.8518, 14.2681],
            'palermo': [38.1157, 13.3613],
            'bari': [41.1171, 16.8719],
            'catania': [37.5079, 15.0830],
            'bologna': [44.4949, 11.3426],
            'firenze': [43.7696, 11.2558],
        }

        # 🌍 COORDINATE REALI per destinazioni estere
        foreign_coords = {
            'usa washington d': [38.9072, -77.0369],  # Washington D.C.
            'washington dc': [38.9072, -77.0369],
            'new york': [40.7128, -74.0060],          # New York
            'tokyo': [35.6762, 139.6503],
            'london': [51.5074, -0.1278],
            'paris': [48.8566, 2.3522],
            'berlin': [52.5200, 13.4050],
            'madrid': [40.4168, -3.7038]
        }

        # Controlla coordinate specifiche prima
        if city.lower() in foreign_coords:
            print(
                f"🌍 Coordinate specifiche per {city}: {foreign_coords[city.lower()]}")
            return foreign_coords[city.lower()]

        # Fallback per altre destinazioni estere
        if any(foreign in city.lower() for foreign in ['usa', 'japan', 'germany', 'england', 'france', 'spain']):
            print(
                f"🇺🇸 Destinazione estera generica {city} - usando coordinate Washington D.C.")
            return [38.9072, -77.0369]

        # 🗽 USA coordinates first
        if 'new york' in city.lower() or 'manhattan' in city.lower():
            return [40.7589, -73.9851]  # NYC center
        elif 'washington' in city.lower():
            return [38.9072, -77.0369]

        # Poi coordinate europee/italiane
        # Default Milano invece Genova
        return city_coords.get(city.lower(), [45.4642, 9.1900])


# Istanza globale
apify_travel = ApifyTravelIntegration()

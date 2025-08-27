"""
Sistema di routing dinamico per itinerari personalizzati
Genera percorsi reali basati su start/end dell'utente
"""

import os
import sys
import requests
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

class DynamicRouter:
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.nominatim_base = "https://nominatim.openstreetmap.org"
        
        # Backup geocoding per città italiane principali
        self.city_centers = {
            'roma': [41.9028, 12.4964],
            'milano': [45.4642, 9.1900], 
            'venezia': [45.4408, 12.3155],
            'firenze': [43.7696, 11.2558],
            'torino': [45.0703, 7.6869],
            'genova': [44.4056, 8.9463],
            'napoli': [40.8518, 14.2681],
            'bologna': [44.4949, 11.3426]
        }
    
    def generate_personalized_itinerary(self, start: str, end: str, city: str = "", 
                                       duration: str = "half_day") -> List[Dict]:
        """
        Genera itinerario personalizzato da start a end
        """
        try:
            # 1. Geocoding di start e end
            start_coords = self._geocode_location(start, city)
            end_coords = self._geocode_location(end, city)
            
            if not start_coords or not end_coords:
                return self._fallback_itinerary(start, end, city)
            
            # 2. Determina città se non specificata
            if not city:
                city = self._detect_city_from_coords(start_coords)
            
            # 3. Genera punti intermedi intelligenti
            waypoints = self._generate_smart_waypoints(
                start_coords, end_coords, city, duration
            )
            
            # 4. Costruisci itinerario finale
            itinerary = self._build_itinerary(
                start, end, start_coords, end_coords, waypoints, city
            )
            
            return itinerary
            
        except Exception as e:
            print(f"Errore routing dinamico: {e}")
            return self._fallback_itinerary(start, end, city)
    
    def _geocode_location(self, location: str, city: str = "") -> Optional[Tuple[float, float]]:
        """Geocodifica una località"""
        try:
            # Backup per città italiane note
            location_lower = location.lower()
            for city_name, coords in self.city_centers.items():
                if city_name in location_lower:
                    return coords
            
            # Nominatim geocoding
            query = f"{location}"
            if city:
                query += f", {city}"
            query += ", Italia"
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = requests.get(
                f"{self.nominatim_base}/search", 
                params=params, 
                timeout=5,
                headers={'User-Agent': 'Viamigo/1.0'}
            )
            
            if response.ok and response.json():
                result = response.json()[0]
                return (float(result['lat']), float(result['lon']))
                
        except Exception as e:
            print(f"Errore geocoding {location}: {e}")
        
        return None
    
    def _detect_city_from_coords(self, coords: Tuple[float, float]) -> str:
        """Rileva la città dalle coordinate"""
        lat, lon = coords
        
        # Controllo città italiane principali (raggio ~20km)
        for city_name, city_coords in self.city_centers.items():
            city_lat, city_lon = city_coords
            # Calcolo distanza approssimativa
            if abs(lat - city_lat) < 0.2 and abs(lon - city_lon) < 0.2:
                return city_name.title()
        
        return "Italia"
    
    def _generate_smart_waypoints(self, start_coords: Tuple[float, float], 
                                 end_coords: Tuple[float, float], 
                                 city: str, duration: str) -> List[Dict]:
        """Genera punti intermedi intelligenti usando AI"""
        if not self.openai_api_key:
            return self._generate_basic_waypoints(start_coords, end_coords, city)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Calcola punto medio per riferimento
            mid_lat = (start_coords[0] + end_coords[0]) / 2
            mid_lon = (start_coords[1] + end_coords[1]) / 2
            
            duration_map = {
                'quick': '2-3 ore',
                'half_day': '4-5 ore', 
                'full_day': '8+ ore'
            }
            
            prompt = f"""
            Crea un itinerario turistico personalizzato per {city} in {duration_map.get(duration, '4-5 ore')}.
            
            Area geografica: 
            - Start: {start_coords[0]:.4f}, {start_coords[1]:.4f}
            - End: {end_coords[0]:.4f}, {end_coords[1]:.4f}
            - Centro area: {mid_lat:.4f}, {mid_lon:.4f}
            
            Genera 3-5 punti di interesse principali tra start e end, considerando:
            - Distanza geografica ragionevole
            - Importanza turistica per {city}
            - Facilità di collegamento a piedi/trasporti
            
            Rispondi SOLO con JSON in questo formato:
            {{
                "waypoints": [
                    {{
                        "name": "Nome attrazione",
                        "description": "Breve descrizione (max 80 caratteri)",
                        "estimated_coords": [lat, lon],
                        "visit_duration": "30 min",
                        "transport_from_previous": "walking"
                    }}
                ]
            }}
            
            Coordinate devono essere realistiche per {city}.
            Transport options: walking, metro, bus, tram, funicular
            """
            
            response = client.chat.completions.create(
                model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=600
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            return ai_result.get('waypoints', [])
            
        except Exception as e:
            print(f"Errore AI waypoints: {e}")
            return self._generate_basic_waypoints(start_coords, end_coords, city)
    
    def _generate_basic_waypoints(self, start_coords: Tuple[float, float], 
                                 end_coords: Tuple[float, float], city: str) -> List[Dict]:
        """Genera waypoints base senza AI"""
        mid_lat = (start_coords[0] + end_coords[0]) / 2
        mid_lon = (start_coords[1] + end_coords[1]) / 2
        
        # Waypoints generici per città italiane
        city_waypoints = {
            'roma': ['Centro Storico', 'Piazza di Spagna', 'Campo de\' Fiori'],
            'milano': ['Duomo', 'Galleria Vittorio Emanuele', 'Brera'],
            'venezia': ['Piazza San Marco', 'Ponte di Rialto', 'Dorsoduro'],
            'firenze': ['Piazza del Duomo', 'Ponte Vecchio', 'Piazza della Signoria'],
            'torino': ['Piazza Castello', 'Via Roma', 'Parco del Valentino'],
            'genova': ['Via del Campo', 'Piazza De Ferrari', 'Porto Antico']
        }
        
        city_lower = city.lower()
        names = city_waypoints.get(city_lower, ['Centro Storico', 'Zona Turistica'])
        
        waypoints = []
        for i, name in enumerate(names[:3]):
            # Distribute waypoints between start and end
            factor = (i + 1) / (len(names) + 1)
            lat = start_coords[0] + (end_coords[0] - start_coords[0]) * factor
            lon = start_coords[1] + (end_coords[1] - start_coords[1]) * factor
            
            waypoints.append({
                'name': name,
                'description': f'Esplora {name} e i suoi dintorni',
                'estimated_coords': [lat, lon],
                'visit_duration': '45 min',
                'transport_from_previous': 'walking'
            })
        
        return waypoints
    
    def _build_itinerary(self, start: str, end: str, 
                        start_coords: Tuple[float, float], 
                        end_coords: Tuple[float, float],
                        waypoints: List[Dict], city: str) -> List[Dict]:
        """Costruisce l'itinerario finale"""
        itinerary = []
        current_time = datetime(2025, 1, 1, 9, 0)  # Start at 9 AM
        
        # Starting point
        itinerary.append({
            'time': current_time.strftime('%H:%M'),
            'title': start.title(),
            'description': f'Punto di partenza: {start}',
            'coordinates': list(start_coords),
            'context': self._generate_context_key(start, city),
            'transport': 'start'
        })
        
        # Waypoints
        for waypoint in waypoints:
            current_time += timedelta(minutes=30)  # Travel time
            itinerary.append({
                'time': current_time.strftime('%H:%M'),
                'title': waypoint['name'],
                'description': waypoint['description'],
                'coordinates': waypoint['estimated_coords'],
                'context': self._generate_context_key(waypoint['name'], city),
                'transport': waypoint.get('transport_from_previous', 'walking')
            })
            
            # Add visit duration
            duration_mins = self._parse_duration(waypoint.get('visit_duration', '45 min'))
            current_time += timedelta(minutes=duration_mins)
        
        # Ending point
        current_time += timedelta(minutes=20)  # Final travel
        itinerary.append({
            'time': current_time.strftime('%H:%M'),
            'title': end.title(),
            'description': f'Destinazione finale: {end}',
            'coordinates': list(end_coords),
            'context': self._generate_context_key(end, city),
            'transport': 'walking'
        })
        
        # Add local tips
        itinerary.append({
            'type': 'tip',
            'title': f'💡 {city}',
            'description': f'Itinerario personalizzato generato per il tuo percorso da {start} a {end}'
        })
        
        return itinerary
    
    def _generate_context_key(self, place: str, city: str) -> str:
        """Genera chiave di contesto per il database"""
        place_clean = place.lower().replace(' ', '_').replace('\'', '').replace('.', '')
        city_clean = city.lower()
        return f"{place_clean}_{city_clean}"
    
    def _parse_duration(self, duration_str: str) -> int:
        """Converte stringa durata in minuti"""
        try:
            if 'min' in duration_str:
                return int(duration_str.split()[0])
            elif 'ore' in duration_str or 'hour' in duration_str:
                return int(duration_str.split()[0]) * 60
        except:
            pass
        return 45  # Default 45 minutes
    
    def _fallback_itinerary(self, start: str, end: str, city: str) -> List[Dict]:
        """Itinerario di fallback se tutto fallisce"""
        return [
            {
                'time': '09:00',
                'title': start.title(),
                'description': f'Punto di partenza: {start}',
                'coordinates': [45.0, 9.0],  # Centro Italia
                'context': 'generic_start',
                'transport': 'start'
            },
            {
                'time': '10:30',
                'title': 'Centro storico',
                'description': 'Esplora il centro storico e i monumenti principali',
                'coordinates': [45.001, 9.001],
                'context': 'generic_center',
                'transport': 'walking'
            },
            {
                'time': '12:00',
                'title': end.title(),
                'description': f'Destinazione finale: {end}',
                'coordinates': [45.002, 9.002],
                'context': 'generic_end',
                'transport': 'walking'
            },
            {
                'type': 'tip',
                'title': '💡 Itinerario base',
                'description': 'Per itinerari più dettagliati, specifica meglio la località'
            }
        ]

# Istanza globale
dynamic_router = DynamicRouter()
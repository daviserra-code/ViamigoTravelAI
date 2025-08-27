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
        
        # Database completo città italiane con coordinate precise
        self.city_centers = {
            # Grandi città
            'roma': [41.9028, 12.4964],
            'milano': [45.4642, 9.1900], 
            'venezia': [45.4408, 12.3155],
            'firenze': [43.7696, 11.2558],
            'torino': [45.0703, 7.6869],
            'genova': [44.4056, 8.9463],
            'napoli': [40.8518, 14.2681],
            'bologna': [44.4949, 11.3426],
            # Città medie e piccole Liguria
            'chiavari': [44.3177, 9.3241],
            'rapallo': [44.3488, 9.2297],
            'portofino': [44.3034, 9.2097],
            'cinque terre': [44.1273, 9.7210],
            'la spezia': [44.1056, 9.8248],
            'savona': [44.3076, 8.4814],
            'imperia': [43.8849, 8.0221],
            'sanremo': [43.8150, 7.7767],
            # Toscana
            'pisa': [43.7228, 10.4017],
            'lucca': [43.8430, 10.5020],
            'siena': [43.3188, 11.3307],
            'livorno': [43.5483, 10.3106],
            # Piemonte
            'asti': [44.9003, 8.2060],
            'cuneo': [44.3841, 7.5456],
            'alba': [44.7009, 8.0356],
            # Lombardia
            'bergamo': [45.6983, 9.6773],
            'brescia': [45.5416, 10.2118],
            'como': [45.8081, 9.0852],
            'mantova': [45.1564, 10.7914],
            # Veneto
            'verona': [45.4384, 10.9916],
            'padova': [45.4064, 11.8768],
            'vicenza': [45.5477, 11.5494],
            'treviso': [45.6669, 12.2441],
            # Emilia-Romagna
            'parma': [44.8015, 10.3279],
            'modena': [44.6471, 10.9252],
            'reggio emilia': [44.6989, 10.6297],
            'ferrara': [44.8381, 11.6176],
            'ravenna': [44.4184, 12.2035],
            'rimini': [44.0678, 12.5695]
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
        """Geocodifica una località con database locale e API di backup"""
        try:
            location_lower = location.lower().strip()
            city_lower = city.lower().strip()
            
            # 1. Controllo diretto per città nel database
            if city_lower in self.city_centers:
                return self.city_centers[city_lower]
            
            # 2. Controllo se location contiene il nome di una città (priorità a match esatti)
            for city_name, coords in self.city_centers.items():
                if city_name == city_lower or city_name == location_lower:
                    return coords
            
            # 3. Controllo substring solo se non c'è match esatto
            for city_name, coords in self.city_centers.items():
                if city_name in location_lower or city_name in city_lower:
                    return coords
            
            # 4. Controllo piazze/luoghi specifici con pattern
            location_patterns = {
                'piazza': 'centro',
                'stazione': 'stazione centrale', 
                'porto': 'porto',
                'centro': 'centro storico',
                'duomo': 'cattedrale',
                'castello': 'castello'
            }
            
            # Se la location ha un pattern riconosciuto, usa coordinate città + offset intelligente
            if city_lower in self.city_centers:
                city_coords = self.city_centers[city_lower]
                for pattern, replacement in location_patterns.items():
                    if pattern in location_lower:
                        # Offset diversificato basato su pattern specifici
                        offsets = {
                            'piazza': (0.001, 0.001),
                            'stazione': (-0.003, 0.002), 
                            'porto': (0.002, -0.003),
                            'centro': (0, 0),
                            'duomo': (0.001, -0.001),
                            'castello': (-0.002, -0.002)
                        }
                        offset_lat, offset_lon = offsets.get(pattern, (0.001, 0.001))
                        # Aggiungi variazione basata su nome specifico per unicità
                        unique_offset = (hash(location_lower) % 100) / 100000  # 0.00001-0.001
                        return (
                            city_coords[0] + offset_lat + unique_offset,
                            city_coords[1] + offset_lon + unique_offset
                        )
            
            # 5. Fallback: Nominatim API con query migliorata
            query_parts = []
            if location:
                query_parts.append(location)
            if city:
                query_parts.append(city)
            query_parts.append("Italia")
            
            query = ", ".join(query_parts)
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 3,  # Più risultati per migliore accuratezza
                'addressdetails': 1,
                'bounded': 1,
                'countrycodes': 'it'  # Solo Italia
            }
            
            response = requests.get(
                f"{self.nominatim_base}/search", 
                params=params, 
                timeout=8,
                headers={'User-Agent': 'Viamigo-Travel-App/1.0'}
            )
            
            if response.ok and response.json():
                results = response.json()
                # Prendi il primo risultato che sembra accurato
                for result in results:
                    lat, lon = float(result['lat']), float(result['lon'])
                    # Verifica che sia in Italia (coordinate ragionevoli)
                    if 35.0 <= lat <= 47.0 and 6.0 <= lon <= 19.0:
                        return (lat, lon)
                
        except Exception as e:
            print(f"Errore geocoding {location} in {city}: {e}")
        
        # 6. Ultimo fallback: coordinate centro Italia
        return (42.5, 12.5)
    
    def _detect_city_from_coords(self, coords: Tuple[float, float]) -> str:
        """Rileva la città dalle coordinate con precisione migliorata"""
        lat, lon = coords
        
        best_match = None
        min_distance = float('inf')
        
        # Trova la città più vicina
        for city_name, city_coords in self.city_centers.items():
            city_lat, city_lon = city_coords
            # Calcolo distanza euclidea approssimativa
            distance = ((lat - city_lat) ** 2 + (lon - city_lon) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                best_match = city_name
        
        # Se la distanza è ragionevole (entro ~50km), restituisci la città
        if min_distance < 0.5:  # circa 50km
            return best_match.title()
        
        # Altrimenti, determina regione italiana
        if 40.0 <= lat <= 42.0:
            return "Sud Italia"
        elif 42.0 <= lat <= 45.0:
            return "Centro Italia"  
        elif 45.0 <= lat <= 47.0:
            return "Nord Italia"
        
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
                max_completion_tokens=600
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
        
        # Waypoints specifici per città italiane con coordinate realistiche
        city_waypoints = {
            'roma': ['Centro Storico', 'Piazza di Spagna', 'Campo de\' Fiori'],
            'milano': ['Duomo', 'Galleria Vittorio Emanuele', 'Brera'],
            'venezia': ['Piazza San Marco', 'Ponte di Rialto', 'Dorsoduro'],
            'firenze': ['Piazza del Duomo', 'Ponte Vecchio', 'Piazza della Signoria'],
            'torino': ['Piazza Castello', 'Via Roma', 'Parco del Valentino'],
            'genova': ['Via del Campo', 'Piazza De Ferrari', 'Porto Antico'],
            'chiavari': ['Centro Storico', 'Lungomare', 'Caruggi medievali'],
            'rapallo': ['Lungolago', 'Centro Storico', 'Castello sul Mare'],
            'portofino': ['Piazzetta', 'Chiesa San Giorgio', 'Faro'],
            'cinque terre': ['Monterosso', 'Vernazza', 'Corniglia'],
            'pisa': ['Campo dei Miracoli', 'Lungarni', 'Borgo Stretto'],
            'lucca': ['Mura medievali', 'Piazza Anfiteatro', 'Via Fillungo'],
            'siena': ['Piazza del Campo', 'Duomo', 'Via di Città']
        }
        
        # Usa waypoints della città corretta e distribuisci coordinate realistiche
        city_lower = city.lower()
        if city_lower in self.city_centers:
            base_coords = self.city_centers[city_lower]
            names = city_waypoints.get(city_lower, ['Centro Storico', 'Zona Turistica'])
        else:
            base_coords = start_coords
            names = ['Centro Storico', 'Zona Turistica']
        
        
        waypoints = []
        for i, name in enumerate(names[:3]):
            # Distribuzione intelligente: usa coordinate base della città + offset graduali
            factor = (i + 1) / (len(names) + 1)
            
            # Per città reali, usa coordinate base + piccoli offset realistici
            if city_lower in self.city_centers:
                offset_lat = (i - 1) * 0.003  # ~300m per waypoint
                offset_lon = (i - 1) * 0.003
                lat = base_coords[0] + offset_lat
                lon = base_coords[1] + offset_lon
            else:
                # Fallback: distribuzione tra start e end
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
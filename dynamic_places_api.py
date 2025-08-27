"""
Sistema dinamico per informazioni sui luoghi turistici worldwide
Utilizza API esterne per ottenere dati autentici in tempo reale
"""

import os
import requests
import json
from typing import Dict, List, Optional

class DynamicPlacesAPI:
    def __init__(self):
        # OpenAI per elaborazione intelligente delle informazioni
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        # API per informazioni geografiche e turistiche
        self.nominatim_base = "https://nominatim.openstreetmap.org"
        self.overpass_base = "https://overpass-api.de/api/interpreter"
        
    def get_place_info(self, place_name: str, city: str = "", country: str = "") -> Optional[Dict]:
        """
        Ottiene informazioni dinamiche su un luogo turistico
        usando API geografiche e intelligence AI
        """
        try:
            # 1. Geocoding per ottenere coordinate e informazioni base
            location_data = self._geocode_place(place_name, city, country)
            if not location_data:
                return None
            
            # 2. Ottieni dettagli dal database OpenStreetMap
            osm_details = self._get_osm_details(location_data)
            
            # 3. Elabora informazioni con AI per formato consistente
            enhanced_info = self._enhance_with_ai(place_name, location_data, osm_details)
            
            return enhanced_info
            
        except Exception as e:
            print(f"Errore ottenendo info per {place_name}: {e}")
            return None
    
    def _geocode_place(self, place_name: str, city: str = "", country: str = "") -> Optional[Dict]:
        """Geocodifica il luogo e ottiene informazioni base"""
        query = f"{place_name}"
        if city:
            query += f", {city}"
        if country:
            query += f", {country}"
            
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'extratags': 1,
            'namedetails': 1
        }
        
        try:
            response = requests.get(f"{self.nominatim_base}/search", params=params, timeout=5)
            if response.ok and response.json():
                return response.json()[0]
        except:
            pass
        return None
    
    def _get_osm_details(self, location_data: Dict) -> Dict:
        """Ottiene dettagli aggiuntivi da OpenStreetMap"""
        try:
            lat = float(location_data['lat'])
            lon = float(location_data['lon'])
            
            # Query Overpass per dettagli turistici nell'area
            overpass_query = f"""
            [out:json][timeout:10];
            (
              way["tourism"](around:100,{lat},{lon});
              node["tourism"](around:100,{lat},{lon});
              way["historic"](around:100,{lat},{lon});
              node["historic"](around:100,{lat},{lon});
              way["amenity"="place_of_worship"](around:100,{lat},{lon});
              node["amenity"="place_of_worship"](around:100,{lat},{lon});
            );
            out tags;
            """
            
            response = requests.post(self.overpass_base, data=overpass_query, timeout=10)
            if response.ok:
                return response.json()
        except:
            pass
        return {}
    
    def _enhance_with_ai(self, place_name: str, location_data: Dict, osm_details: Dict) -> Dict:
        """Usa AI per elaborare e strutturare le informazioni"""
        if not self.openai_api_key:
            return self._create_basic_info(place_name, location_data)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Prepara il contesto per l'AI
            context = {
                'place_name': place_name,
                'coordinates': [float(location_data['lat']), float(location_data['lon'])],
                'address': location_data.get('display_name', ''),
                'osm_tags': location_data.get('extratags', {}),
                'category': location_data.get('category', ''),
                'type': location_data.get('type', '')
            }
            
            prompt = f"""
            Crea informazioni turistiche dettagliate per: {place_name}
            
            Contesto disponibile:
            - Posizione: {context['address']}
            - Coordinate: {context['coordinates']}
            - Categoria OSM: {context['category']} / {context['type']}
            
            Genera un JSON con questa struttura ESATTA:
            {{
                "title": "Nome completo del luogo",
                "summary": "Descrizione di 2-3 righe che spiega l'importanza storica/culturale/turistica",
                "details": [
                    {{"label": "Categoria", "value": "Tipo di attrazione"}},
                    {{"label": "Costruzione", "value": "Periodo o data se storico"}},
                    {{"label": "Stile", "value": "Stile architettonico se applicabile"}},
                    {{"label": "Ingresso", "value": "Info su costi o gratuità"}},
                    {{"label": "Curiosità", "value": "Fatto interessante o leggenda"}}
                ],
                "coordinates": {context['coordinates']},
                "timetable": [
                    {{"direction": "Periodo/Stagione", "times": "Orari tipici se applicabile"}}
                ]
            }}
            
            IMPORTANTE:
            - Usa solo informazioni verificabili e generiche per il tipo di luogo
            - Non inventare orari specifici a meno che non siano standard per quel tipo
            - Mantieni il tone informativo ma coinvolgente
            - Se è un luogo storico, includi periodo di costruzione
            - Se è religioso, includi info su visite e rispetto
            """
            
            response = client.chat.completions.create(
                model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=800
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            return ai_response
            
        except Exception as e:
            print(f"Errore AI processing: {e}")
            return self._create_basic_info(place_name, location_data)
    
    def _create_basic_info(self, place_name: str, location_data: Dict) -> Dict:
        """Crea informazioni base senza AI"""
        category = location_data.get('category', 'place')
        place_type = location_data.get('type', 'location')
        
        # Mappatura categorie per descrizioni
        descriptions = {
            'tourism': 'Attrazione turistica',
            'historic': 'Sito storico',
            'amenity': 'Servizio pubblico',
            'building': 'Edificio di interesse',
            'natural': 'Luogo naturale'
        }
        
        return {
            'title': place_name.title(),
            'summary': f'{descriptions.get(category, "Luogo di interesse")} situato in {location_data.get("display_name", "")}.',
            'details': [
                {'label': 'Categoria', 'value': descriptions.get(category, 'Luogo di interesse')},
                {'label': 'Tipo', 'value': place_type.replace('_', ' ').title()},
                {'label': 'Posizione', 'value': location_data.get('display_name', '')},
                {'label': 'Coordinate', 'value': f"{location_data['lat']}, {location_data['lon']}"}
            ],
            'coordinates': [float(location_data['lat']), float(location_data['lon'])],
            'timetable': []
        }

# Istanza globale per uso nell'app
dynamic_places = DynamicPlacesAPI()
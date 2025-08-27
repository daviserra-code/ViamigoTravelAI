"""
Sistema di pre-training per popolare il database locale
con informazioni su destinazioni turistiche principali
"""

import json
import os
from typing import List, Dict
from dynamic_places_api import dynamic_places
from flask_app import app, db
from models import PlaceCache
import time

class PretrainingSystem:
    def __init__(self):
        self.priority_destinations = {
            # Italia - principali
            'italia': [
                ('Colosseo', 'Roma', 'Italia'),
                ('Torre di Pisa', 'Pisa', 'Italia'),
                ('Duomo di Milano', 'Milano', 'Italia'),
                ('Palazzo Ducale', 'Venezia', 'Italia'),
                ('Ponte Vecchio', 'Firenze', 'Italia'),
                ('Teatro La Scala', 'Milano', 'Italia'),
                ('Fontana di Trevi', 'Roma', 'Italia'),
                ('Basilica di San Marco', 'Venezia', 'Italia'),
                ('Uffizi', 'Firenze', 'Italia'),
                ('Duomo di Firenze', 'Firenze', 'Italia'),
                ('Sagrada Familia', 'Barcellona', 'Spagna'),
                ('Torre Eiffel', 'Parigi', 'Francia'),
                ('Big Ben', 'Londra', 'Regno Unito'),
                ('Porta di Brandeburgo', 'Berlino', 'Germania'),
                ('Acropoli', 'Atene', 'Grecia')
            ],
            # Europa - capitali principali
            'europa': [
                ('Notre Dame', 'Parigi', 'Francia'),
                ('Louvre', 'Parigi', 'Francia'),
                ('Tower Bridge', 'Londra', 'Regno Unito'),
                ('British Museum', 'Londra', 'Regno Unito'),
                ('Museo del Prado', 'Madrid', 'Spagna'),
                ('Park Güell', 'Barcellona', 'Spagna'),
                ('Neuschwanstein', 'Baviera', 'Germania'),
                ('Museo Van Gogh', 'Amsterdam', 'Paesi Bassi'),
                ('Castello di Praga', 'Praga', 'Repubblica Ceca'),
                ('Palazzo Schönbrunn', 'Vienna', 'Austria')
            ],
            # Mondo - icone globali
            'mondiale': [
                ('Statua della Libertà', 'New York', 'Stati Uniti'),
                ('Empire State Building', 'New York', 'Stati Uniti'),
                ('Golden Gate Bridge', 'San Francisco', 'Stati Uniti'),
                ('Cristo Redentore', 'Rio de Janeiro', 'Brasile'),
                ('Machu Picchu', 'Cusco', 'Perù'),
                ('Taj Mahal', 'Agra', 'India'),
                ('Grande Muraglia', 'Pechino', 'Cina'),
                ('Opera House', 'Sydney', 'Australia'),
                ('Burj Khalifa', 'Dubai', 'Emirati Arabi'),
                ('Piramidi di Giza', 'Giza', 'Egitto')
            ]
        }
    
    def run_pretraining(self, level='italia', batch_size=5, delay=2):
        """Esegue il pre-training per un livello specifico"""
        destinations = self.priority_destinations.get(level, [])
        
        print(f"🚀 Avvio pre-training livello: {level}")
        print(f"📍 Destinazioni da processare: {len(destinations)}")
        
        with app.app_context():
            processed = 0
            for i in range(0, len(destinations), batch_size):
                batch = destinations[i:i+batch_size]
                
                for place_name, city, country in batch:
                    try:
                        # Controlla se già in cache
                        cache_key = f"{place_name.lower().replace(' ', '_')}_{city.lower()}"
                        existing = PlaceCache.query.filter_by(cache_key=cache_key).first()
                        
                        if existing:
                            print(f"✅ {place_name} già in cache")
                            continue
                        
                        # Ottieni informazioni dinamiche
                        print(f"🔄 Processing: {place_name}, {city}")
                        place_info = dynamic_places.get_place_info(place_name, city, country)
                        
                        if place_info:
                            # Salva in cache database
                            cache_entry = PlaceCache(
                                cache_key=cache_key,
                                place_name=place_name,
                                city=city,
                                country=country,
                                place_data=json.dumps(place_info),
                                priority_level=level
                            )
                            db.session.add(cache_entry)
                            db.session.commit()
                            
                            print(f"💾 Salvato: {place_name} in cache")
                            processed += 1
                        else:
                            print(f"❌ Errore processing: {place_name}")
                        
                        # Delay per evitare rate limiting
                        time.sleep(delay)
                        
                    except Exception as e:
                        print(f"❌ Errore {place_name}: {e}")
                        continue
                
                print(f"📊 Batch completato. Processati: {processed}/{len(destinations)}")
        
        print(f"🎉 Pre-training {level} completato! Processati: {processed} luoghi")
        return processed
    
    def get_cache_stats(self):
        """Statistiche della cache"""
        with app.app_context():
            total = PlaceCache.query.count()
            by_level = db.session.query(
                PlaceCache.priority_level, 
                db.func.count(PlaceCache.id)
            ).group_by(PlaceCache.priority_level).all()
            
            stats = {
                'total_cached': total,
                'by_level': dict(by_level)
            }
            return stats
    
    def clear_cache(self, level=None):
        """Pulisce la cache (tutto o per livello)"""
        with app.app_context():
            if level:
                deleted = PlaceCache.query.filter_by(priority_level=level).delete()
            else:
                deleted = PlaceCache.query.delete()
            db.session.commit()
            return deleted

# Aggiorna il modello per includere il caching
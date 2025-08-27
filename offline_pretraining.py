#!/usr/bin/env python3
"""
Sistema di pre-training offline per popolare il database
con informazioni complete sui luoghi turistici principali
"""

import sys
import json
from flask_app import app, db
from models import PlaceCache

class OfflinePretraining:
    def __init__(self):
        self.destinations_data = {
            # Destinazioni iconiche con dati precompilati
            'colosseo_roma': {
                'place_name': 'Colosseo',
                'city': 'Roma',
                'country': 'Italia',
                'data': {
                    'title': 'Colosseo, Roma',
                    'summary': 'Il più grande anfiteatro del mondo antico, simbolo dell\'Impero Romano. Costruito tra il 70 e l\'80 d.C., poteva ospitare fino a 80.000 spettatori per i combattimenti tra gladiatori.',
                    'details': [
                        {'label': 'Costruzione', 'value': '70-80 d.C. (Imperatori Flavi)'},
                        {'label': 'Capacità originale', 'value': '80.000 spettatori'},
                        {'label': 'Dimensioni', 'value': '189m x 156m, altezza 50m'},
                        {'label': 'Patrimonio UNESCO', 'value': 'Dal 1980'},
                        {'label': 'Biglietto standard', 'value': '€18 (ridotto €4)'},
                        {'label': 'Biglietto arena', 'value': '€24 (include accesso arena)'},
                        {'label': 'Prenotazione', 'value': 'Obbligatoria online'}
                    ],
                    'coordinates': [41.8902, 12.4922],
                    'timetable': [
                        {'direction': 'Gen-Feb, Nov-Dic', 'times': '8:30-16:30'},
                        {'direction': 'Mar-Ott', 'times': '8:30-19:15'},
                        {'direction': 'Ultimo ingresso', 'times': '1 ora prima chiusura'}
                    ],
                    'actionLink': {
                        'text': 'Prenota biglietto ufficiale',
                        'url': 'https://colosseo.it'
                    }
                }
            },
            'torre_pisa': {
                'place_name': 'Torre di Pisa',
                'city': 'Pisa',
                'country': 'Italia',
                'data': {
                    'title': 'Torre Pendente di Pisa',
                    'summary': 'Il campanile della cattedrale di Pisa, famoso in tutto il mondo per la sua caratteristica inclinazione. Capolavoro dell\'architettura romanica pisana del XII secolo.',
                    'details': [
                        {'label': 'Altezza', 'value': '56 metri (lato più basso)'},
                        {'label': 'Inclinazione', 'value': '3,97° (stabilizzata)'},
                        {'label': 'Costruzione', 'value': '1173-1372 (tre fasi)'},
                        {'label': 'Scalini', 'value': '294 gradini fino alla cima'},
                        {'label': 'Peso', 'value': '14.453 tonnellate'},
                        {'label': 'Biglietto salita', 'value': '€25 (30 minuti in cima)'},
                        {'label': 'Patrimonio UNESCO', 'value': 'Piazza dei Miracoli (1987)'}
                    ],
                    'coordinates': [43.7230, 10.3966],
                    'timetable': [
                        {'direction': 'Apr-Set', 'times': '9:00-20:00 (salita ogni 30 min)'},
                        {'direction': 'Ott-Mar', 'times': '9:00-18:00'},
                        {'direction': 'Prenotazione', 'times': 'Obbligatoria con orario specifico'}
                    ]
                }
            },
            'duomo_milano': {
                'place_name': 'Duomo di Milano',
                'city': 'Milano',
                'country': 'Italia',
                'data': {
                    'title': 'Duomo di Milano',
                    'summary': 'La cattedrale gotica più grande d\'Italia, simbolo di Milano. Famosa per le sue guglie elaborate, la Madonnina dorata e la vista panoramica dalle terrazze.',
                    'details': [
                        {'label': 'Costruzione', 'value': '1386-1965 (quasi 6 secoli)'},
                        {'label': 'Stile', 'value': 'Gotico lombardo-renano'},
                        {'label': 'Guglie', 'value': '135 guglie con 3.400 statue'},
                        {'label': 'Madonnina', 'value': 'Statua dorata del 1774 (h. 4m)'},
                        {'label': 'Duomo ingresso', 'value': 'Gratuito (messa e visite)'},
                        {'label': 'Terrazze ascensore', 'value': '€16 (€13 scale)'},
                        {'label': 'Museo', 'value': '€3 (storia della costruzione)'}
                    ],
                    'coordinates': [45.4641, 9.1920],
                    'timetable': [
                        {'direction': 'Cattedrale', 'times': 'Lun-Dom 7:00-19:00'},
                        {'direction': 'Terrazze', 'times': '9:00-19:00 (estate), 9:00-17:30 (inverno)'},
                        {'direction': 'Museo', 'times': 'Gio-Mar 10:00-18:00'}
                    ]
                }
            },
            'palazzo_ducale_venezia': {
                'place_name': 'Palazzo Ducale',
                'city': 'Venezia',
                'country': 'Italia',
                'data': {
                    'title': 'Palazzo Ducale, Venezia',
                    'summary': 'Capolavoro dell\'arte gotica veneziana, antica residenza del Doge. Simbolo della Serenissima con i famosi Ponti dei Sospiri e le prigioni storiche.',
                    'details': [
                        {'label': 'Costruzione', 'value': 'IX sec., ricostruito XIV-XV sec.'},
                        {'label': 'Stile', 'value': 'Gotico veneziano'},
                        {'label': 'Sale principali', 'value': 'Sala del Maggior Consiglio, Sala dello Scrutinio'},
                        {'label': 'Ponte dei Sospiri', 'value': 'Collegamento con le Prigioni Nuove'},
                        {'label': 'Tintoretto', 'value': 'Paradiso (dipinto più grande al mondo)'},
                        {'label': 'Biglietto', 'value': '€30 (Musei di Piazza San Marco)'},
                        {'label': 'Itinerari segreti', 'value': '€28 (prenotazione obbligatoria)'}
                    ],
                    'coordinates': [45.4340, 12.3406],
                    'timetable': [
                        {'direction': 'Apr-Ott', 'times': '8:30-19:00'},
                        {'direction': 'Nov-Mar', 'times': '8:30-17:30'},
                        {'direction': 'Itinerari segreti', 'times': 'Gio-Mar (orari variabili)'}
                    ]
                }
            },
            'ponte_vecchio_firenze': {
                'place_name': 'Ponte Vecchio',
                'city': 'Firenze',
                'country': 'Italia',
                'data': {
                    'title': 'Ponte Vecchio, Firenze',
                    'summary': 'Il ponte medievale più famoso al mondo, unico ponte di Firenze risparmiato durante la Seconda Guerra Mondiale. Celebre per le sue botteghe orafe e il Corridoio Vasariano.',
                    'details': [
                        {'label': 'Costruzione', 'value': '1345 (ricostruzione dopo alluvione)'},
                        {'label': 'Architetto', 'value': 'Taddeo Gaddi (attr.)'},
                        {'label': 'Lunghezza', 'value': '95 metri'},
                        {'label': 'Botteghe', 'value': '43 negozi di orafi e gioiellieri'},
                        {'label': 'Corridoio Vasariano', 'value': 'Passaggio privato Medici (1565)'},
                        {'label': 'Seconda Guerra', 'value': 'Unico ponte risparmiato da Hitler'},
                        {'label': 'Accesso', 'value': 'Gratuito (sempre aperto)'}
                    ],
                    'coordinates': [43.7679, 11.2529],
                    'timetable': [
                        {'direction': 'Ponte', 'times': 'Sempre accessibile'},
                        {'direction': 'Negozi', 'times': 'Lun-Sab 9:00-20:00'},
                        {'direction': 'Corridoio Vasariano', 'times': 'Visite guidate su prenotazione'}
                    ]
                }
            }
        }
    
    def populate_cache(self):
        """Popola la cache con i dati precompilati"""
        with app.app_context():
            count = 0
            for cache_key, dest_info in self.destinations_data.items():
                try:
                    # Controlla se già presente
                    existing = PlaceCache.query.filter_by(cache_key=cache_key).first()
                    if existing:
                        print(f"✅ {dest_info['place_name']} già in cache")
                        continue
                    
                    # Crea nuovo record
                    cache_entry = PlaceCache(
                        cache_key=cache_key,
                        place_name=dest_info['place_name'],
                        city=dest_info['city'],
                        country=dest_info['country'],
                        place_data=json.dumps(dest_info['data']),
                        priority_level='italia_premium'
                    )
                    
                    db.session.add(cache_entry)
                    db.session.commit()
                    
                    print(f"💾 Salvato: {dest_info['place_name']}")
                    count += 1
                    
                except Exception as e:
                    print(f"❌ Errore {dest_info['place_name']}: {e}")
                    continue
            
            print(f"🎉 Pre-training completato! Aggiunti {count} luoghi iconici")
            return count
    
    def get_stats(self):
        """Statistiche cache"""
        with app.app_context():
            total = PlaceCache.query.count()
            by_level = db.session.query(
                PlaceCache.priority_level, 
                db.func.count(PlaceCache.id)
            ).group_by(PlaceCache.priority_level).all()
            
            return {
                'total': total,
                'by_level': dict(by_level)
            }

if __name__ == "__main__":
    pretrainer = OfflinePretraining()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        stats = pretrainer.get_stats()
        print("📊 Statistiche Cache:")
        print(f"  Totale: {stats['total']}")
        for level, count in stats['by_level'].items():
            print(f"  {level}: {count}")
    else:
        pretrainer.populate_cache()
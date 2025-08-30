
from flask import Blueprint, request, jsonify
import json

detail_bp = Blueprint('details', __name__)

def normalize_context_key(context):
    """Normalize context keys to match database entries"""
    # Remove common suffixes and prefixes
    normalized = context.lower()
    
    # Remove city suffixes like "_genova", ",_genova_genova"
    normalized = normalized.replace(',_genova_genova', '')
    normalized = normalized.replace('_genova_genova', '')
    normalized = normalized.replace('_genova', '')
    
    # Replace double underscores with single
    normalized = normalized.replace('__', '_')
    
    # Remove trailing underscores
    normalized = normalized.strip('_')
    
    return normalized

def generate_dynamic_details(context, city):
    """Generate dynamic details for any city using AI or local knowledge"""
    import os
    
    # Clean up the context to get the place name
    place_name = context.replace('_', ' ').replace(city, '').strip()
    
    # For Milano, create specific details
    if city == 'milano':
        milano_places = {
            'piazza duomo': {
                'title': 'Piazza del Duomo, Milano',
                'summary': 'Il cuore pulsante di Milano con la magnifica cattedrale gotica.',
                'details': [
                    {'label': 'Duomo', 'value': 'Cattedrale gotica iniziata nel 1386'},
                    {'label': 'Galleria', 'value': 'Galleria Vittorio Emanuele II accanto'},
                    {'label': 'Madonnina', 'value': 'Statua dorata sulla guglia più alta'},
                    {'label': 'Terrazze', 'value': 'Vista panoramica dalla terrazza del Duomo'},
                    {'label': 'Metro', 'value': 'Stazione Duomo (M1 rossa, M3 gialla)'}
                ],
                'tip': 'Sali sulle terrazze del Duomo per una vista spettacolare',
                'opening_hours': 'Duomo: 9:00-19:00, Terrazze: 9:00-19:00',
                'cost': 'Duomo €3, Terrazze €10-15'
            },
            'corso buenos aires': {
                'title': 'Corso Buenos Aires, Milano',
                'summary': 'Una delle vie dello shopping più lunghe d\'Europa con oltre 350 negozi.',
                'details': [
                    {'label': 'Lunghezza', 'value': '1,2 km di shopping'},
                    {'label': 'Negozi', 'value': 'Oltre 350 punti vendita'},
                    {'label': 'Metro', 'value': 'Lima (M1) e Loreto (M1/M2)'},
                    {'label': 'Shopping', 'value': 'Da catene internazionali a boutique locali'},
                    {'label': 'Orari', 'value': 'Maggior parte 10:00-20:00'}
                ],
                'tip': 'Evita il sabato pomeriggio se non ami la folla',
                'opening_hours': 'Negozi: 10:00-20:00 (Dom chiusi alcuni)',
                'cost': 'Gratuito (shopping a parte)'
            },
            'the hub': {
                'title': 'The Hub Hotel, Milano',
                'summary': 'Hotel moderno e centro congressi vicino alla Stazione Centrale.',
                'details': [
                    {'label': 'Posizione', 'value': 'Vicino Stazione Centrale'},
                    {'label': 'Servizi', 'value': 'Business center, ristorante, bar'},
                    {'label': 'Camere', 'value': 'Design contemporaneo'},
                    {'label': 'Trasporti', 'value': 'Metro M2/M3 Centrale FS'}
                ],
                'tip': 'Ottima posizione per chi viaggia in treno',
                'opening_hours': 'Reception 24h',
                'cost': 'Varia per camera'
            }
        }
        
        # Search for matching place
        for key, details in milano_places.items():
            if key in place_name.lower() or key in context.lower():
                return details
    
    # Generic fallback for any city
    return {
        'title': f'{place_name.title()}, {city.title()}',
        'summary': f'Luogo di interesse a {city.title()}',
        'details': [
            {'label': 'Città', 'value': city.title()},
            {'label': 'Tipo', 'value': 'Attrazione turistica'},
            {'label': 'Consiglio', 'value': 'Chiedi informazioni ai locals'}
        ],
        'tip': f'Esplora {place_name.title()} e scopri le sue caratteristiche uniche',
        'opening_hours': 'Verifica orari locali',
        'cost': 'Da verificare'
    }

@detail_bp.route('/get_details', methods=['POST'])
def get_details():
    """Enhanced details handler with dynamic city support"""
    try:
        data = request.get_json()
        context = data.get('context', '')
        
        # Try to extract city information from context
        city_detected = 'genova'  # Default fallback
        context_lower = context.lower()
        
        # Detect city from context
        if 'milano' in context_lower or 'milan' in context_lower:
            city_detected = 'milano'
        elif 'roma' in context_lower or 'rome' in context_lower:
            city_detected = 'roma'
        elif 'venezia' in context_lower or 'venice' in context_lower:
            city_detected = 'venezia'
        elif 'firenze' in context_lower or 'florence' in context_lower:
            city_detected = 'firenze'
        elif 'new_york' in context_lower or 'nyc' in context_lower:
            city_detected = 'new_york'
        elif 'paris' in context_lower:
            city_detected = 'paris'
        elif 'london' in context_lower:
            city_detected = 'london'
        
        # Try dynamic generation first for non-Genova cities
        if city_detected != 'genova':
            # Generate dynamic details for other cities
            dynamic_details = generate_dynamic_details(context, city_detected)
            if dynamic_details:
                return jsonify(dynamic_details)
        
        # Database of comprehensive details for Genova attractions
        details_database = {
            # Handle various context formats from frontend
            'piazza_de_ferrari,_genova_genova': {
                'title': 'Piazza De Ferrari, Genova',
                'summary': 'Il salotto di Genova, circondata da palazzi storici e dominata dalla grande fontana centrale.',
                'details': [
                    {'label': 'Fontana', 'value': 'Costruita nel 1936, ristrutturata nel 2001'},
                    {'label': 'Palazzi storici', 'value': 'Palazzo Ducale, Palazzo della Regione'},
                    {'label': 'Teatro', 'value': 'Teatro Carlo Felice (opera house)'},
                    {'label': 'Shopping', 'value': 'Gallerie Mazzini, Via XX Settembre'},
                    {'label': 'Metro', 'value': 'Stazione De Ferrari (linea rossa)'}
                ],
                'tip': 'Centro perfetto per iniziare la visita di Genova',
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            },
            # Fix context keys to match frontend
            'piazza_de_ferrari': {
                'title': 'Piazza De Ferrari, Genova',
                'summary': 'Il salotto di Genova, circondata da palazzi storici e dominata dalla grande fontana centrale.',
                'details': [
                    {'label': 'Fontana', 'value': 'Costruita nel 1936, ristrutturata nel 2001'},
                    {'label': 'Palazzi storici', 'value': 'Palazzo Ducale, Palazzo della Regione'},
                    {'label': 'Teatro', 'value': 'Teatro Carlo Felice (opera house)'},
                    {'label': 'Shopping', 'value': 'Gallerie Mazzini, Via XX Settembre'},
                    {'label': 'Metro', 'value': 'Stazione De Ferrari (linea rossa)'}
                ],
                'tip': 'Centro perfetto per iniziare la visita di Genova',
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            },
            'via__campo': {
                'title': 'Via del Campo, Genova',
                'summary': 'La strada più famosa di Genova, resa celebre dalla canzone di Fabrizio De André.',
                'details': [
                    {'label': 'Lunghezza', 'value': '500 metri di storia medievale'},
                    {'label': 'Epoca', 'value': 'XII secolo (caruggi medievali)'},
                    {'label': 'Fabrizio De André', 'value': 'Canzone "Via del Campo" (1967)'},
                    {'label': 'Caratteristiche', 'value': 'Negozi storici, farinata, botteghe artigiane'},
                    {'label': 'Mercato', 'value': 'Mercato del Pesce e prodotti locali'}
                ],
                'tip': 'Prova la farinata da "Il Soccorso" - autentica specialità genovese',
                'opening_hours': 'Sempre accessibile (negozi: 10:00-19:00)',
                'cost': 'Gratuito'
            },
            'cattedrale__san_lorenzo': {
                'title': 'Cattedrale di San Lorenzo, Genova',
                'summary': 'Il Duomo di Genova, famoso per la bomba navale britannica inesplosa del 1941.',
                'details': [
                    {'label': 'Costruzione', 'value': 'IX-XIV secolo (romanico-gotico)'},
                    {'label': 'Facciata', 'value': 'Marmo bianco e nero a strisce orizzontali'},
                    {'label': 'Bomba 1941', 'value': 'Proiettile navale britannico inesploso (visibile)'},
                    {'label': 'Tesoro', 'value': 'Santo Graal leggendario, reliquie preziose'},
                    {'label': 'Portale', 'value': 'Leoni stilofori medievali'}
                ],
                'tip': 'Non perdere il Museo del Tesoro con il Santo Graal',
                'opening_hours': 'Lun-Sab 9:00-18:00, Dom 15:00-18:00',
                'cost': 'Ingresso gratuito, Tesoro €6'
            },
            'acquario__genova': {
                'title': 'Acquario di Genova',
                'summary': 'Secondo acquario più grande d\'Europa con 12.000 esemplari marini.',
                'details': [
                    {'label': 'Dimensioni', 'value': '9.700 m² di superficie espositiva'},
                    {'label': 'Apertura', 'value': '1992 (Expo Colombo 500 anni)'},
                    {'label': 'Architetto', 'value': 'Renzo Piano (Porto Antico)'},
                    {'label': 'Biglietto', 'value': '€29 adulti, €19 bambini'},
                    {'label': 'Attrazioni', 'value': 'Delfini, squali, lamantini, pinguini'},
                    {'label': 'Record', 'value': '2° in Europa per grandezza'}
                ],
                'tip': 'Arriva alle 9:00 per evitare code. Il biglietto include la Biosfera.',
                'opening_hours': 'Lun-Ven 9:00-20:00, Sab-Dom 8:30-20:00',
                'cost': '€29 adulti, €19 bambini'
            },
            'porto_antico': {
                'title': 'Porto Antico, Genova',
                'summary': 'Area portuale storica rinnovata da Renzo Piano per Expo 1992.',
                'details': [
                    {'label': 'Progetto Renzo Piano', 'value': '1992 (500° scoperta America)'},
                    {'label': 'Biosfera', 'value': 'Serra tropicale in vetro e acciaio'},
                    {'label': 'Bigo', 'value': 'Ascensore panoramico 40m altezza'},
                    {'label': 'Galata Museo del Mare', 'value': 'Più grande del Mediterraneo'},
                    {'label': 'Eventi', 'value': 'Concerti, festival, mercatini'},
                    {'label': 'Ristoranti', 'value': 'Cucina ligure e vista mare'}
                ],
                'tip': 'Area perfetta per aperitivo serale. Eventi gratuiti nei weekend.',
                'opening_hours': 'Sempre accessibile (attrazioni 10:00-19:00)',
                'cost': 'Passeggiata gratuita, attrazioni a pagamento'
            },
            'acquario_genova': {
                'title': 'Acquario di Genova',
                'summary': 'Secondo acquario più grande d\'Europa con 12.000 esemplari marini in 70 vasche tematiche.',
                'details': [
                    {'label': 'Orari', 'value': 'Lun-Ven 9:00-20:00, Sab-Dom 8:30-20:00 (estate)'},
                    {'label': 'Prezzo', 'value': '€29 adulti, €19 bambini 4-12 anni'},
                    {'label': 'Durata consigliata', 'value': '2-3 ore'},
                    {'label': 'Accessibilità', 'value': 'Completamente accessibile'},
                    {'label': 'Highlights', 'value': 'Delfini, squali, tunnel sottomarino, Biosfera'}
                ],
                'highlights': ['70 vasche tematiche', 'Tunnel sottomarino', 'Biosfera Renzo Piano'],
                'insider_tip': 'Arriva alle 9:00 per evitare code. Il biglietto include la Biosfera.',
                'imageUrl': '/static/images/acquario_genova.jpg',
                'opening_hours': 'Lun-Ven 9:00-20:00, Sab-Dom 8:30-20:00',
                'cost': '€29 adulti, €19 bambini'
            },
            'gelateria_il_doge': {
                'title': 'Gelateria Il Doge',
                'summary': 'Gelateria artigianale con vista sul porto e gusti tipici liguri.',
                'details': [
                    {'label': 'Orari', 'value': '10:00-22:00'},
                    {'label': 'Prezzo medio', 'value': '€3-5'},
                    {'label': 'Specialità', 'value': 'Gelato al pesto, focaccia'},
                    {'label': 'Vista', 'value': 'Porto Antico'}
                ],
                'tip': 'Prova il gelato al pesto - suona strano ma è delizioso!',
                'opening_hours': '10:00-22:00',
                'cost': '€3-5'
            },
            'via_campo': {
                'title': 'Via del Campo, Genova',
                'summary': 'La strada più famosa di Genova, resa celebre dalla canzone di Fabrizio De André.',
                'details': [
                    {'label': 'Lunghezza', 'value': '500 metri di storia medievale'},
                    {'label': 'Epoca', 'value': 'XII secolo (caruggi medievali)'},
                    {'label': 'Fabrizio De André', 'value': 'Canzone "Via del Campo" (1967)'},
                    {'label': 'Caratteristiche', 'value': 'Negozi storici, farinata, botteghe artigiane'},
                    {'label': 'Mercato', 'value': 'Mercato del Pesce e prodotti locali'}
                ],
                'tip': 'Prova la farinata da "Il Soccorso" - autentica specialità genovese',
                'opening_hours': 'Sempre accessibile (negozi: 10:00-19:00)',
                'cost': 'Gratuito'
            },
            'cattedrale_san_lorenzo': {
                'title': 'Cattedrale di San Lorenzo, Genova', 
                'summary': 'Il Duomo di Genova, famoso per la bomba navale britannica inesplosa del 1941.',
                'details': [
                    {'label': 'Costruzione', 'value': 'IX-XIV secolo (romanico-gotico)'},
                    {'label': 'Facciata', 'value': 'Marmo bianco e nero a strisce orizzontali'},
                    {'label': 'Bomba 1941', 'value': 'Proiettile navale britannico inesploso (visibile)'},
                    {'label': 'Tesoro', 'value': 'Santo Graal leggendario, reliquie preziose'},
                    {'label': 'Portale', 'value': 'Leoni stilofori medievali'}
                ],
                'tip': 'Non perdere il Museo del Tesoro con il Santo Graal',
                'opening_hours': 'Lun-Sab 9:00-18:00, Dom 15:00-18:00',
                'cost': 'Ingresso gratuito, Tesoro €6'
            },
            'acquario_genova': {
                'title': 'Acquario di Genova',
                'summary': 'Secondo acquario più grande d\'Europa con 12.000 esemplari marini in 70 vasche tematiche.',
                'details': [
                    {'label': 'Orari', 'value': 'Lun-Ven 9:00-20:00, Sab-Dom 8:30-20:00 (estate)'},
                    {'label': 'Prezzo', 'value': '€29 adulti, €19 bambini 4-12 anni'},
                    {'label': 'Durata consigliata', 'value': '2-3 ore'},
                    {'label': 'Accessibilità', 'value': 'Completamente accessibile'}
                ],
                'highlights': ['70 vasche tematiche', 'Tunnel sottomarino', 'Biosfera Renzo Piano'],
                'insider_tip': 'Arriva alle 9:00 per evitare code. Il biglietto include la Biosfera.',
                'imageUrl': '/static/images/acquario_genova.jpg'
            },
            'cattedrale_san_lorenzo': {
                'title': 'Cattedrale di San Lorenzo',
                'summary': 'Duomo di Genova con facciata a strisce bianche e nere, contiene la bomba inesplosa del 1941.',
                'details': [
                    {'label': 'Orari', 'value': 'Lun-Sab 8:00-12:00, 15:00-19:00'},
                    {'label': 'Prezzo', 'value': 'Cattedrale gratuita | Museo €6'},
                    {'label': 'Stile', 'value': 'Romanico-gotico ligure'},
                    {'label': 'Costruzione', 'value': 'XII-XIV secolo'}
                ],
                'highlights': ['Bomba britannica inesplosa', 'Santo Graal leggendario', 'Cripta romanica'],
                'insider_tip': 'Non perdere il Museo del Tesoro con il Santo Graal. Ingresso separato a destra.',
                'imageUrl': '/static/images/cattedrale_san_lorenzo.jpg'
            },
            'via_del_campo': {
                'title': 'Via del Campo',
                'summary': 'Via storica immortalata da Fabrizio De André, cuore autentico dei caruggi medievali.',
                'details': [
                    {'label': 'Tipologia', 'value': 'Caruggio medievale'},
                    {'label': 'Specialità', 'value': 'Farinata genovese'},
                    {'label': 'Accessibilità', 'value': 'Sempre accessibile'},
                    {'label': 'Periodo storico', 'value': 'XIII-XV secolo'}
                ],
                'highlights': ['Caruggi medievali', 'Farinata da Il Soccorso', 'Mercato tradizionale'],
                'insider_tip': 'Mattina per il mercato del pesce, sera per la vita notturna autentica.',
                'imageUrl': '/static/images/via_del_campo.jpg'
            },
            'porto_antico': {
                'title': 'Porto Antico',
                'summary': 'Area portuale storica rinnovata da Renzo Piano per Expo \'92, oggi hub culturale.',
                'details': [
                    {'label': 'Architetto', 'value': 'Renzo Piano (1992)'},
                    {'label': 'Attrazioni', 'value': 'Bigo, Galata, Biosfera'},
                    {'label': 'Orari', 'value': 'Sempre accessibile'},
                    {'label': 'Parcheggio', 'value': 'A pagamento nelle vicinanze'}
                ],
                'highlights': ['Bigo ascensore panoramico', 'Galata Museo del Mare', 'Biosfera'],
                'insider_tip': 'Area perfetta per aperitivo serale. Eventi gratuiti nei weekend.',
                'imageUrl': '/static/images/porto_antico.jpg'
            },
            'gelateria_il_doge': {
                'title': 'Gelateria Il Doge',
                'summary': 'Gelateria artigianale con vista sul porto e gusti tipici liguri.',
                'details': [
                    {'label': 'Orari', 'value': '10:00-22:00'},
                    {'label': 'Prezzo medio', 'value': '€3-5'},
                    {'label': 'Specialità', 'value': 'Gelato al pesto, focaccia'},
                    {'label': 'Vista', 'value': 'Porto Antico'}
                ],
                'highlights': ['Gelato artigianale', 'Gusti tipici liguri', 'Vista porto'],
                'insider_tip': 'Prova il gelato al pesto - suona strano ma è delizioso!',
                'imageUrl': '/static/images/gelato_porto.jpg'
            },
            'antica_osteria_borgo': {
                'title': 'Antica Osteria del Borgo',
                'summary': 'Trattoria autentica specializzata in cucina ligure tradizionale.',
                'details': [
                    {'label': 'Orari', 'value': '12:00-15:00, 19:00-23:00'},
                    {'label': 'Prezzo', 'value': '€25-35 a persona'},
                    {'label': 'Specialità', 'value': 'Pesto al mortaio, focaccia DOP'},
                    {'label': 'Prenotazione', 'value': 'Consigliata per cena'}
                ],
                'highlights': ['Pesto fatto al mortaio', 'Focaccia col formaggio DOP', 'Farinata calda'],
                'insider_tip': 'Ordina il menu degustazione ligure completo.',
                'imageUrl': '/static/images/osteria_borgo.jpg'
            }
        }
        
        # Normalize context key by removing suffixes and variations
        normalized_context = normalize_context_key(context)
        
        # Try to find details for the context (try multiple variations)
        detail_data = None
        
        print(f"🔍 Searching for context: '{context}'")
        print(f"🔍 Normalized context: '{normalized_context}'")
        print(f"🔍 Available keys: {list(details_database.keys())[:10]}...")  # Show first 10 keys
        
        # Try exact match first
        if context in details_database:
            detail_data = details_database[context]
            print(f"✅ Exact match found for: {context}")
        # Try normalized context
        elif normalized_context in details_database:
            detail_data = details_database[normalized_context]
            print(f"✅ Normalized match found for: {normalized_context}")
        # Try partial matching for context variations
        else:
            # Try removing underscores and special characters
            simple_context = context.replace('_', ' ').replace(',', '').lower().strip()
            for key in details_database.keys():
                simple_key = key.replace('_', ' ').replace(',', '').lower().strip()
                if simple_key in simple_context or simple_context in simple_key:
                    detail_data = details_database[key]
                    print(f"✅ Partial match found: '{key}' matches '{context}'")
                    break
            
            # If still not found, try substring matching
            if not detail_data:
                for key in details_database.keys():
                    if any(word in key for word in normalized_context.split('_')):
                        detail_data = details_database[key]
                        print(f"✅ Substring match found: '{key}' for '{context}'")
                        break
        
        if detail_data:
            print(f"✅ Found details for {context}")
            # Return details directly, not nested under 'details' key
            return jsonify(detail_data)
        else:
            print(f"❌ No details found for context: {context}")
            # Fallback for unknown contexts  
            return jsonify({
                'title': 'Informazioni non disponibili',
                'summary': 'Dettagli non trovati per questa attrazione.',
                'details': [],
                'tip': 'I dettagli specifici verranno aggiunti presto.'
            }), 404
            
    except Exception as e:
        print(f"❌ Error getting details: {e}")
        return jsonify({'error': 'Details not available'}), 500

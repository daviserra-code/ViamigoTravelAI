
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

@detail_bp.route('/get_details', methods=['POST'])
def get_details():
    """Enhanced details handler that accesses rich details from context"""
    try:
        data = request.get_json()
        context = data.get('context', '')
        
        # Database of comprehensive details for Genova attractions
        details_database = {
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
        
        # Try exact match first
        if context in details_database:
            detail_data = details_database[context]
        # Try normalized context
        elif normalized_context in details_database:
            detail_data = details_database[normalized_context]
        # Try partial matching for context variations
        else:
            for key in details_database.keys():
                if key in context or context.startswith(key):
                    detail_data = details_database[key]
                    break
        
        if detail_data:
            print(f"✅ Found details for {context}")
            return jsonify({
                'success': True,
                'details': detail_data
            })
        else:
            print(f"❌ No details found for context: {context}")
            # Fallback for unknown contexts  
            return jsonify({
                'success': False,
                'error': 'Details not found',
                'title': 'Informazioni non disponibili',
                'summary': 'Dettagli non trovati per questa attrazione.',
                'details': []
            }), 404
            
    except Exception as e:
        print(f"❌ Error getting details: {e}")
        return jsonify({'error': 'Details not available'}), 500


from flask import Blueprint, request, jsonify
import json

detail_bp = Blueprint('details', __name__)

@detail_bp.route('/get_details', methods=['POST'])
def get_details():
    """Enhanced details handler that accesses rich details from context"""
    try:
        data = request.get_json()
        context = data.get('context', '')
        
        # Database of comprehensive details for Genova attractions
        details_database = {
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
        
        # Try to find details for the context
        detail_data = details_database.get(context)
        
        if detail_data:
            return jsonify(detail_data)
        else:
            # Fallback for unknown contexts
            return jsonify({
                'title': 'Informazioni non disponibili',
                'summary': 'Dettagli non trovati per questa attrazione.',
                'details': []
            }), 404
            
    except Exception as e:
        print(f"❌ Error getting details: {e}")
        return jsonify({'error': 'Details not available'}), 500

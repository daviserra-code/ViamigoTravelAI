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

    # Roma attractions
    if city == 'roma' or city == 'rome':
        roma_places = {
            'colosseo': {
                'title': 'Colosseo, Roma',
                'summary': 'Il più grande anfiteatro del mondo romano, simbolo eterno di Roma.',
                'details': [
                    {'label': 'Costruzione', 'value': '72-80 d.C. sotto Vespasiano'},
                    {'label': 'Capacità', 'value': '50.000-80.000 spettatori'},
                    {'label': 'Arena', 'value': 'Gladiatori e spettacoli'},
                    {'label': 'Sotterranei', 'value': 'Labirinto ipogeo visitabile'},
                    {'label': 'Metro', 'value': 'Colosseo (Linea B)'}
                ],
                'tip': 'Prenota online per evitare code. Biglietto combinato con Foro Romano',
                'opening_hours': '8:30-19:00 (estate), 8:30-16:30 (inverno)',
                'cost': '€16 adulti, €2 ridotto'
            },
            'fontana di trevi': {
                'title': 'Fontana di Trevi, Roma',
                'summary': 'La fontana barocca più famosa al mondo.',
                'details': [
                    {'label': 'Architetto', 'value': 'Nicola Salvi (1762)'},
                    {'label': 'Tradizione', 'value': 'Lancia una moneta per tornare'},
                    {'label': 'Raccolta', 'value': '€3000/giorno alla Caritas'},
                    {'label': 'Film', 'value': 'La Dolce Vita di Fellini'}
                ],
                'tip': 'Visita presto la mattina o tardi la sera per meno folla',
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            }
        }
        for key, details in roma_places.items():
            if key in place_name.lower() or key in context.lower():
                return details

    # Venezia attractions
    elif city == 'venezia' or city == 'venice':
        venezia_places = {
            'san marco': {
                'title': 'Piazza San Marco, Venezia',
                'summary': 'Il salotto più elegante d\'Europa con la basilica bizantina.',
                'details': [
                    {'label': 'Basilica', 'value': 'Mosaici dorati bizantini'},
                    {'label': 'Campanile', 'value': '98.6m, vista panoramica'},
                    {'label': 'Caffè Florian', 'value': 'Dal 1720, storico caffè'},
                    {'label': 'Acqua alta', 'value': 'Passerelle in caso di marea'}
                ],
                'tip': 'Sali sul campanile per vista mozzafiato sulla laguna',
                'opening_hours': 'Basilica 9:30-17:00, Piazza sempre aperta',
                'cost': 'Basilica €3, Campanile €10'
            },
            'rialto': {
                'title': 'Ponte di Rialto, Venezia',
                'summary': 'Il ponte più antico e famoso sul Canal Grande.',
                'details': [
                    {'label': 'Costruzione', 'value': '1588-1591'},
                    {'label': 'Architetto', 'value': 'Antonio da Ponte'},
                    {'label': 'Mercato', 'value': 'Mercato del pesce vicino'},
                    {'label': 'Negozi', 'value': 'Gioiellerie sul ponte'}
                ],
                'tip': 'Vista migliore dal fondamenta del Vin',
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            }
        }
        for key, details in venezia_places.items():
            if key in place_name.lower() or key in context.lower():
                return details

    # Napoli attractions
    elif city == 'napoli' or city == 'naples':
        napoli_places = {
            'spaccanapoli': {
                'title': 'Spaccanapoli, Napoli',
                'summary': 'L\'antico decumano che taglia il centro storico.',
                'details': [
                    {'label': 'Lunghezza', 'value': '2 km di storia'},
                    {'label': 'Chiese', 'value': 'Santa Chiara, Gesù Nuovo'},
                    {'label': 'Pizza', 'value': 'Pizzerie storiche'},
                    {'label': 'Artigianato', 'value': 'Presepi di San Gregorio Armeno'}
                ],
                'tip': 'Prova la pizza da Sorbillo o Di Matteo',
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            }
        }
        for key, details in napoli_places.items():
            if key in place_name.lower() or key in context.lower():
                return details

    # London attractions
    elif city == 'london':
        london_places = {
            'big_ben': {
                'title': 'Big Ben, London',
                'summary': 'Iconic clock tower at Westminster Palace, officially called Elizabeth Tower. Symbol of British democracy and one of London\'s most recognizable landmarks.',
                'details': [
                    {'label': 'Official name',
                        'value': 'Elizabeth Tower (renamed 2012)'},
                    {'label': 'Height', 'value': '96 meters (316 feet)'},
                    {'label': 'Built', 'value': '1843-1859 (Augustus Pugin)'},
                    {'label': 'Bell weight', 'value': '13.76 tonnes'},
                    {'label': 'Clock faces', 'value': '4 faces, 7 meters diameter each'},
                    {'label': 'Tube station',
                        'value': 'Westminster (Circle, District, Jubilee)'},
                    {'label': 'Best views',
                        'value': 'Westminster Bridge, Parliament Square'}
                ],
                'tip': '🏛️ **Insider tip**: Best photos from Westminster Bridge at sunset. Tours only available to UK residents with advance booking.',
                'opening_hours': 'External viewing 24/7, tours by appointment only',
                'cost': 'External viewing free, guided tours £15-25'
            },
            'tower_bridge': {
                'title': 'Tower Bridge, London',
                'summary': 'Victorian Gothic bridge with glass walkways.',
                'details': [
                    {'label': 'Built', 'value': '1886-1894'},
                    {'label': 'Walkways', 'value': 'Glass floor 42m high'},
                    {'label': 'Engine rooms', 'value': 'Victorian machinery'},
                    {'label': 'Tube', 'value': 'Tower Hill station'}
                ],
                'tip': 'Visit engine rooms for history',
                'opening_hours': '9:30-18:00',
                'cost': '£11.40 adults'
            },
            'piccadilly_circus': {
                'title': 'Piccadilly Circus, London',
                'summary': 'Bustling junction in West End, famous for neon advertising displays and Eros statue. Gateway to London\'s theatre district.',
                'details': [
                    {'label': 'Nickname', 'value': '"Times Square of London"'},
                    {'label': 'Eros statue',
                        'value': 'Shaftesbury Memorial Fountain (1893)'},
                    {'label': 'Advertising',
                        'value': 'Historic curved LED displays since 1908'},
                    {'label': 'Theatres', 'value': 'Gateway to West End theatre district'},
                    {'label': 'Shopping', 'value': 'Regent Street, Oxford Street nearby'},
                    {'label': 'Tube station',
                        'value': 'Piccadilly Circus (Piccadilly, Bakerloo)'}
                ],
                'tip': '🎭 **Best experience**: Evening for illuminated signs, perfect starting point for West End shows.',
                'opening_hours': 'Public space - accessible 24/7',
                'cost': 'Free to visit and photograph'
            },
            'piccadilly_circuslondon': {
                'title': 'Piccadilly Circus, London',
                'summary': 'Iconic junction in London\'s West End, famous for its bright advertising displays and the Eros statue.',
                'details': [
                    {'label': 'Location', 'value': 'Westminster, Central London'},
                    {'label': 'Famous for', 'value': 'Curved LED advertising displays'},
                    {'label': 'Statue',
                        'value': 'Shaftesbury Memorial (Eros) - 1893'},
                    {'label': 'Transport', 'value': 'Piccadilly Circus tube station'},
                    {'label': 'Nearby', 'value': 'Oxford Street, Regent Street shopping'},
                    {'label': 'Best time', 'value': 'Evening when lights are brightest'}
                ],
                'tip': '🌟 Best photos at dusk when the neon signs light up against the twilight sky',
                'opening_hours': 'Always accessible - public space',
                'cost': 'Free'
            },
            'tower_of_london': {
                'title': 'Tower of London',
                'summary': 'Historic fortress and UNESCO World Heritage Site, home to the Crown Jewels and 1000 years of royal history.',
                'details': [
                    {'label': 'Built', 'value': '1066 by William the Conqueror'},
                    {'label': 'Famous for',
                        'value': 'Crown Jewels, Yeoman Warders (Beefeaters)'},
                    {'label': 'Ravens',
                        'value': '6 ravens live here (legend says if they leave, kingdom falls)'},
                    {'label': 'Executions',
                        'value': 'Anne Boleyn, Catherine Howard executed here'},
                    {'label': 'Tube',
                        'value': 'Tower Hill station (Circle/District lines)'},
                    {'label': 'Duration', 'value': '3-4 hours recommended'}
                ],
                'tip': '👑 Book online to skip queues. See Crown Jewels first before crowds arrive.',
                'opening_hours': 'Tue-Sat 9:00-17:30, Sun-Mon 10:00-17:30',
                'cost': '£33.60 adults, £16.80 children'
            },
            'london_eye': {
                'title': 'London Eye',
                'summary': 'Giant observation wheel on South Bank offering spectacular 360° views across London.',
                'details': [
                    {'label': 'Height', 'value': '135 meters (443 feet)'},
                    {'label': 'Opened',
                        'value': '2000 - originally temporary for millennium'},
                    {'label': 'Capsules', 'value': '32 capsules, each holds 25 people'},
                    {'label': 'Duration', 'value': '30-minute slow rotation'},
                    {'label': 'Views', 'value': 'Big Ben, St Paul\'s, Shard on clear days'},
                    {'label': 'Transport',
                        'value': 'Waterloo station (5-minute walk)'}
                ],
                'tip': '🌅 Book sunset slots for magical views. Fast Track tickets available to skip queues.',
                'opening_hours': 'Daily 11:00-18:00 (varies by season)',
                'cost': '£32+ adults (prices vary by time/season)'
            },
            'westminster': {
                'title': 'Westminster, London',
                'summary': 'Political heart of London with Houses of Parliament, Big Ben, and Westminster Abbey.',
                'details': [
                    {'label': 'Parliament',
                        'value': 'Houses of Parliament with Big Ben tower'},
                    {'label': 'Westminster Abbey',
                        'value': 'Coronation church for 1000 years'},
                    {'label': 'Downing Street',
                        'value': 'PM\'s residence (No. 10) - 5 min walk'},
                    {'label': 'Transport',
                        'value': 'Westminster tube (Circle/District/Jubilee)'},
                    {'label': 'River Thames',
                        'value': 'Westminster Bridge for classic photos'},
                    {'label': 'History', 'value': 'UNESCO World Heritage Site'}
                ],
                'tip': '📸 Westminster Bridge offers the classic Big Ben photo angle',
                'opening_hours': 'Public areas always accessible',
                'cost': 'Free to walk around'
            },
            'piccadilly_circuslondon_london': {
                'title': 'Piccadilly Circus, London',
                'summary': 'Bustling junction in West End, famous for neon advertising displays and Eros statue.',
                'details': [
                    {'label': 'Nickname', 'value': '"Times Square of London"'},
                    {'label': 'Eros statue',
                        'value': 'Shaftesbury Memorial Fountain (1893)'},
                    {'label': 'Advertising',
                        'value': 'Historic curved LED displays since 1908'},
                    {'label': 'Tube station',
                        'value': 'Piccadilly Circus (Piccadilly, Bakerloo)'}
                ],
                'tip': '🎭 Evening for illuminated signs, perfect for West End shows.',
                'opening_hours': 'Public space - accessible 24/7',
                'cost': 'Free'
            },
        }
        for key, details in london_places.items():
            if key in place_name.lower() or key in context.lower():
                return details

    # For Milano, create specific details
    elif city == 'milano':
        milano_places = {
            'piazza duomo': {
                'title': 'Piazza del Duomo, Milano',
                'summary': 'Il cuore pulsante di Milano con la magnifica cattedrale gotica.',
                'details': [
                    {'label': 'Duomo', 'value': 'Cattedrale gotica iniziata nel 1386'},
                    {'label': 'Galleria',
                        'value': 'Galleria Vittorio Emanuele II accanto'},
                    {'label': 'Madonnina',
                        'value': 'Statua dorata sulla guglia più alta'},
                    {'label': 'Terrazze',
                        'value': 'Vista panoramica dalla terrazza del Duomo'},
                    {'label': 'Metro',
                        'value': 'Stazione Duomo (M1 rossa, M3 gialla)'}
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
                    {'label': 'Shopping',
                        'value': 'Da catene internazionali a boutique locali'},
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

        # Add more Milano places dynamically
        milano_generic = {
            'navigli': {
                'title': 'Navigli, Milano',
                'summary': 'Quartiere dei canali storici con ristoranti e vita notturna.',
                'details': [
                    {'label': 'Canali', 'value': 'Naviglio Grande e Naviglio Pavese'},
                    {'label': 'Storia', 'value': 'Sistema di canali del XII secolo'},
                    {'label': 'Aperitivo', 'value': 'Famoso per aperitivo milanese'},
                    {'label': 'Mercatino',
                        'value': 'Antiquariato ultima domenica del mese'}
                ],
                'tip': 'Perfetto per aperitivo serale lungo i canali',
                'opening_hours': 'Sempre accessibile, locali 18:00-02:00',
                'cost': 'Gratuito (consumazioni extra)'
            },
            'castello sforzesco': {
                'title': 'Castello Sforzesco, Milano',
                'summary': 'Fortezza del XV secolo con musei e parco Sempione.',
                'details': [
                    {'label': 'Costruzione', 'value': '1450 Francesco Sforza'},
                    {'label': 'Musei',
                        'value': 'Arte antica, Pietà Rondanini di Michelangelo'},
                    {'label': 'Parco', 'value': 'Parco Sempione adiacente'},
                    {'label': 'Torre', 'value': 'Torre del Filarete'}
                ],
                'tip': 'Ingresso cortili gratuito, musei a pagamento',
                'opening_hours': 'Castello 7:00-19:30, Musei 9:00-17:30',
                'cost': 'Cortili gratis, Musei €5'
            }
        }

        # Try generic Milano places
        for key, details in milano_generic.items():
            if key in place_name.lower() or key in context.lower():
                return details

    # Generic fallback for Milano attractions
    if city == 'milano':
        return {
            'title': f'{place_name.title()}, Milano',
            'summary': f'Attrazione di Milano da esplorare',
            'details': [
                {'label': 'Città', 'value': 'Milano'},
                {'label': 'Zona', 'value': 'Centro storico'},
                {'label': 'Trasporti', 'value': 'Metro linee M1/M2/M3'},
                {'label': 'Consiglio', 'value': 'Parte del tour di Milano'}
            ],
            'tip': 'Scopri questa attrazione nel cuore di Milano',
            'opening_hours': 'Consultare orari ufficiali',
            'cost': 'Verificare tariffe aggiornate'
        }

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

        # Detect city from context - enhanced detection with NO default fallback to prevent hallucinations
        context_lower = context.lower()
        city_detected = None  # NO default to prevent wrong city data!

        # Enhanced Milano detection patterns - prioritize before other cities
        if any(term in context_lower for term in ['milano', 'milan', 'duomo', 'buenos aires',
                                                  'galleria vittorio', 'navigli', 'brera',
                                                  'castello sforzesco', 'scala']):
            city_detected = 'milano'
        # Torino detection - PRIORITIZE before Roma to avoid "via roma" confusion
        elif any(term in context_lower for term in ['torino', 'turin', 'mole antonelliana', 
                                                     'museo egizio', 'palazzo reale torino',
                                                     '_torino', ',torino']):
            city_detected = 'torino'
        # Roma detection - check for city context, not just substring "roma"
        # Avoid matching "via roma" (common street name in many cities)
        elif (('roma,' in context_lower or ',roma' in context_lower or 
               'rome' in context_lower or 'colosseum' in context_lower or
               'colosseo' in context_lower or 'vaticano' in context_lower or
               'fontana di trevi' in context_lower) and 
              'torino' not in context_lower and 'milano' not in context_lower):
            city_detected = 'roma'
        # London detection with various patterns
        elif ('london' in context_lower or 'piccadilly' in context_lower or
              'westminster' in context_lower or 'soho' in context_lower or
                'big_ben' in context_lower or 'tower_bridge' in context_lower):
            city_detected = 'london'
        elif 'venezia' in context_lower or 'venice' in context_lower or 'rialto' in context_lower:
            city_detected = 'venezia'
        elif 'napoli' in context_lower or 'naples' in context_lower or 'vesuvio' in context_lower:
            city_detected = 'napoli'
        elif 'firenze' in context_lower or 'florence' in context_lower or 'uffizi' in context_lower:
            city_detected = 'firenze'
        elif 'new_york' in context_lower or 'nyc' in context_lower or 'manhattan' in context_lower:
            city_detected = 'new_york'
        elif 'paris' in context_lower or 'eiffel' in context_lower:
            city_detected = 'paris'
        # Genova detection - ONLY if explicitly mentioned
        elif any(term in context_lower for term in ['genova', 'genoa', 'piazza de ferrari genova',
                                                    'acquario di genova', 'palazzo ducale genova',
                                                    'porto antico genova', 'lanterna genova']):
            city_detected = 'genova'

        # If no city detected, return error instead of wrong data
        if not city_detected:
            print(f"❌ NO CITY DETECTED in context: {context}")
            return jsonify({
                'error': 'City not detected',
                'title': 'Informazioni non disponibili',
                'summary': 'Non è stato possibile identificare la città per questa attrazione.',
                'details': [],
                'tip': 'Prova a specificare la città nella ricerca',
                'opening_hours': 'N/A',
                'cost': 'N/A'
            }), 400

        print(
            f"✅ City detected: {city_detected} from context: {context[:100]}")

        # 🔍 STEP 1: Check PostgreSQL PlaceCache first for verified data
        from models import PlaceCache
        from flask_app import db

        place_name_clean = context.replace('_', ' ').replace(',', '').strip()

        # Try to find in database by matching place name and city
        db_place = PlaceCache.query.filter(
            db.func.lower(PlaceCache.place_name).like(
                f'%{place_name_clean.lower()}%'),
            db.func.lower(PlaceCache.city) == city_detected.lower()
        ).first()

        if db_place:
            print(
                f"✅ Found verified data in PostgreSQL for: {db_place.place_name}")
            place_data = db_place.place_data

            # Format for frontend if it's in the correct structure
            if isinstance(place_data, dict) and 'name' in place_data:
                return jsonify({
                    'title': f"{place_data.get('name', 'Attrazione')}, {city_detected.title()}",
                    'summary': f"Informazioni verificate per {place_data.get('name')}",
                    'details': [
                        {'label': 'Tipo', 'value': place_data.get(
                            'type', 'N/A').title()},
                        {'label': 'Coordinate',
                            'value': f"{place_data.get('lat', 'N/A')}, {place_data.get('lon', 'N/A')}"},
                        {'label': 'Fonte', 'value': 'Database verificato ✅'}
                    ],
                    'tip': f'Dati verificati dal database per {city_detected.title()}',
                    'opening_hours': 'Verifica sul posto',
                    'cost': 'Verifica sul posto'
                })

        # 🔍 STEP 2: Try dynamic generation for all cities (including Genova)
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
                    {'label': 'Fontana',
                        'value': 'Costruita nel 1936, ristrutturata nel 2001'},
                    {'label': 'Palazzi storici',
                        'value': 'Palazzo Ducale, Palazzo della Regione'},
                    {'label': 'Teatro',
                        'value': 'Teatro Carlo Felice (opera house)'},
                    {'label': 'Shopping', 'value': 'Gallerie Mazzini, Via XX Settembre'},
                    {'label': 'Metro',
                        'value': 'Stazione De Ferrari (linea rossa)'}
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
                    {'label': 'Fontana',
                        'value': 'Costruita nel 1936, ristrutturata nel 2001'},
                    {'label': 'Palazzi storici',
                        'value': 'Palazzo Ducale, Palazzo della Regione'},
                    {'label': 'Teatro',
                        'value': 'Teatro Carlo Felice (opera house)'},
                    {'label': 'Shopping', 'value': 'Gallerie Mazzini, Via XX Settembre'},
                    {'label': 'Metro',
                        'value': 'Stazione De Ferrari (linea rossa)'}
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
                    {'label': 'Epoca',
                        'value': 'XII secolo (caruggi medievali)'},
                    {'label': 'Fabrizio De André',
                        'value': 'Canzone "Via del Campo" (1967)'},
                    {'label': 'Caratteristiche',
                        'value': 'Negozi storici, farinata, botteghe artigiane'},
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
                    {'label': 'Costruzione',
                        'value': 'IX-XIV secolo (romanico-gotico)'},
                    {'label': 'Facciata',
                        'value': 'Marmo bianco e nero a strisce orizzontali'},
                    {'label': 'Bomba 1941',
                        'value': 'Proiettile navale britannico inesploso (visibile)'},
                    {'label': 'Tesoro',
                        'value': 'Santo Graal leggendario, reliquie preziose'},
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
                    {'label': 'Dimensioni',
                        'value': '9.700 m² di superficie espositiva'},
                    {'label': 'Apertura',
                        'value': '1992 (Expo Colombo 500 anni)'},
                    {'label': 'Architetto',
                        'value': 'Renzo Piano (Porto Antico)'},
                    {'label': 'Biglietto', 'value': '€29 adulti, €19 bambini'},
                    {'label': 'Attrazioni',
                        'value': 'Delfini, squali, lamantini, pinguini'},
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
                    {'label': 'Progetto Renzo Piano',
                        'value': '1992 (500° scoperta America)'},
                    {'label': 'Biosfera', 'value': 'Serra tropicale in vetro e acciaio'},
                    {'label': 'Bigo', 'value': 'Ascensore panoramico 40m altezza'},
                    {'label': 'Galata Museo del Mare',
                        'value': 'Più grande del Mediterraneo'},
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
                    {'label': 'Orari',
                        'value': 'Lun-Ven 9:00-20:00, Sab-Dom 8:30-20:00 (estate)'},
                    {'label': 'Prezzo', 'value': '€29 adulti, €19 bambini 4-12 anni'},
                    {'label': 'Durata consigliata', 'value': '2-3 ore'},
                    {'label': 'Accessibilità', 'value': 'Completamente accessibile'},
                    {'label': 'Highlights',
                        'value': 'Delfini, squali, tunnel sottomarino, Biosfera'}
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
                    {'label': 'Epoca',
                        'value': 'XII secolo (caruggi medievali)'},
                    {'label': 'Fabrizio De André',
                        'value': 'Canzone "Via del Campo" (1967)'},
                    {'label': 'Caratteristiche',
                        'value': 'Negozi storici, farinata, botteghe artigiane'},
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
                    {'label': 'Costruzione',
                        'value': 'IX-XIV secolo (romanico-gotico)'},
                    {'label': 'Facciata',
                        'value': 'Marmo bianco e nero a strisce orizzontali'},
                    {'label': 'Bomba 1941',
                        'value': 'Proiettile navale britannico inesploso (visibile)'},
                    {'label': 'Tesoro',
                        'value': 'Santo Graal leggendario, reliquie preziose'},
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
                    {'label': 'Orari',
                        'value': 'Lun-Ven 9:00-20:00, Sab-Dom 8:30-20:00 (estate)'},
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
        # Show first 10 keys
        print(f"🔍 Available keys: {list(details_database.keys())[:10]}...")

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
            simple_context = context.replace(
                '_', ' ').replace(',', '').lower().strip()
            for key in details_database.keys():
                simple_key = key.replace('_', ' ').replace(
                    ',', '').lower().strip()
                if simple_key in simple_context or simple_context in simple_key:
                    detail_data = details_database[key]
                    print(
                        f"✅ Partial match found: '{key}' matches '{context}'")
                    break

            # If still not found, try substring matching
            if not detail_data:
                for key in details_database.keys():
                    if any(word in key for word in normalized_context.split('_')):
                        detail_data = details_database[key]
                        print(
                            f"✅ Substring match found: '{key}' for '{context}'")
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

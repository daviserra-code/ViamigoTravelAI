from flask import Blueprint, request, jsonify
import json
import psycopg2
import os
from dotenv import load_dotenv

detail_bp = Blueprint('details', __name__)

load_dotenv()


def _get_details_from_comprehensive_db(context: str) -> dict:
    """
    Query comprehensive_attractions table directly for intelligent router context
    Context format: "palazzo_reale_di_torino_torino"
    """
    try:
        # Parse context: last part is city, rest is attraction name
        parts = context.replace('_', ' ').split()

        # Common Italian city names
        italian_cities = {'roma', 'milano', 'torino', 'venezia', 'firenze', 'napoli',
                          'bologna', 'genova', 'palermo', 'catania', 'bari', 'verona',
                          'padova', 'trieste', 'parma', 'perugia'}

        # Find city name (last matching city in context)
        city_name = None
        attraction_name = None

        for i, part in enumerate(parts):
            if part.lower() in italian_cities:
                city_name = part
                attraction_name = ' '.join(parts[:i])
                break

        # If no city found, last word is probably city
        if not city_name and len(parts) > 1:
            city_name = parts[-1]
            attraction_name = ' '.join(parts[:-1])
        elif not city_name:
            attraction_name = ' '.join(parts)

        if not attraction_name:
            return None

        print(
            f"🔍 Searching comprehensive_attractions: '{attraction_name}' in '{city_name}'")

        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()

        # Query with flexible matching
        query = """
            SELECT name, city, description, category, latitude, longitude, 
                   image_url, wikidata_id
            FROM comprehensive_attractions
            WHERE LOWER(name) LIKE LOWER(%s)
        """
        params = [f'%{attraction_name}%']
        
        if city_name:
            query += " AND LOWER(city) = LOWER(%s)"
            params.append(city_name)
        
        query += " LIMIT 1"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if result:
            name, city, description, category, lat, lng, image_url, wikidata_id = result
            
            formatted_result = {
                'success': True,
                'title': name,
                'summary': (description[:200] + '...') if description and len(description) > 200 else (description or f'{name} a {city}'),
                'description': description or f'Attrazione importante a {city}',
                'imageUrl': image_url,
                'cost': 'Consultare sito ufficiale',
                'opening_hours': 'Consultare sito ufficiale',
                'tip': f'Visita {name} durante gli orari di apertura per la migliore esperienza',
                'source': 'comprehensive_attractions',
                'details': [
                    {'label': 'Città', 'value': city},
                    {'label': 'Categoria', 'value': category or 'Attrazione'},
                ]
            }

            if lat and lng:
                formatted_result['details'].append({
                    'label': 'Coordinate',
                    'value': f"{lat:.4f}, {lng:.4f}"
                })

            if wikidata_id:
                formatted_result['details'].append({
                    'label': 'Wikidata ID',
                    'value': wikidata_id
                })

            cursor.close()
            conn.close()

            print(f"✅ Found in comprehensive_attractions: {name}")
            return formatted_result

        cursor.close()
        conn.close()
        return None

    except Exception as e:
        print(f"❌ Error querying comprehensive_attractions: {e}")
        import traceback
        traceback.print_exc()
        return None


@detail_bp.route('/get_details', methods=['POST'])
def get_details():
    """Scalable details handler using database-first approach"""
    try:
        data = request.get_json()
        context = data.get('context', '')

        print(f"🔍 Processing detail request for context: {context}")

        # PRIORITY 1: Query comprehensive_attractions directly (for intelligent router)
        db_result = _get_details_from_comprehensive_db(context)
        if db_result:
            print(f"✅ Found details in comprehensive_attractions database")
            return jsonify(db_result)

        # PRIORITY 2: Use the intelligent detail handler system
        try:
            from intelligent_detail_handler import IntelligentDetailHandler

            handler = IntelligentDetailHandler()
            user_data = data.get('user_data', {})

            result = handler.get_details(context, user_data)

            if result and result.get('success'):
                print(
                    f"✅ Intelligent handler success: {result.get('source', 'unknown')} source")
                return jsonify(result)
            else:
                print(
                    f"⚠️ Intelligent handler returned empty result, using comprehensive API")

        except Exception as e:
            print(
                f"❌ Intelligent handler error: {e}, trying comprehensive API")

        # PRIORITY 2: Search place_cache table (has Milano data!)
        try:
            import psycopg2
            import os
            import json
            from dotenv import load_dotenv
            load_dotenv()

            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()

            # Search in place_cache with flexible matching
            # Handle variations like "Duomo Milano" vs "Duomo di Milano"
            search_terms = []
            if 'duomo' in context.lower() and 'milano' in context.lower():
                search_terms = ['%duomo%milano%',
                                '%duomo di milano%', '%milano%duomo%']
            else:
                search_terms = [f'%{context}%']

            cursor.execute("""
                SELECT place_name, city, place_data 
                FROM place_cache 
                WHERE place_name ILIKE ANY(%s) OR cache_key ILIKE ANY(%s)
                ORDER BY 
                    CASE WHEN place_name ILIKE %s THEN 1 ELSE 2 END,
                    access_count DESC
                LIMIT 1
            """, (search_terms, search_terms, f'%{context}%'))

            cache_result = cursor.fetchone()

            if cache_result:
                place_name, city, place_data_str = cache_result

                try:
                    place_data = json.loads(place_data_str)

                    formatted_result = {
                        'success': True,
                        'title': place_data.get('title', place_name),
                        'summary': place_data.get('summary', f'Attrazione a {city}'),
                        'description': place_data.get('summary', 'Descrizione non disponibile'),
                        'cost': 'Consultare sito ufficiale',
                        'opening_hours': 'Consultare sito ufficiale',
                        'tip': 'Verifica orari e disponibilità prima della visita',
                        'source': 'place_cache',
                        'details': place_data.get('details', [
                            {'label': 'Città', 'value': city},
                            {'label': 'Tipo', 'value': 'Attrazione'}
                        ])
                    }

                    # Extract cost and hours from place_data if available
                    if place_data.get('details'):
                        for detail in place_data['details']:
                            if 'biglietto' in detail.get('label', '').lower():
                                formatted_result['cost'] = detail.get(
                                    'value', 'Consultare sito ufficiale')

                    if place_data.get('timetable'):
                        timetable_str = ', '.join(
                            [f"{t.get('direction', '')}: {t.get('times', '')}" for t in place_data['timetable']])
                        formatted_result['opening_hours'] = timetable_str

                    cursor.close()
                    conn.close()

                    print(f"✅ Found in place_cache: {place_name}")
                    return jsonify(formatted_result)

                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error in place_cache: {e}")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"❌ place_cache error: {e}, trying comprehensive API")

        # PRIORITY 3: Use comprehensive attractions API
        try:
            import requests
            from urllib.parse import quote

            # Try to search in comprehensive attractions
            search_query = quote(context)
            api_url = f"http://localhost:5000/api/attractions/comprehensive/search?query={search_query}&limit=1"

            response = requests.get(api_url, timeout=5)
            if response.ok:
                data = response.json()
                if data.get('attractions') and len(data['attractions']) > 0:
                    attraction = data['attractions'][0]

                    # Format for frontend
                    formatted_result = {
                        'success': True,
                        'title': attraction.get('name', context),
                        'summary': attraction.get('description', '')[:200] + '...' if attraction.get('description') else f'Attrazione a {attraction.get("city", "")}',
                        'description': attraction.get('description', 'Descrizione non disponibile'),
                        'cost': 'Consultare sito ufficiale',
                        'opening_hours': 'Consultare sito ufficiale',
                        'tip': 'Verifica orari e disponibilità prima della visita',
                        'source': 'database',
                        'details': [
                            {'label': 'Città', 'value': attraction.get(
                                'city', 'N/A')},
                            {'label': 'Categoria', 'value': attraction.get(
                                'category', 'N/A')},
                            {'label': 'Tipo', 'value': attraction.get(
                                'attraction_type', 'Attrazione')}
                        ]
                    }

                    if attraction.get('latitude') and attraction.get('longitude'):
                        formatted_result['details'].append({
                            'label': 'Coordinate',
                            'value': f"{attraction.get('latitude'):.4f}, {attraction.get('longitude'):.4f}"
                        })

                    print(f"✅ Found in comprehensive attractions database")
                    return jsonify(formatted_result)

        except Exception as e:
            print(f"❌ Comprehensive API error: {e}, trying ChromaDB")

        # PRIORITY 3: ChromaDB semantic search
        try:
            from simple_rag_helper import simple_rag

            # Search ChromaDB for relevant information
            rag_result = simple_rag(f"dettagli informazioni {context}")

            if rag_result:
                formatted_result = {
                    'success': True,
                    'title': context.title(),
                    'summary': rag_result[:200] + '...' if len(rag_result) > 200 else rag_result,
                    'description': rag_result,
                    'cost': 'Variabile',
                    'opening_hours': 'Consultare fonti ufficiali',
                    'tip': 'Informazioni ottenute da knowledge base',
                    'source': 'chromadb',
                    'details': [
                        {'label': 'Fonte', 'value': 'Knowledge Base'},
                        {'label': 'Tipo', 'value': 'Attrazione'}
                    ]
                }

                print(f"✅ Found information in ChromaDB")
                return jsonify(formatted_result)

        except Exception as e:
            print(f"❌ ChromaDB error: {e}, trying Apify")

        # PRIORITY 4: Apify real-time data
        try:
            from apify_integration import ApifyTravelIntegration

            apify = ApifyTravelIntegration()
            apify_result = apify.get_attraction_details(context)

            if apify_result and apify_result.get('success'):
                print(f"✅ Found details via Apify")
                return jsonify(apify_result)

        except Exception as e:
            print(f"❌ Apify error: {e}, using fallback")

        # Final fallback
        return _legacy_get_details(context)

    except Exception as e:
        print(f"❌ Detail handler error: {e}")
        return jsonify({
            'error': 'Detail generation failed',
            'title': 'Informazioni non disponibili',
            'summary': 'Si è verificato un errore nel recuperare i dettagli.',
            'details': [],
            'tip': 'Riprova più tardi',
            'opening_hours': 'N/A',
            'cost': 'N/A'
        }), 500


def _legacy_get_details(context):
    """Legacy detail handler with basic functionality for backward compatibility"""
    return jsonify({
        'title': context.replace('_', ' ').title(),
        'summary': f'Informazioni su {context.replace("_", " ")}',
        'details': [
            {'label': 'Tipo', 'value': 'Attrazione'},
            {'label': 'Posizione', 'value': 'Italia'}
        ],
        'tip': 'Visita durante gli orari di apertura',
        'opening_hours': 'Consultare sito ufficiale',
        'cost': 'Variabile'
    })

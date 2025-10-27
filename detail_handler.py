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

            # 🎯 ENHANCE DESCRIPTION - Get rich context from ChromaDB
            enhanced_description = description or f'Attrazione importante a {city}'
            historical_context = None
            insider_tips = []

            try:
                from simple_rag_helper import rag_helper
                # Query ChromaDB for rich context about this attraction
                chroma_results = rag_helper.semantic_search_places(
                    query=f"{name} {city} storia cultura",
                    city=city,
                    n_results=3
                )
                if chroma_results and len(chroma_results) > 0:
                    # Extract historical/cultural context from first result
                    first_result = chroma_results[0]
                    if 'description' in first_result:
                        historical_context = first_result['description'][:300] + \
                            '...' if len(
                                first_result['description']) > 300 else first_result['description']

                    # Extract insider tips from additional results
                    for result in chroma_results[1:3]:
                        desc = result.get('description', '')
                        if 'tip' in desc.lower() or 'consiglio' in desc.lower():
                            insider_tips.append(desc[:150])

                    print(
                        f"✅ ChromaDB enriched {name} with {len(chroma_results)} results")
            except Exception as e:
                print(f"⚠️ ChromaDB context query failed: {e}")

            # Build comprehensive description
            full_description = enhanced_description
            if historical_context and historical_context != enhanced_description:
                full_description += f"\n\n📜 Contesto Storico: {historical_context}"

            # Generate contextual tips based on category
            contextual_tips = []
            if category and 'museum' in category.lower():
                contextual_tips.append("🎨 Prenota online per evitare code")
                contextual_tips.append(
                    "📸 Verifica le politiche fotografiche prima di visitare")
            elif category and 'church' in category.lower():
                contextual_tips.append("👔 Abbigliamento appropriato richiesto")
                contextual_tips.append(
                    "🔇 Silenzio durante le funzioni religiose")
            elif category and 'park' in category.lower():
                contextual_tips.append(
                    "☀️ Miglior visita in giornate soleggiate")
                contextual_tips.append("🥪 Ottimo per picnic e relax")

            # Combine insider tips from ChromaDB + contextual tips
            all_tips = (insider_tips + contextual_tips)[:3]  # Max 3 tips
            tip_text = ' | '.join(
                all_tips) if all_tips else f'Visita {name} durante gli orari di apertura per la migliore esperienza'

            formatted_result = {
                'success': True,
                'title': name,
                'summary': (enhanced_description[:200] + '...') if len(enhanced_description) > 200 else enhanced_description,
                'description': full_description,
                'imageUrl': image_url,
                'cost': 'Consultare sito ufficiale per tariffe aggiornate',
                'opening_hours': 'Consultare sito ufficiale per orari aggiornati',
                'tip': tip_text,
                'source': 'comprehensive_attractions+chromadb' if historical_context else 'comprehensive_attractions',
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


def _enhance_generic_result(context: str, apify_data: dict = None) -> dict:
    """
    Enhance generic/fallback results with context-aware information
    """
    # Parse context to extract place name and city
    parts = context.replace('_', ' ').split()
    italian_cities = {'roma', 'milano', 'torino', 'venezia', 'firenze', 'napoli',
                      'bologna', 'genova', 'palermo', 'catania', 'bari', 'verona',
                      'padova', 'trieste'}

    city_name = None
    place_name = None

    for i, part in enumerate(parts):
        if part.lower() in italian_cities:
            city_name = part.title()
            place_name = ' '.join(parts[:i]).title()
            break

    if not city_name and len(parts) > 1:
        city_name = parts[-1].title()
        place_name = ' '.join(parts[:-1]).title()
    else:
        place_name = ' '.join(parts).title()

    # Enhanced descriptions for common Italian landmarks
    enhanced_descriptions = {
        'piazza castello': {
            'torino': {
                'summary': 'Piazza Castello è la piazza principale di Torino, cuore del centro storico. Circondata da portici e edifici monumentali come Palazzo Reale e Palazzo Madama, è il fulcro della vita culturale torinese.',
                'description': 'La piazza, di forma rettangolare, è dominata dal maestoso Palazzo Reale e da Palazzo Madama. È il centro nevralgico della città, punto di partenza ideale per esplorare il centro storico. Ospita eventi culturali e manifestazioni durante tutto l\'anno.',
                'tips': [
                    'Visita Palazzo Reale e i suoi giardini',
                    'Ammira Palazzo Madama, patrimonio UNESCO',
                    'Passeggia sotto i portici per ripararti dal sole o dalla pioggia',
                    'La piazza è pedonale, perfetta per una passeggiata'
                ],
                'best_time': 'Mattino per foto senza folla, sera per l\'illuminazione suggestiva'
            }
        },
        'piazza san carlo': {
            'torino': {
                'summary': 'Conosciuta come "il salotto di Torino", è una delle piazze più eleganti della città, circondata da caffè storici e palazzi barocchi.',
                'description': 'Piazza San Carlo, di forma rettangolare perfettamente simmetrica, è ornata dalla statua equestre di Emanuele Filiberto al centro e circondata da portici con caffè storici. Le chiese gemelle di San Carlo e Santa Cristina completano lo scenario barocco.',
                'tips': [
                    'Fermati al Caffè Torino o al Caffè San Carlo, caffè storici',
                    'Ammira le chiese gemelle',
                    'Passeggia sotto i portici',
                    'Ideale per shopping di lusso'
                ],
                'best_time': 'Pomeriggio per aperitivo nei caffè storici'
            }
        }
    }

    # Get enhanced info if available
    place_key = place_name.lower()
    enhanced = None
    if place_key in enhanced_descriptions:
        city_key = city_name.lower() if city_name else None
        if city_key and city_key in enhanced_descriptions[place_key]:
            enhanced = enhanced_descriptions[place_key][city_key]

    # Build result
    result = {
        'success': True,
        'title': place_name,
        'source': 'enhanced_fallback'
    }

    if enhanced:
        result['summary'] = enhanced['summary']
        result['description'] = enhanced['description']
        result['tip'] = enhanced['tips'][0] if enhanced['tips'] else 'Consulta informazioni locali'
        result['opening_hours'] = enhanced.get(
            'best_time', 'Sempre accessibile')
        result['cost'] = 'Gratuito (piazza pubblica)'
        result['details'] = [
            {'label': 'Città', 'value': city_name or 'Italia'},
            {'label': 'Tipo', 'value': 'Piazza storica'},
            {'label': 'Miglior orario', 'value': enhanced.get(
                'best_time', 'Tutto il giorno')},
        ]
        # Add all tips as additional details
        for tip in enhanced['tips']:
            result['details'].append({'label': '💡 Suggerimento', 'value': tip})
    elif apify_data and apify_data.get('description'):
        # Use Apify data but enhance it
        result['summary'] = f"{place_name} a {city_name}" if city_name else place_name
        result['description'] = apify_data.get(
            'description', f'Attrazione importante a {city_name}')
        result['tip'] = 'Verifica orari e disponibilità prima della visita'
        result['opening_hours'] = 'Consultare fonti ufficiali'
        result['cost'] = 'Consultare sito ufficiale'
        result['details'] = [
            {'label': 'Città', 'value': city_name or 'Italia'},
            {'label': 'Tipo', 'value': apify_data.get(
                'category', 'Attrazione')},
        ]
        if apify_data.get('rating'):
            result['details'].append({
                'label': 'Rating',
                'value': f"{apify_data['rating']} ⭐"
            })
        if apify_data.get('image_url'):
            result['imageUrl'] = apify_data['image_url']
    else:
        # Generic fallback
        result['summary'] = f"{place_name} è un'importante attrazione a {city_name}" if city_name else f"{place_name} è un luogo di interesse"
        result['description'] = f"Luogo storico e culturale nel centro di {city_name}. Merita una visita per scoprire la storia e l'atmosfera locale." if city_name else "Luogo di interesse storico e culturale."
        result['tip'] = 'Chiedi informazioni ai locals per scoprire curiosità'
        result['opening_hours'] = 'Consultare fonti ufficiali'
        result['cost'] = 'Variabile'
        result['details'] = [
            {'label': 'Città', 'value': city_name or 'Italia'},
            {'label': 'Tipo', 'value': 'Attrazione'},
            {'label': 'Nota', 'value': 'Informazioni dettagliate in aggiornamento'}
        ]

    print(f"✅ Created enhanced fallback for {place_name} ({result['source']})")
    return result


@detail_bp.route('/get_details', methods=['POST'])
def get_details():
    """Scalable details handler using database-first approach"""
    try:
        import time
        start_time = time.time()
        
        data = request.get_json()
        context = data.get('context', '')

        print(f"🔍 Processing detail request for context: {context}")

        # PRIORITY 1: Query comprehensive_attractions directly (for intelligent router)
        print(f"⏱️ Starting comprehensive_attractions query...")
        db_result = _get_details_from_comprehensive_db(context)
        print(f"⏱️ Comprehensive DB query took {time.time() - start_time:.2f}s")
        if db_result:
            print(f"✅ Found details in comprehensive_attractions database")
            return jsonify(db_result)

        # PRIORITY 2: ChromaDB semantic search (FAST and uses sentence transformers!)
        try:
            print(f"⏱️ Starting ChromaDB semantic search...")
            chroma_start = time.time()
            from simple_rag_helper import rag_helper

            # Search ChromaDB for relevant information about this place
            search_results = rag_helper.semantic_search_places(
                query=context,
                n_results=1
            )

            if search_results and len(search_results) > 0:
                place = search_results[0]
                
                formatted_result = {
                    'success': True,
                    'title': place.get('name', context.title()),
                    'summary': place.get('description', '')[:200] + '...' if place.get('description') and len(place.get('description', '')) > 200 else place.get('description', f'Attrazione trovata tramite ricerca semantica'),
                    'description': place.get('description', 'Descrizione non disponibile'),
                    'cost': 'Variabile',
                    'opening_hours': 'Consultare fonti ufficiali',
                    'tip': 'Informazioni ottenute da knowledge base semantica',
                    'source': 'chromadb',
                    'details': [
                        {'label': 'Fonte', 'value': 'Knowledge Base (Semantic Search)'},
                        {'label': 'Tipo', 'value': place.get('category', 'Attrazione')},
                        {'label': 'Rilevanza', 'value': f"{place.get('score', 0):.2%}"}
                    ]
                }

                if place.get('city'):
                    formatted_result['details'].insert(0, {'label': 'Città', 'value': place.get('city')})

                print(f"✅ Found information in ChromaDB in {time.time() - chroma_start:.2f}s")
                return jsonify(formatted_result)
            else:
                print(f"⚠️ ChromaDB returned no results, trying place_cache")

        except Exception as e:
            print(f"❌ ChromaDB error: {e}, trying place_cache")

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
            print(f"❌ Comprehensive API error: {e}, trying Apify as last resort")

        # PRIORITY 5 (LAST RESORT): Apify real-time data - expensive and slow!
        print(f"⚠️ All fast sources exhausted, trying Apify as LAST RESORT...")
        apify_start = time.time()
        try:
            from intelligent_detail_handler import IntelligentDetailHandler

            handler = IntelligentDetailHandler()
            user_data = data.get('user_data', {})

            print(f"⏱️ Calling Apify handler (this may take 30+ seconds)...")
            result = handler.get_details(context, user_data)
            print(f"⏱️ Apify took {time.time() - apify_start:.2f}s")

            if result and result.get('success'):
                print(f"✅ Apify success: {result.get('source', 'unknown')} source")
                return jsonify(result)
            else:
                print(f"⚠️ Apify returned empty result, using fallback")

        except Exception as e:
            print(f"❌ Apify error: {e}, using enhanced fallback")

        # Final fallback - use enhanced version with context-aware descriptions
        enhanced_result = _enhance_generic_result(context, None)
        return jsonify(enhanced_result)

    except Exception as e:
        print(f"❌ Detail handler error: {e}")
        # Even on error, try enhanced fallback
        try:
            enhanced_result = _enhance_generic_result(
                request.get_json().get('context', ''))
            return jsonify(enhanced_result)
        except:
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

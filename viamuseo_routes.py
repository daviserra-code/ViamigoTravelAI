#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Viamuseo Routes - Museum Virtual Visit Experience
Provides endpoints for museum collection exploration, artwork viewing,
and AI-powered museum information via ChromaDB
"""

from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from typing import Dict, List, Optional
import chromadb

viamuseo_bp = Blueprint('viamuseo', __name__)
log = logging.getLogger('viamigo.viamuseo')

# Database connection


def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(os.getenv('DATABASE_URL'))


# ChromaDB client for museum Q&A
try:
    chroma_client = chromadb.PersistentClient(path="./chroma_museums")
    museum_collection = chroma_client.get_collection("museum_collections")
    log.info("✅ ChromaDB museum collection loaded")
except Exception as e:
    log.warning(f"⚠️ ChromaDB museum collection not available: {e}")
    chroma_client = None
    museum_collection = None


@viamuseo_bp.route('/api/viamuseo/check-museum', methods=['POST'])
def check_museum():
    """
    Check if an attraction is a museum with collection data
    Returns museum info + whether Viamuseo experience is available
    """
    try:
        data = request.get_json()
        attraction_name = data.get('name')
        attraction_id = data.get('id')

        if not attraction_name and not attraction_id:
            return jsonify({'error': 'Name or ID required'}), 400

        # Clean attraction name: remove city suffix (e.g., "Galleria Borghese, Rome" -> "Galleria Borghese")
        if attraction_name and ',' in attraction_name:
            attraction_name = attraction_name.split(',')[0].strip()
            log.info(f"🔍 Cleaned name: {attraction_name}")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # CRITICAL FIX: First check if the attraction ITSELF is a museum
        # This prevents "Piazza Duomo" (attraction) from matching "Ipogeo di piazza Duomo" (museum)
        if attraction_id:
            # Check by ID - is THIS attraction a museum?
            cur.execute("""
                SELECT category FROM comprehensive_attractions WHERE id = %s
            """, (attraction_id,))
            cat_result = cur.fetchone()
            if cat_result and cat_result['category'] not in ('museum', 'tourism:museum'):
                log.info(
                    f"❌ Attraction ID {attraction_id} is NOT a museum (category={cat_result['category']})")
                cur.close()
                conn.close()
                return jsonify({
                    'is_museum': False,
                    'has_viamuseo': False,
                    'reason': f'This is a {cat_result["category"]}, not a museum'
                })
        elif attraction_name:
            # Check by name - is THIS attraction a museum?
            cur.execute("""
                SELECT id, category FROM comprehensive_attractions 
                WHERE name = %s OR name ILIKE %s
                ORDER BY 
                    CASE WHEN name = %s THEN 1 ELSE 2 END
                LIMIT 1
            """, (attraction_name, f'%{attraction_name}%', attraction_name))
            cat_result = cur.fetchone()
            if cat_result:
                if cat_result['category'] not in ('museum', 'tourism:museum'):
                    log.info(
                        f"❌ Attraction '{attraction_name}' is NOT a museum (category={cat_result['category']})")
                    cur.close()
                    conn.close()
                    return jsonify({
                        'is_museum': False,
                        'has_viamuseo': False,
                        'reason': f'This is a {cat_result["category"]}, not a museum'
                    })
                # It IS a museum, use this ID for the query
                attraction_id = cat_result['id']

        # Check if attraction is a museum with collections
        if attraction_id:
            query = """
                SELECT 
                    ca.id,
                    ca.name,
                    ca.city,
                    ca.description,
                    ca.latitude,
                    ca.longitude,
                    ca.wikidata_id,
                    ca.wikipedia_url,
                    mc.total_artworks,
                    mc.collection_types,
                    CASE 
                        WHEN mc.id IS NOT NULL THEN true 
                        ELSE false 
                    END as has_viamuseo
                FROM comprehensive_attractions ca
                LEFT JOIN museum_collections mc ON ca.id = mc.attraction_id
                WHERE ca.id = %s AND ca.category IN ('museum', 'tourism:museum')
            """
            cur.execute(query, (attraction_id,))
        else:
            # Try exact match first (prioritize to avoid cross-city confusion)
            query = """
                SELECT 
                    ca.id,
                    ca.name,
                    ca.city,
                    ca.description,
                    ca.latitude,
                    ca.longitude,
                    ca.wikidata_id,
                    ca.wikipedia_url,
                    mc.total_artworks,
                    mc.collection_types,
                    CASE 
                        WHEN mc.id IS NOT NULL THEN true 
                        ELSE false 
                    END as has_viamuseo
                FROM comprehensive_attractions ca
                LEFT JOIN museum_collections mc ON ca.id = mc.attraction_id
                WHERE ca.name = %s AND ca.category IN ('museum', 'tourism:museum')
                LIMIT 1
            """
            cur.execute(query, (attraction_name,))
            museum = cur.fetchone()

            # If no exact match, try ILIKE (but this can match wrong museums like Ipogeo di piazza Duomo)
            if not museum:
                query = """
                    SELECT 
                        ca.id,
                        ca.name,
                        ca.city,
                        ca.description,
                        ca.latitude,
                        ca.longitude,
                        ca.wikidata_id,
                        ca.wikipedia_url,
                        mc.total_artworks,
                        mc.collection_types,
                        CASE 
                            WHEN mc.id IS NOT NULL THEN true 
                            ELSE false 
                        END as has_viamuseo
                    FROM comprehensive_attractions ca
                    LEFT JOIN museum_collections mc ON ca.id = mc.attraction_id
                    WHERE ca.name ILIKE %s AND ca.category IN ('museum', 'tourism:museum')
                    ORDER BY 
                        CASE 
                            WHEN ca.name = %s THEN 1
                            WHEN ca.name ILIKE %s THEN 2
                            ELSE 3
                        END,
                        mc.total_artworks DESC NULLS LAST
                    LIMIT 1
                """
                cur.execute(
                    query, (f'%{attraction_name}%', attraction_name, f'{attraction_name}%'))
                museum = cur.fetchone()
            else:
                museum = museum  # Use exact match result

        museum = cur.fetchone()
        cur.close()
        conn.close()

        if not museum:
            log.info(f"❌ No museum found for: {attraction_name}")
            return jsonify({
                'is_museum': False,
                'has_viamuseo': False
            })

        log.info(
            f"✅ Museum check: {attraction_name} -> has_viamuseo={museum['has_viamuseo']}, total_artworks={museum.get('total_artworks', 0)}")
        return jsonify({
            'is_museum': True,
            'has_viamuseo': museum['has_viamuseo'],
            'museum_id': museum['id'],
            'total_artworks': museum.get('total_artworks', 0),
            'museum': dict(museum)
        })

    except Exception as e:
        log.error(f"Error checking museum: {e}")
        return jsonify({'error': str(e)}), 500


@viamuseo_bp.route('/api/viamuseo/museum/<int:museum_id>', methods=['GET'])
def get_museum_details(museum_id):
    """
    Get full museum details including all artworks and collections
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get museum info
        cur.execute("""
            SELECT 
                ca.id,
                ca.name,
                ca.city,
                ca.description,
                ca.latitude,
                ca.longitude,
                ca.wikidata_id,
                ca.wikipedia_url,
                ca.image_url,
                mc.artworks,
                mc.collection_types,
                mc.visitor_stats,
                mc.total_artworks
            FROM comprehensive_attractions ca
            JOIN museum_collections mc ON ca.id = mc.attraction_id
            WHERE ca.id = %s
        """, (museum_id,))

        museum = cur.fetchone()
        cur.close()
        conn.close()

        if not museum:
            return jsonify({'error': 'Museum not found'}), 404

        return jsonify({'museum': dict(museum)})

    except Exception as e:
        log.error(f"Error fetching museum details: {e}")
        return jsonify({'error': str(e)}), 500


@viamuseo_bp.route('/api/viamuseo/museum/<int:museum_id>/artworks', methods=['GET'])
def get_museum_artworks(museum_id):
    """
    Get paginated artworks for a museum
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT mc.artworks, mc.total_artworks
            FROM museum_collections mc
            JOIN comprehensive_attractions ca ON ca.id = mc.attraction_id
            WHERE ca.id = %s
        """, (museum_id,))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Museum not found'}), 404

        artworks = result['artworks'] or []
        total = result['total_artworks'] or 0

        # Paginate artworks
        start = (page - 1) * per_page
        end = start + per_page
        paginated = artworks[start:end]

        return jsonify({
            'artworks': paginated,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })

    except Exception as e:
        log.error(f"Error fetching artworks: {e}")
        return jsonify({'error': str(e)}), 500


@viamuseo_bp.route('/api/viamuseo/museum/<int:museum_id>/ask', methods=['POST'])
def ask_museum_question(museum_id):
    """
    Ask questions about the museum using ChromaDB semantic search
    """
    try:
        data = request.get_json()
        question = data.get('question')

        if not question:
            return jsonify({'error': 'Question required'}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get museum context
        cur.execute("""
            SELECT 
                ca.id,
                ca.name,
                ca.description,
                ca.city,
                ca.osm_tags,
                ca.wikidata_id,
                ca.wikipedia_url,
                mc.artworks,
                mc.collection_types,
                mc.total_artworks
            FROM comprehensive_attractions ca
            JOIN museum_collections mc ON ca.id = mc.attraction_id
            WHERE ca.id = %s
        """, (museum_id,))

        museum = cur.fetchone()
        cur.close()
        conn.close()

        if not museum:
            return jsonify({'error': 'Museum not found'}), 404

        # Extract practical info from OSM tags
        osm_tags = museum['osm_tags'] or {}
        opening_hours = osm_tags.get('opening_hours')
        website = osm_tags.get('website') or osm_tags.get('contact:website')
        phone = osm_tags.get('phone') or osm_tags.get('contact:phone')
        address = osm_tags.get('addr:full') or osm_tags.get('addr:street')

        question_lower = question.lower()

        # Check if question is about practical info (hours, address, tickets, etc)
        practical_keywords = ['orar', 'aper', 'chiuso', 'indirizzo', 'dove', 'bigliett', 'prezzo', 'costo',
                              'telefo', 'contatt', 'sito', 'web', 'email', 'come arrivare']
        is_practical = any(
            keyword in question_lower for keyword in practical_keywords)

        answer = ""

        if is_practical:
            # Answer practical questions directly from museum data
            if any(word in question_lower for word in ['orar', 'aper', 'chiuso', 'quando']):
                if opening_hours:
                    answer = f"Orari di apertura del {museum['name']}:\n\n{opening_hours}"
                else:
                    answer = f"Gli orari di apertura del {museum['name']} non sono disponibili al momento. "
                    if website:
                        answer += f"Puoi consultare il sito ufficiale: {website}"

            elif any(word in question_lower for word in ['indirizzo', 'dove', 'come arrivare', 'posizione']):
                if address:
                    answer = f"Il {museum['name']} si trova in {address}"
                    if museum['city']:
                        answer += f", {museum['city']}."
                else:
                    answer = f"Il {museum['name']} si trova a {museum['city']}."

            elif any(word in question_lower for word in ['bigliett', 'prezzo', 'costo', 'ingresso']):
                answer = f"Per informazioni su biglietti e prezzi del {museum['name']}, "
                if website:
                    answer += f"ti consiglio di consultare il sito ufficiale: {website}"
                elif phone:
                    answer += f"puoi contattare il museo al: {phone}"
                else:
                    answer += "ti consiglio di contattare direttamente il museo."

            elif any(word in question_lower for word in ['telefo', 'contatt', 'email']):
                if phone:
                    answer = f"Puoi contattare il {museum['name']} al numero: {phone}"
                if website:
                    answer += f"\n\nSito web: {website}"
                if not phone and not website:
                    answer = f"I contatti del {museum['name']} non sono disponibili al momento."

            elif any(word in question_lower for word in ['sito', 'web', 'website']):
                if website:
                    answer = f"Il sito web del {museum['name']} è: {website}"
                else:
                    answer = f"Il sito web del {museum['name']} non è disponibile al momento."

            # If we answered, return immediately
            if answer:
                return jsonify({
                    'question': question,
                    'answer': answer,
                    'context': f"Practical info: {museum['name']}"
                })

        # For artwork/collection questions, use ChromaDB semantic search
        artworks = museum['artworks'] or []

        # Check for specific artist mentions in the question
        specific_artist = None
        artist_names = set(a.get('artist', '')
                           for a in artworks if a.get('artist'))
        for artist in artist_names:
            if artist and len(artist) > 3 and not artist.startswith('http'):
                artist_words = artist.lower().split()
                if any(word in question_lower for word in artist_words if len(word) > 3):
                    specific_artist = artist
                    break

        if specific_artist:
            # Query about specific artist
            artist_works = [a for a in artworks if a.get(
                'artist') == specific_artist]
            answer = f"{specific_artist} è presente al {museum['name']} con "
            if len(artist_works) == 1:
                work = artist_works[0]
                work_name = work.get('name', work.get('title', "un'opera"))
                answer += f"l'opera '{work_name}'"
                if work.get('year'):
                    answer += f" ({work.get('year')})"
            else:
                answer += f"{len(artist_works)} opere"
                valid_names = [w.get('name', w.get('title', '')) for w in artist_works[:3]
                               if w.get('name') and not w.get('name', '').startswith('Q') and len(w.get('name', '')) > 3]
                if valid_names:
                    quoted_names = ', '.join([f"'{n}'" for n in valid_names])
                    answer += f": {quoted_names}"
                    if len(artist_works) > len(valid_names):
                        answer += " e altre"
            answer += "."

        elif any(word in question_lower for word in ['famose', 'importanti', 'principali', 'capolavori', 'migliori']):
            # Question about famous/important works
            answer = f"Tra le opere principali del {museum['name']} ci sono:\n\n"
            displayed = 0
            for artwork in artworks[:10]:
                name = artwork.get('name', artwork.get('title', ''))
                if name and not name.startswith('Q') and not name.startswith('http') and len(name) > 3:
                    artist = artwork.get('artist', 'Artista sconosciuto')
                    if not artist.startswith('http'):
                        year = f" ({artwork.get('year')})" if artwork.get(
                            'year') else ""
                        answer += f"• {name} di {artist}{year}\n"
                        displayed += 1
                        if displayed >= 5:
                            break

            if displayed == 0:
                answer = f"Il {museum['name']} ospita una collezione di {len(artworks)} opere d'arte."
            elif len(artworks) > displayed:
                answer += f"\nLa collezione comprende in totale {len(artworks)} opere."

        elif any(word in question_lower for word in ['parlami', 'racconta', 'dimmi', 'approfond', 'dettagli']):
            # Deep dive request
            if museum['description']:
                answer = f"{museum['description']}\n\n"
            answer += f"Il {museum['name']} custodisce una collezione di {len(artworks)} opere d'arte. "

            # Count unique valid artists
            valid_artists = set(a.get('artist') for a in artworks
                                if a.get('artist') and not a.get('artist', '').startswith('http')
                                and not a.get('artist', '').startswith('Q'))
            if valid_artists:
                answer += f"La collezione include opere di {len(valid_artists)} artisti diversi. "

            # Mention top represented artists
            artist_counts = {}
            for a in artworks:
                artist = a.get('artist', '')
                if artist and not artist.startswith('http') and not artist.startswith('Q') and len(artist) > 3:
                    artist_counts[artist] = artist_counts.get(artist, 0) + 1

            if artist_counts:
                top_artists = sorted(artist_counts.items(),
                                     key=lambda x: x[1], reverse=True)[:3]
                answer += "\n\nArtisti ben rappresentati nella collezione: "
                answer += ", ".join(
                    [f"{a[0]} ({a[1]} {'opera' if a[1] == 1 else 'opere'})" for a in top_artists]) + "."

        elif any(word in question_lower for word in ['artisti', 'autori', 'pittori']):
            # Question about artists
            artist_counts = {}
            for a in artworks:
                artist = a.get('artist', '')
                if artist and not artist.startswith('http') and not artist.startswith('Q') and len(artist) > 3:
                    artist_counts[artist] = artist_counts.get(artist, 0) + 1

            if artist_counts:
                answer = f"Nella collezione del {museum['name']} sono presenti opere di {len(artist_counts)} artisti. "
                top_artists = sorted(artist_counts.items(),
                                     key=lambda x: x[1], reverse=True)[:5]
                answer += "Tra i principali: " + \
                    ", ".join([a[0] for a in top_artists]) + "."
            else:
                answer = f"Il {museum['name']} ospita una collezione di {len(artworks)} opere d'arte."

        else:
            # General overview
            answer = f"Il {museum['name']} "
            if museum['description']:
                answer += f"{museum['description']} "
            else:
                answer += f"a {museum['city']} "

            answer += f"ospita una collezione di {len(artworks)} opere d'arte. "

            # Add one notable work as example if available
            notable_works = [a for a in artworks[:5]
                             if a.get('name') and not a.get('name', '').startswith('Q')
                             and not a.get('name', '').startswith('http') and len(a.get('name', '')) > 3]
            if notable_works:
                work = notable_works[0]
                artist = work.get('artist', 'autore ignoto')
                if not artist.startswith('http'):
                    answer += f"Tra le opere: '{work.get('name')}' di {artist}."

        # Build context for debugging
        context = f"Museum: {museum['name']}\nQuestion: {question}\nArtworks: {len(artworks)}"

        return jsonify({
            'question': question,
            'answer': answer,
            'context': context
        })

    except Exception as e:
        log.error(f"Error processing question: {e}")
        return jsonify({'error': str(e)}), 500


@viamuseo_bp.route('/api/viamuseo/search', methods=['GET'])
def search_museums():
    """
    Search for museums with Viamuseo experience
    """
    try:
        query = request.args.get('q', '')
        city = request.args.get('city', '')
        limit = request.args.get('limit', 10, type=int)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        sql = """
            SELECT 
                ca.id,
                ca.name,
                ca.city,
                ca.description,
                mc.total_artworks,
                mc.collection_types
            FROM comprehensive_attractions ca
            JOIN museum_collections mc ON ca.id = mc.attraction_id
            WHERE ca.category = 'museum'
        """

        params = []
        if query:
            sql += " AND ca.name ILIKE %s"
            params.append(f'%{query}%')
        if city:
            sql += " AND ca.city ILIKE %s"
            params.append(f'%{city}%')

        sql += " ORDER BY mc.total_artworks DESC LIMIT %s"
        params.append(limit)

        cur.execute(sql, params)
        museums = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'museums': [dict(m) for m in museums],
            'count': len(museums)
        })

    except Exception as e:
        log.error(f"Error searching museums: {e}")
        return jsonify({'error': str(e)}), 500

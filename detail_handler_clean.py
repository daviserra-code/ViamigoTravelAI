from flask import Blueprint, request, jsonify
import json

detail_bp = Blueprint('details', __name__)

@detail_bp.route('/get_details', methods=['POST'])
def get_details():
    """Enhanced details handler using intelligent multi-stage approach"""
    try:
        data = request.get_json()
        context = data.get('context', '')
        
        print(f"🔍 Processing detail request for context: {context}")

        # Use intelligent detail handler for scalable approach
        try:
            from intelligent_detail_handler import get_intelligent_details
            
            # Pass user data if available from session
            user_data = data.get('user_data', {})
            
            result = get_intelligent_details(context, user_data)
            
            if result.get('success'):
                print(f"✅ Intelligent handler success: {result.get('source', 'unknown')} source")
                return jsonify(result)
            else:
                print(f"⚠️ Intelligent handler failed, using legacy fallback")
                
        except Exception as e:
            print(f"❌ Intelligent handler error: {e}, falling back to legacy")
        
        # Legacy fallback for compatibility
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
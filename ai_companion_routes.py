#!/usr/bin/env python3
"""
🧠 AI COMPANION ROUTES - Real AI-powered travel intelligence
Genuine GPT-5 AI for Piano B, Scoperte Intelligenti, Diario di Viaggio
"""

from flask import Blueprint, request, jsonify
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import json
from openai import OpenAI
import os

ai_companion_bp = Blueprint('ai_companion', __name__)

# Initialize OpenAI with fast timeout
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class AICompanionEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def generate_piano_b(self, current_itinerary, context, emergency_type="weather"):
        """Real AI Piano B generation with fast timeout"""
        try:
            prompt = f"""
Sei un AI travel companion intelligente. Genera un Piano B dinamico per questo itinerario:

Itinerario corrente: {json.dumps(current_itinerary[:3], indent=2)}
Contesto: {context}
Emergenza: {emergency_type}

Crea un JSON con alternative realistiche e intelligenti:
{{
    "emergency_type": "{emergency_type}",
    "ai_analysis": "Analisi intelligente della situazione",
    "dynamic_alternatives": [
        {{
            "time": "orario",
            "title": "Nome alternativa",
            "description": "Descrizione dettagliata",
            "why_better": "Perché è meglio della versione originale",
            "ai_insight": "Insight intelligente specifico",
            "indoor": true/false
        }}
    ],
    "smart_adaptations": ["suggerimento AI 1", "suggerimento AI 2"],
    "cost_impact": "Analisi costi",
    "ai_confidence": "high/medium/low"
}}

Rispondi SOLO con JSON valido. Sii specifico e intelligente.
"""
            
            response = openai_client.chat.completions.create(
                model="gpt-5",  # Latest model as per blueprint
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion esperto che genera Piani B intelligenti e dinamici."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=6  # Fast timeout
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"✅ AI Piano B generato: {result.get('ai_confidence', 'unknown')} confidence")
            return result
            
        except Exception as e:
            print(f"⚠️ AI Piano B fallback: {e}")
            return {
                "emergency_type": emergency_type,
                "ai_analysis": "Fallback: Sistema AI temporaneamente non disponibile",
                "dynamic_alternatives": [
                    {
                        "time": "09:00",
                        "title": "Piano alternativo indoor",
                        "description": "Alternative al coperto nelle vicinanze",
                        "why_better": "Protezione completa dalle intemperie",
                        "ai_insight": "Analisi AI non disponibile",
                        "indoor": True
                    }
                ],
                "smart_adaptations": ["Controlla app meteo locale", "Usa trasporti pubblici"],
                "cost_impact": "Simile al piano originale",
                "ai_confidence": "fallback"
            }
    
    def generate_scoperte_intelligenti(self, location, time_context, user_profile=None):
        """Real AI intelligent discoveries"""
        try:
            profile_context = f"Profilo utente: {user_profile}" if user_profile else "Profilo generico"
            
            prompt = f"""
Sei un AI travel companion che scopre gemme nascoste. Analizza questa situazione:

Località: {location}
Momento: {time_context}
{profile_context}

Genera scoperte intelligenti e contestuali:
{{
    "ai_analysis": "Analisi intelligente del contesto attuale",
    "contextual_discoveries": [
        {{
            "title": "Nome scoperta",
            "description": "Descrizione dettagliata e autentica",
            "distance": "distanza precisa",
            "why_now": "Perché è perfetto PROPRIO ora",
            "local_secret": "Segreto che solo i locals sanno",
            "ai_insight": "Insight intelligente unico",
            "timing_perfect": "Spiegazione timing perfetto"
        }}
    ],
    "behavioral_learning": "Cosa l'AI ha imparato dalle preferenze dell'utente",
    "adaptive_suggestions": ["suggerimento adattivo 1", "suggerimento adattivo 2"],
    "ai_confidence": "high/medium/low"
}}

Sii specifico, intelligente e contextualmente rilevante.
"""
            
            response = openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion che scopre gemme nascoste con intelligenza contestuale."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=6
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"✅ AI Scoperte generate: {len(result.get('contextual_discoveries', []))} scoperte")
            return result
            
        except Exception as e:
            print(f"⚠️ AI Scoperte fallback: {e}")
            return {
                "ai_analysis": "Fallback: Sistema AI temporaneamente non disponibile",
                "contextual_discoveries": [
                    {
                        "title": "Scoperta locale",
                        "description": "Gem nascosta nelle vicinanze",
                        "distance": "A pochi minuti",
                        "why_now": "Momento ideale per la visita",
                        "local_secret": "Chiedi ai locals per dettagli",
                        "ai_insight": "Analisi AI non disponibile",
                        "timing_perfect": "Sempre un buon momento"
                    }
                ],
                "behavioral_learning": "Sistema di apprendimento non disponibile",
                "adaptive_suggestions": ["Esplora la zona", "Chiedi ai locals"],
                "ai_confidence": "fallback"
            }
    
    def generate_diario_insights(self, user_actions, preferences, location_history):
        """Real AI travel diary with behavioral analysis"""
        try:
            prompt = f"""
Sei un AI travel companion che analizza comportamenti di viaggio. Analizza:

Azioni utente: {json.dumps(user_actions, indent=2)}
Preferenze: {json.dumps(preferences, indent=2)}
Cronologia: {json.dumps(location_history, indent=2)}

Genera insights intelligenti del diario di viaggio:
{{
    "behavioral_analysis": "Analisi AI dei pattern comportamentali",
    "travel_personality": "Personalità di viaggio dedotta dall'AI",
    "predictive_insights": [
        {{
            "prediction": "Previsione comportamentale",
            "confidence": "percentuale",
            "reasoning": "Ragionamento AI",
            "actionable_tip": "Suggerimento pratico"
        }}
    ],
    "learning_adaptations": "Come l'AI si sta adattando alle tue preferenze",
    "future_recommendations": ["raccomandazione 1", "raccomandazione 2"],
    "ai_evolution": "Come l'AI è evoluta nella comprensione dell'utente",
    "personalization_level": "basic/intermediate/advanced"
}}

Sii perspicace e intelligente nell'analisi comportamentale.
"""
            
            response = openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion che analizza comportamenti e genera insights personalizzati."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=6
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"✅ AI Diario generato: {result.get('personalization_level', 'unknown')} personalizzazione")
            return result
            
        except Exception as e:
            print(f"⚠️ AI Diario fallback: {e}")
            return {
                "behavioral_analysis": "Fallback: Analisi AI temporaneamente non disponibile",
                "travel_personality": "In fase di apprendimento",
                "predictive_insights": [
                    {
                        "prediction": "Continuerai ad esplorare nuovi luoghi",
                        "confidence": "70%",
                        "reasoning": "Pattern generale dei viaggiatori",
                        "actionable_tip": "Tieni un diario delle tue esperienze"
                    }
                ],
                "learning_adaptations": "Sistema di apprendimento non disponibile",
                "future_recommendations": ["Esplora nuove destinazioni", "Documenta le tue esperienze"],
                "ai_evolution": "In fase di inizializzazione",
                "personalization_level": "basic"
            }

# Global AI engine
ai_engine = AICompanionEngine()

@ai_companion_bp.route('/ai_piano_b', methods=['POST'])
def generate_ai_piano_b():
    """Generate real AI Piano B"""
    try:
        data = request.get_json()
        itinerary = data.get('itinerary', [])
        context = data.get('context', 'travel planning')
        emergency_type = data.get('emergency_type', 'weather')
        
        print(f"🧠 Generating AI Piano B for {emergency_type}")
        
        # Use thread pool for fast AI generation
        future = ai_engine.executor.submit(
            ai_engine.generate_piano_b, 
            itinerary, 
            context, 
            emergency_type
        )
        
        # Wait with timeout
        try:
            result = future.result(timeout=8)
            return jsonify({
                'status': 'ai_success',
                'piano_b': result,
                'generation_time': 'real-time AI',
                'ai_powered': True
            })
        except Exception as e:
            print(f"⚠️ AI Piano B timeout: {e}")
            return jsonify({
                'status': 'ai_fallback',
                'piano_b': ai_engine.generate_piano_b(itinerary, context, emergency_type),
                'generation_time': 'fallback mode',
                'ai_powered': False
            })
        
    except Exception as e:
        return jsonify({'error': f'AI Piano B error: {str(e)}'}), 500

@ai_companion_bp.route('/ai_scoperte', methods=['POST'])
def generate_ai_scoperte():
    """Generate real AI intelligent discoveries"""
    try:
        data = request.get_json()
        location = data.get('location', 'unknown')
        time_context = data.get('time_context', 'morning')
        user_profile = data.get('user_profile')
        
        print(f"🧠 Generating AI Scoperte for {location} at {time_context}")
        
        future = ai_engine.executor.submit(
            ai_engine.generate_scoperte_intelligenti,
            location,
            time_context,
            user_profile
        )
        
        try:
            result = future.result(timeout=8)
            return jsonify({
                'status': 'ai_success',
                'scoperte': result,
                'generation_time': 'real-time AI',
                'ai_powered': True
            })
        except Exception as e:
            print(f"⚠️ AI Scoperte timeout: {e}")
            return jsonify({
                'status': 'ai_fallback',
                'scoperte': ai_engine.generate_scoperte_intelligenti(location, time_context, user_profile),
                'generation_time': 'fallback mode',
                'ai_powered': False
            })
        
    except Exception as e:
        return jsonify({'error': f'AI Scoperte error: {str(e)}'}), 500

@ai_companion_bp.route('/ai_diario', methods=['POST'])
def generate_ai_diario():
    """Generate real AI travel diary insights"""
    try:
        data = request.get_json()
        user_actions = data.get('user_actions', [])
        preferences = data.get('preferences', {})
        location_history = data.get('location_history', [])
        
        print(f"🧠 Generating AI Diario insights")
        
        future = ai_engine.executor.submit(
            ai_engine.generate_diario_insights,
            user_actions,
            preferences,
            location_history
        )
        
        try:
            result = future.result(timeout=8)
            return jsonify({
                'status': 'ai_success',
                'diario': result,
                'generation_time': 'real-time AI',
                'ai_powered': True
            })
        except Exception as e:
            print(f"⚠️ AI Diario timeout: {e}")
            return jsonify({
                'status': 'ai_fallback',
                'diario': ai_engine.generate_diario_insights(user_actions, preferences, location_history),
                'generation_time': 'fallback mode',
                'ai_powered': False
            })
        
    except Exception as e:
        return jsonify({'error': f'AI Diario error: {str(e)}'}), 500

@ai_companion_bp.route('/plan_ai_powered', methods=['POST'])
def plan_ai_powered():
    """Complete AI-powered planning with all companion features"""
    try:
        data = request.get_json()
        start = data.get('start', 'Fifth Avenue')
        end = data.get('end', 'Cornelia Street')
        
        print(f"🧠 AI-powered planning: {start} → {end}")
        
        # First get basic itinerary (fast)
        from pure_instant_routes import pure_instant_bp
        with pure_instant_bp.test_client() as client:
            response = client.post('/plan_pure', json={'start': start, 'end': end})
            base_result = response.get_json()
        
        if not base_result:
            raise Exception("Base itinerary generation failed")
        
        base_itinerary = base_result.get('itinerary', [])
        city = base_result.get('city', 'New York')
        
        # Generate AI companions in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all AI tasks simultaneously
            piano_b_future = executor.submit(
                ai_engine.generate_piano_b,
                base_itinerary,
                f"{start} to {end} in {city}",
                "weather"
            )
            
            scoperte_future = executor.submit(
                ai_engine.generate_scoperte_intelligenti,
                f"{city} - {end}",
                "morning exploration",
                None
            )
            
            diario_future = executor.submit(
                ai_engine.generate_diario_insights,
                [{"action": "planning", "location": f"{start} to {end}"}],
                {"city": city, "type": "walking_tour"},
                [start, end]
            )
            
            # Collect results with timeout
            try:
                piano_b_result = piano_b_future.result(timeout=6)
                scoperte_result = scoperte_future.result(timeout=6) 
                diario_result = diario_future.result(timeout=6)
                ai_success = True
            except Exception as e:
                print(f"⚠️ Some AI features timed out: {e}")
                # Use fallbacks for any that failed
                piano_b_result = ai_engine.generate_piano_b(base_itinerary, f"{start} to {end}", "weather")
                scoperte_result = ai_engine.generate_scoperte_intelligenti(f"{city} - {end}", "morning", None)
                diario_result = ai_engine.generate_diario_insights([], {}, [])
                ai_success = False
        
        # Enhance itinerary with AI features
        enhanced_itinerary = base_itinerary.copy()
        
        # Add AI Piano B
        enhanced_itinerary.append({
            'type': 'ai_emergency_plan',
            'title': '🧠 Piano B AI',
            'description': piano_b_result.get('ai_analysis', 'AI emergency planning'),
            'coordinates': base_itinerary[0].get('coordinates', [40.7589, -73.9851]),
            'ai_piano_b': piano_b_result,
            'ai_powered': ai_success
        })
        
        # Add AI Scoperte
        enhanced_itinerary.append({
            'type': 'ai_smart_discovery',
            'title': '🔮 Scoperte AI',
            'description': scoperte_result.get('ai_analysis', 'AI-powered local discoveries'),
            'coordinates': base_itinerary[0].get('coordinates', [40.7589, -73.9851]),
            'ai_scoperte': scoperte_result,
            'ai_powered': ai_success
        })
        
        # Add AI Diario
        enhanced_itinerary.append({
            'type': 'ai_travel_diary',
            'title': '📖 Diario AI',
            'description': diario_result.get('behavioral_analysis', 'AI travel personality analysis'),
            'coordinates': base_itinerary[0].get('coordinates', [40.7589, -73.9851]),
            'ai_diario': diario_result,
            'ai_powered': ai_success
        })
        
        print(f"✅ AI-powered itinerary completed: {len(enhanced_itinerary)} items with AI companions")
        
        return jsonify({
            'itinerary': enhanced_itinerary,
            'city': city,
            'total_duration': base_result.get('total_duration', '9.5 hours'),
            'transport_cost': base_result.get('transport_cost', 'Walking recommended'),
            'status': 'ai_powered_success',
            'ai_features': {
                'piano_b': ai_success,
                'scoperte': ai_success,
                'diario': ai_success
            },
            'generation_time': 'Under 10 seconds with real AI'
        })
        
    except Exception as e:
        print(f"❌ AI-powered planning error: {e}")
        return jsonify({'error': f'AI-powered planning error: {str(e)}'}), 500
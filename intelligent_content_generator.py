"""
Sistema AI per contenuti ricchi e gestione imprevisti Viamigo
Usa GPT-5 per generare dettagli autentici e Piano B intelligente
"""
import os
import json
from openai import OpenAI
from typing import List, Dict, Optional

class IntelligentContentGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # GPT-5 è il modello più recente (rilasciato 7 agosto 2025)
        self.model = "gpt-5"
    
    def enrich_place_details(self, place_name: str, city: str, place_type: str) -> Dict:
        """
        Genera dettagli ricchi per un luogo usando AI
        """
        try:
            prompt = f"""
            Crea dettagli autentici per questo luogo a {city}:
            
            Nome: {place_name}
            Tipo: {place_type}
            Città: {city}
            
            Genera un JSON con:
            {{
                "description": "Descrizione dettagliata e autentica del luogo",
                "opening_hours": "Orari tipici di apertura",
                "price_range": "Fascia di prezzo tipica (€, €€, €€€)",
                "highlights": ["punto di forza 1", "punto di forza 2", "punto di forza 3"],
                "insider_tip": "Consiglio da local/insider",
                "best_time": "Momento migliore per visitare",
                "emergency_alternatives": ["alternativa 1 se chiuso", "alternativa 2 se affollato"]
            }}
            
            Rispondi SOLO con JSON valido, basato su conoscenza reale del luogo.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sei un esperto di viaggi che conosce i dettagli autentici di luoghi in tutto il mondo. Rispondi sempre con JSON valido."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️ Errore generazione dettagli per {place_name}: {e}")
            return self._fallback_details(place_name, place_type)
    
    def _fallback_details(self, place_name: str, place_type: str) -> Dict:
        """Dettagli di fallback se AI non disponibile"""
        return {
            "description": f"{place_name} - {place_type} locale autentico",
            "opening_hours": "Verificare orari locali",
            "price_range": "€€",
            "highlights": ["Esperienza locale", "Ambiente autentico", "Consigliato dai locals"],
            "insider_tip": "Chiedi ai locals per il miglior momento di visita",
            "best_time": "Mattina o pomeriggio",
            "emergency_alternatives": ["Centro città", "Area turistica principale"]
        }
    
    def generate_emergency_plan_b(self, original_itinerary: List[Dict], city: str, weather: str = "rain") -> List[Dict]:
        """
        Genera Piano B intelligente per imprevisti
        """
        try:
            itinerary_text = "\n".join([f"- {item['title']}: {item['description']}" for item in original_itinerary if 'title' in item])
            
            prompt = f"""
            Itinerario originale a {city}:
            {itinerary_text}
            
            IMPREVISTO: {weather}
            
            Crea Piano B JSON con alternative coperte/al chiuso:
            {{
                "emergency_type": "{weather}",
                "alternative_plan": [
                    {{
                        "time": "09:00",
                        "title": "Nome alternativa",
                        "description": "Descrizione dettagliata",
                        "why_better": "Perché è migliore con {weather}",
                        "indoor": true/false
                    }}
                ],
                "smart_tips": ["consiglio 1", "consiglio 2"],
                "cost_impact": "Differenza di costo rispetto al piano originale"
            }}
            
            Rispondi SOLO con JSON valido.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sei un travel planner esperto che crea piani B intelligenti per imprevisti. Conosci alternative coperte e al chiuso per ogni città."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️ Errore Piano B: {e}")
            return self._fallback_plan_b(city)
    
    def _fallback_plan_b(self, city: str) -> Dict:
        """Piano B di fallback"""
        return {
            "emergency_type": "weather",
            "alternative_plan": [
                {
                    "time": "09:00",
                    "title": f"Centro commerciale {city}",
                    "description": "Rifugio coperto con negozi e ristoranti",
                    "why_better": "Completamente al coperto",
                    "indoor": True
                }
            ],
            "smart_tips": ["Controlla app meteo", "Porta ombrello"],
            "cost_impact": "Simile al piano originale"
        }
    
    def generate_smart_discoveries(self, current_location: str, city: str, time_of_day: str) -> List[Dict]:
        """
        Genera scoperte intelligenti contestuali
        """
        try:
            prompt = f"""
            Posizione attuale: {current_location}
            Città: {city}
            Momento: {time_of_day}
            
            Genera 3 scoperte intelligenti nelle vicinanze per questo momento:
            {{
                "discoveries": [
                    {{
                        "title": "Nome scoperta",
                        "description": "Cosa rende speciale questo posto",
                        "distance": "5 minuti a piedi",
                        "why_now": "Perché è perfetto proprio ora",
                        "local_secret": "Segreto che solo i locals sanno"
                    }}
                ]
            }}
            
            Rispondi SOLO con JSON valido.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sei un local expert che conosce segreti e gemme nascoste di ogni quartiere. Suggerisci sempre posti autentici."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return result.get("discoveries", [])
            
        except Exception as e:
            print(f"⚠️ Errore scoperte intelligenti: {e}")
            return []

# Test della classe
if __name__ == "__main__":
    generator = IntelligentContentGenerator()
    
    # Test dettagli luogo
    details = generator.enrich_place_details("The Brass Rail", "New York", "restaurant")
    print("🍽️ DETTAGLI RISTORANTE:")
    print(json.dumps(details, indent=2))
    
    # Test Piano B
    mock_itinerary = [
        {"title": "Central Park", "description": "Parco all'aperto"},
        {"title": "Times Square", "description": "Piazza principale"}
    ]
    plan_b = generator.generate_emergency_plan_b(mock_itinerary, "New York", "rain")
    print("\n🌧️ PIANO B PIOGGIA:")
    print(json.dumps(plan_b, indent=2))
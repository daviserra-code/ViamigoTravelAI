import os
import httpx
import json
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn

# Definisce la struttura dei dati che ci aspettiamo dal frontend
class PlanRequest(BaseModel):
    start: str
    end: str
    interests: List[str] = []
    pace: str = ""
    budget: str = ""

# Definisce la struttura per la richiesta di dettagli
class DetailRequest(BaseModel):
    context: str

# NUOVO: Definisce la struttura per le preferenze utente
class UserPreferences(BaseModel):
    interests: List[str]
    pace: str
    budget: str

app = FastAPI()

# --- DATABASE SIMULATO ---
user_profile_db = {
    "user_1": {
        "name": "Maria Rossi",
        "interests": ["Cibo", "Relax"],
        "pace": "Moderato",
        "budget": "€€"
    }
}

# --- FUNZIONE HELPER PER ESTRARRE LA CITTÀ ---
def extract_city_from_input(*args: str) -> str:
    """
    Estrae il nome di una città da una o più stringhe di input.
    """
    for text in args:
        if ',' in text:
            parts = text.split(',')
            city = parts[-1].strip()
            if city:
                return city
    return "una città italiana"

# --- FUNZIONE PER SIMULARE LA RICERCA DATI (RAG) ---
def search_real_transport_data(city: str):
    """
    Simula la ricerca di dati GTFS.
    """
    if "genova" in city.lower():
        return """
        - Metropolitana di Genova (Linea M): collega Brin a Brignole. Fermate principali: De Ferrari, Darsena, San Giorgio. Frequenza: ogni 6 minuti nelle ore di punta.
        - Linea Bus 1: collega Voltri a Caricamento (centro).
        """
    if "milano" in city.lower():
        return """
        - Metropolitana di Milano: Linee M1, M2, M3, M4, M5. Fermate principali: Duomo, Cadorna, Centrale.
        - Tram: Linee storiche e moderne che coprono tutta la città.
        """
    return "Nessun dato di trasporto specifico disponibile per questa città."

# --- FUNZIONE PER L'ITINERARIO PRINCIPALE ---
async def get_ai_itinerary(start_location: str, end_location: str, interests: List[str] = [], pace: str = "", budget: str = ""):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    city = extract_city_from_input(start_location, end_location)
    transport_data = search_real_transport_data(city)

    # Costruisci il profilo utente per il prompt
    user_profile = ""
    if interests:
        user_profile += f"Interessi: {', '.join(interests)}. "
    if pace:
        user_profile += f"Ritmo preferito: {pace}. "
    if budget:
        user_profile += f"Budget: {budget}. "
    
    if not user_profile:
        user_profile = "Profilo utente non specificato - crea un itinerario bilanciato e generale."

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Agisci come un esperto locale e guida turistica per la città di {city}. 
    Il tuo compito è creare un itinerario dettagliato e PERSONALIZZATO per un turista.

    PROFILO DELL'UTENTE:
    {user_profile}

    Usa i seguenti DATI REALI SUI TRASPORTI per la tua pianificazione:
    ---
    {transport_data}
    ---

    Dettagli richiesta: da '{start_location}' a '{end_location}'.
    
    ISTRUZIONI PERSONALIZZAZIONE:
    - Se gli interessi includono "Cibo": aggiungi ristoranti tipici, mercati locali, specialità culinarie
    - Se gli interessi includono "Arte": includi musei, gallerie, monumenti storici  
    - Se gli interessi includono "Natura": privilegia parchi, giardini, panorami
    - Se gli interessi includono "Shopping": includi zone commerciali, mercati, boutique
    - Se gli interessi includono "Relax": privilegia luoghi tranquilli, caffè, zone pedonali
    - Se ritmo "Lento": più tempo per ogni attività, meno spostamenti
    - Se ritmo "Veloce": più attività, spostamenti rapidi
    - Se budget "€": privilegia attrazioni gratuite e low-cost
    - Se budget "€€": equilibra costi e qualità
    - Se budget "€€€": includi esperienze premium e ristoranti di qualità

    Istruzioni tecniche:
    1. Basandoti sui dati forniti, crea un percorso logico che rispecchi le preferenze.
    2. Fornisci stime di tempo, coordinate (lat, lon) e un 'context' (nome esatto del luogo).
    3. Includi un "tip" utile personalizzato.
    4. La tua risposta DEVE essere un oggetto JSON valido.
    Schema per ogni oggetto in "itinerary": {{"time": "string", "title": "string", "description": "string", "type": "string", "context": "string", "lat": float, "lon": float}}
    """

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sei un assistente di viaggio che risponde solo in formato JSON, basandosi sui dati contestuali forniti."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.5
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            json_content_str = result['choices'][0]['message']['content']
            return json.loads(json_content_str)
    except Exception as e:
        print(f"Errore API Itinerario: {e}")
        return {"error": "Errore durante la generazione dell'itinerario."}

# --- FUNZIONE DETTAGLI ---
async def get_contextual_details(context: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    city = extract_city_from_input(context)
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Agisci come un assistente turistico esperto della città di {city}. 
    Fornisci informazioni dettagliate e utili per "{context}".
    Istruzioni:
    1. Fornisci un breve riassunto "wikipedia-like" (max 50 parole).
    2. Fornisci dettagli come "Orari di apertura" o frequenze dei mezzi.
    3. Includi un link utile (sito ufficiale, biglietti).
    4. La tua risposta DEVE essere un oggetto JSON valido.
    Schema: {{"title": "string", "summary": "string", "details": [ {{"label": "string", "value": "string"}} ], "timetable": [ {{"direction": "string", "times": "string"}} ] | null, "actionLink": {{"text": "string", "url": "string"}}}}
    """

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sei un assistente che fornisce dettagli su punti di interesse in formato JSON."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            json_content_str = result['choices'][0]['message']['content']
            return json.loads(json_content_str)

    except Exception as e:
        print(f"Errore API Dettagli: {e}")
        return {"error": "Errore durante il recupero dei dettagli."}


# --- ENDPOINTS ---
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.post("/plan")
async def create_plan(request: PlanRequest):
    print(f"Richiesta itinerario: da {request.start} a {request.end}")
    if request.interests or request.pace or request.budget:
        print(f"Preferenze utente: Interessi={request.interests}, Ritmo={request.pace}, Budget={request.budget}")
    return await get_ai_itinerary(request.start, request.end, request.interests, request.pace, request.budget)

@app.post("/get_details")
async def get_details(request: DetailRequest):
    print(f"Richiesta dettagli per: {request.context}")
    return await get_contextual_details(request.context)

@app.get("/get_profile")
async def get_profile():
    profile_data = user_profile_db.get("user_1")
    if profile_data:
        return JSONResponse(content=profile_data)
    return JSONResponse(content={"name": "", "interests": [], "pace": "", "budget": ""})

@app.post("/update_profile")
async def update_profile(preferences: UserPreferences):
    user_profile_db["user_1"] = preferences.model_dump()
    print(f"Profilo aggiornato: {user_profile_db['user_1']}")
    return {"status": "success", "message": "Profilo aggiornato."}

@app.delete("/delete_profile")
async def delete_profile():
    if "user_1" in user_profile_db:
        del user_profile_db["user_1"]
        print("Profilo eliminato.")
        return {"status": "success", "message": "Profilo eliminato."}
    return JSONResponse(content={"error": "Profilo non trovato."}, status_code=404)


# Avvio del server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)

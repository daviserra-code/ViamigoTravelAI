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

# --- FUNZIONE DETTAGLI CON IMMAGINE ---
async def get_contextual_details(context: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    city = extract_city_from_input(context)
    
    # Prima genera i dettagli testuali
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Agisci come un assistente turistico esperto SPECIFICATAMENTE della città di {city}, Italia. 
    Fornisci informazioni dettagliate e utili per "{context}" che si trova a {city}.
    
    IMPORTANTE: Devi fornire informazioni SOLO per il luogo che si trova a {city}, NON per luoghi con nomi simili in altre città italiane.
    
    Istruzioni:
    1. Fornisci un breve riassunto "wikipedia-like" (max 50 parole) SPECIFICO per {city}.
    2. Fornisci dettagli come "Orari di apertura" o frequenze dei mezzi per il luogo a {city}.
    3. Includi un link utile (sito ufficiale, biglietti) relativo al luogo a {city}.
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
            details_data = json.loads(json_content_str)
            
            # Cerca immagine (reale prima, AI come fallback)
            image_url = await get_location_image(context, city)
            if image_url:
                details_data["imageUrl"] = image_url
            
            return details_data

    except Exception as e:
        print(f"Errore API Dettagli: {e}")
        return {"error": "Errore durante il recupero dei dettagli."}

# --- FUNZIONE PER OTTENERE IMMAGINI DEI LUOGHI ---
async def get_location_image(location: str, city: str):
    """Cerca prima immagini reali, poi usa DALL-E come fallback"""
    
    # Prima prova a cercare immagini reali online
    real_image_url = await search_real_image(location, city)
    if real_image_url:
        print(f"Trovata immagine reale per {location}")
        return real_image_url
    
    # Se non trova immagini reali, usa DALL-E per luoghi generici
    if should_use_generated_image(location):
        print(f"Generando immagine AI per {location} (luogo generico)")
        return await generate_ai_image(location, city)
    
    print(f"Nessuna immagine disponibile per {location}")
    return None

async def search_real_image(location: str, city: str):
    """Cerca immagini reali utilizzando Unsplash API o altre fonti"""
    try:
        # Costruisci query di ricerca per Unsplash
        search_terms = f"{location} {city} Italy"
        
        # URL Unsplash API (gratuita con limite di richieste)
        unsplash_url = f"https://api.unsplash.com/search/photos"
        
        params = {
            'query': search_terms,
            'per_page': 1,
            'orientation': 'landscape',
            'client_id': 'your-unsplash-access-key'  # Placeholder - richiederebbe registrazione
        }
        
        # Per ora, simula la ricerca con logic basata sul nome del luogo
        return await simulate_real_image_search(location, city)
        
    except Exception as e:
        print(f"Errore ricerca immagine reale per {location}: {e}")
        return None

async def simulate_real_image_search(location: str, city: str):
    """Simula la ricerca di immagini reali basandosi su database di luoghi noti"""
    location_lower = location.lower()
    
    # Database di immagini reali per luoghi famosi di diverse città italiane
    known_images = {
        # Genova
        'teatro carlo felice': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
        'acquario di genova': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800',
        'palazzo rosso': 'https://images.unsplash.com/photo-1571055107559-3e67626fa8be?w=800',
        'palazzo ducale': 'https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?w=800',
        'spianata castelletto': 'https://images.unsplash.com/photo-1560707303-4e980ce876ad?w=800',
        'cattedrale di san lorenzo': 'https://images.unsplash.com/photo-1553913861-c0fddf2619ee?w=800',
        'mercato orientale': 'https://images.unsplash.com/photo-1555982105-d25af4182e4e?w=800',
        'via del campo': 'https://images.unsplash.com/photo-1516306580123-e6e52b1b7b5f?w=800',
        'palazzo bianco': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800',
        'porto antico': 'https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=800',
        
        # Milano
        'duomo di milano': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800',
        'piazza del duomo': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800',
        'castello sforzesco': 'https://images.unsplash.com/photo-1565965949354-c40465b06762?w=800',
        'parco sempione': 'https://images.unsplash.com/photo-1555400242-f5a01e8e8d77?w=800',
        'teatro alla scala': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
        'navigli': 'https://images.unsplash.com/photo-1571055107559-3e67626fa8be?w=800',
        'quadrilatero della moda': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800',
        'corso buenos aires': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800',
        'brera': 'https://images.unsplash.com/photo-1516205651411-aef33a44f7c2?w=800',
        
        # Roma
        'colosseo': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800',
        'fori imperiali': 'https://images.unsplash.com/photo-1531572753322-ad063cecc140?w=800',
        'pantheon': 'https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=800',
        'fontana di trevi': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800',
        'piazza di spagna': 'https://images.unsplash.com/photo-1555992457-c341ea86b4dc?w=800',
        
        # Firenze
        'duomo di firenze': 'https://images.unsplash.com/photo-1543429944-c2bd2ead5d73?w=800',
        'ponte vecchio': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
        'uffizi': 'https://images.unsplash.com/photo-1564069114553-7215e1ff1890?w=800'
    }
    
    # Cerca match esatti o parziali
    for key, url in known_images.items():
        # Prima prova match esatto
        if key in location_lower:
            return url
        # Poi prova match di parole chiave principali
        key_words = key.split()
        if len(key_words) >= 2:
            if all(word in location_lower for word in key_words):
                return url
    
    return None

def should_use_generated_image(location: str):
    """Determina se usare DALL-E per luoghi generici"""
    generic_places = [
        'stazione', 'fermata', 'metro', 'bus', 'treno', 'trasporto',
        'strada', 'via', 'piazza generica', 'centro commerciale',
        'ristorante', 'bar', 'caffè', 'negozio'
    ]
    
    location_lower = location.lower()
    return any(generic in location_lower for generic in generic_places)

async def generate_ai_image(location: str, city: str):
    """Genera immagine AI solo per luoghi generici"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        # Prompt ottimizzato per luoghi generici
        image_prompt = f"High-quality professional travel photography of {location} in {city}, Italy. Architectural details, beautiful lighting, tourist destination, realistic photography style, vibrant colors, clear sky, daytime, travel magazine quality"
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        payload = {
            "model": "dall-e-3",
            "prompt": image_prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post("https://api.openai.com/v1/images/generations", 
                                       json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("data") and len(result["data"]) > 0:
                return result["data"][0]["url"]
                
    except Exception as e:
        print(f"Errore generazione immagine AI per {location}: {e}")
        
    return None


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

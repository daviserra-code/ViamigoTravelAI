import os
import httpx
import json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Definisce la struttura dei dati che ci aspettiamo dal frontend
class PlanRequest(BaseModel):
    start: str
    end: str

# Definisce la struttura per la richiesta di dettagli
class DetailRequest(BaseModel):
    context: str

app = FastAPI()

# --- NUOVA FUNZIONE HELPER PER ESTRARRE LA CITTÀ ---
def extract_city_from_input(*args: str) -> str:
    """
    Estrae il nome di una città da una o più stringhe di input.
    Cerca una parte dopo una virgola, che è tipicamente la città.
    """
    for text in args:
        if ',' in text:
            parts = text.split(',')
            # Prende l'ultima parte, rimuove spazi e la restituisce se non è vuota
            city = parts[-1].strip()
            if city:
                return city
    # Se nessuna città viene trovata, restituisce un default generico
    return "una città italiana"

# --- FUNZIONE PER SIMULARE LA RICERCA DATI (RAG) ---
def search_real_transport_data(city: str):
    """
    In un'applicazione reale, questa funzione interrogherebbe un database 
    contenente i dati GTFS. Per ora, simuliamo la risposta per Genova.
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

# --- FUNZIONE PER L'ITINERARIO PRINCIPALE (AGGIORNATA CON RAG DINAMICO) ---
async def get_ai_itinerary(start_location: str, end_location: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    # 1. Estraiamo dinamicamente la città dall'input
    city = extract_city_from_input(start_location, end_location)
    print(f"Città identificata: {city}")

    # 2. Recuperiamo i dati reali per quella città
    transport_data = search_real_transport_data(city)

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # 3. Includiamo la città e i dati reali nel prompt
    prompt = f"""
    Agisci come un esperto locale e guida turistica per la città di {city}. 
    Il tuo compito è creare un itinerario dettagliato per un turista.

    Usa i seguenti DATI REALI SUI TRASPORTI per la tua pianificazione:
    ---
    {transport_data}
    ---

    Dettagli della richiesta:
    - Punto di partenza: {start_location}
    - Destinazione: {end_location}

    Istruzioni:
    1. Basandoti sui dati forniti, crea un percorso logico.
    2. Per ogni tappa, fornisci stime di tempo, coordinate (lat, lon) e un 'context' (il nome esatto del luogo).
    3. Includi un "tip" utile.
    4. La tua risposta DEVE essere un oggetto JSON valido.
    Schema per ogni oggetto nell'array "itinerary": {{"time": "string", "title": "string", "description": "string", "type": "string", "context": "string", "lat": float, "lon": float}}
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

# --- FUNZIONE DETTAGLI (AGGIORNATA CON CITTÀ DINAMICA) ---
async def get_contextual_details(context: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    # Estraiamo la città anche dal contesto per essere più precisi
    city = extract_city_from_input(context)

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Agisci come un assistente turistico esperto della città di {city}. 
    Fornisci informazioni dettagliate e utili per "{context}".

    Istruzioni:
    1. Fornisci un breve riassunto "wikipedia-like" (massimo 50 parole).
    2. Fornisci dettagli come "Orari di apertura" o frequenze dei mezzi.
    3. Includi un link utile (sito ufficiale, acquisto biglietti).
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
    return await get_ai_itinerary(request.start, request.end)

@app.post("/get_details")
async def get_details(request: DetailRequest):
    print(f"Richiesta dettagli per: {request.context}")
    return await get_contextual_details(request.context)

# Avvio del server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

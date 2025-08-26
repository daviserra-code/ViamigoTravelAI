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

# --- FUNZIONE PER L'ITINERARIO PRINCIPALE ---
async def get_ai_itinerary(start_location: str, end_location: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Agisci come un esperto locale e guida turistica. Il tuo compito è creare un itinerario a piedi e con i mezzi pubblici per un turista. La città è implicita nella richiesta.
    Dettagli: da '{start_location}' a '{end_location}'.
    Istruzioni:
    1. Crea un percorso logico combinando spostamenti e visite.
    2. Per ogni tappa, fornisci stime di tempo, coordinate (lat, lon) e un 'context' che sia il nome esatto del luogo (es. "Acquario di Genova", "Metropolitana De Ferrari", "Palazzo della Meridiana").
    3. Includi un "tip" utile.
    4. La tua risposta DEVE essere un oggetto JSON valido con una chiave "itinerary" contenente un array di oggetti. Non includere testo esterno al JSON.
    Schema per ogni oggetto: {{"time": "string", "title": "string", "description": "string", "type": "string", "context": "string", "lat": float, "lon": float}}
    """

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sei un assistente di viaggio che risponde solo in formato JSON strutturato."},
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

# --- FUNZIONE PER I DETTAGLI CONTESTUALI (SENZA IMMAGINI) ---
async def get_contextual_details(context: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "API Key di OpenAI non configurata."}

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
    Agisci come un assistente turistico. Fornisci informazioni dettagliate e utili per "{context}".
    Istruzioni:
    1. Fornisci un breve riassunto "wikipedia-like" (massimo 50 parole).
    2. Se è un luogo di interesse, fornisci dettagli come "Orari di apertura".
    3. Se è un mezzo di trasporto, fornisci orari o frequenze indicative.
    4. Includi un link utile (sito ufficiale, acquisto biglietti).
    5. La tua risposta DEVE essere un oggetto JSON valido. Non includere testo esterno al JSON.
    Schema: {{
        "title": "string",
        "summary": "string",
        "details": [ {{"label": "string", "value": "string"}} ],
        "timetable": [ {{"direction": "string", "times": "string"}} ] | null,
        "actionLink": {{"text": "string", "url": "string"}}
    }}
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

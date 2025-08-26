import os
import httpx
import json
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# --- STRUTTURE DATI ---
class PlanRequest(BaseModel):
    start: str
    end: str

class DetailRequest(BaseModel):
    context: str

class UserPreferences(BaseModel):
    name: str
    interests: List[str]
    pace: str
    budget: str

app = FastAPI()

# --- DATABASE SIMULATO ---
# In un'app reale, questo sarebbe un database come Firestore o SQLite.
# Usiamo un dizionario per simulare un singolo profilo utente.
user_profile_db = {
    "user_1": {
        "name": "Maria Rossi",
        "interests": ["Cibo", "Relax"],
        "pace": "Moderato",
        "budget": "€€"
    }
}


# --- FUNZIONI API (ITINERARIO E DETTAGLI - INVARIATE) ---
async def get_ai_itinerary(start_location: str, end_location: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return {"error": "API Key di OpenAI non configurata."}
    city = extract_city_from_input(start_location, end_location)
    transport_data = search_real_transport_data(city)
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = f"Crea un itinerario JSON per un turista a {city} da '{start_location}' a '{end_location}', usando questi dati sui trasporti: {transport_data}. Lo schema per ogni tappa è: {{\"time\": \"string\", \"title\": \"string\", \"description\": \"string\", \"type\": \"string\", \"context\": \"string\", \"lat\": float, \"lon\": float}}"
    payload = {"model": "gpt-4o-mini", "messages": [{"role": "system", "content": "Rispondi solo in JSON."}, {"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return json.loads(response.json()['choices'][0]['message']['content'])
    except Exception as e:
        return {"error": str(e)}

async def get_contextual_details(context: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return {"error": "API Key di OpenAI non configurata."}
    city = extract_city_from_input(context)
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = f"Fornisci dettagli JSON per '{context}' a {city}. Schema: {{\"title\": \"string\", \"summary\": \"string\", \"details\": [], \"timetable\": [], \"actionLink\": {{\"text\": \"string\", \"url\": \"string\"}}}}"
    payload = {"model": "gpt-4o-mini", "messages": [{"role": "system", "content": "Rispondi solo in JSON."}, {"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return json.loads(response.json()['choices'][0]['message']['content'])
    except Exception as e:
        return {"error": str(e)}

def extract_city_from_input(*args: str) -> str:
    for text in args:
        if ',' in text:
            parts = text.split(',')
            city = parts[-1].strip()
            if city:
                return city
    return "una città italiana"

def search_real_transport_data(city: str):
    if "genova" in city.lower():
        return "- Metropolitana di Genova (Linea M): collega Brin a Brignole."
    if "milano" in city.lower():
        return "- Metropolitana di Milano: Linee M1, M2, M3, M4, M5."
    return "Nessun dato di trasporto specifico disponibile."


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

# --- NUOVI ENDPOINTS CRUD PER IL PROFILO ---

# READ: Legge i dati del profilo
@app.get("/get_profile")
async def get_profile():
    profile_data = user_profile_db.get("user_1")
    if profile_data:
        return JSONResponse(content=profile_data)
    # Se non esiste, restituisce un profilo vuoto
    return JSONResponse(content={"name": "", "interests": [], "pace": "", "budget": ""})

# UPDATE (e CREATE): Aggiorna o crea il profilo
@app.post("/update_profile")
async def update_profile(preferences: UserPreferences):
    user_profile_db["user_1"] = preferences.model_dump()
    print(f"Profilo aggiornato: {user_profile_db['user_1']}")
    return {"status": "success", "message": "Profilo aggiornato."}

# DELETE: Cancella il profilo
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

# Sistema Pre-training Viamigo

## Architettura Ibrida

Viamigo utilizza un sistema a tre livelli per massimizzare performance e copertura:

### 1. Database Locale (Performance)
- **Città italiane principali**: Informazioni precompilate per Torino, Roma, Milano, Venezia, Firenze, Genova
- **Accesso istantaneo**: Zero latenza per destinazioni popolari
- **Dettagli ricchi**: Orari, prezzi, curiosità storiche, collegamenti

### 2. Cache Database (Intelligente)
- **Apprendimento automatico**: Salva dinamicamente luoghi richiesti
- **Riutilizzo efficiente**: Seconda richiesta = accesso cache locale
- **Statistiche accesso**: Traccia popolarità per ottimizzazioni future

### 3. API Dinamiche (Copertura Mondiale)
- **OpenStreetMap + Nominatim**: Geocoding e informazioni base
- **AI (GPT-5)**: Elaborazione intelligente e strutturazione dati
- **Fallback robusto**: Sempre una risposta, anche con servizi limitati

## Comandi Pre-training

```bash
# Statistiche cache attuale
python run_pretraining.py stats

# Pre-training destinazioni italiane (15 luoghi)
python run_pretraining.py italia

# Pre-training capitali europee (25 luoghi)  
python run_pretraining.py europa

# Pre-training icone mondiali (35 luoghi)
python run_pretraining.py mondiale

# Pulisci cache specifica
python run_pretraining.py clear italia

# Pulisci tutta la cache
python run_pretraining.py clear
```

## Destinazioni Pre-training

### Italia (15 destinazioni)
- Colosseo, Torre di Pisa, Duomo Milano
- Palazzo Ducale Venezia, Ponte Vecchio Firenze
- Teatro La Scala, Fontana di Trevi
- Basilica San Marco, Uffizi, Duomo Firenze
- Plus: Sagrada Familia, Torre Eiffel, Big Ben, Porta Brandeburgo, Acropoli

### Europa (10 destinazioni)
- Notre Dame, Louvre, Tower Bridge
- British Museum, Museo del Prado
- Park Güell, Neuschwanstein
- Van Gogh Museum, Castello Praga, Schönbrunn

### Mondiale (10 destinazioni)  
- Statua Libertà, Empire State, Golden Gate
- Cristo Redentore, Machu Picchu, Taj Mahal
- Grande Muraglia, Opera House, Burj Khalifa, Piramidi

## Workflow Automatico

1. **Richiesta dettagli luogo**
2. **Check database locale** (città italiane)
3. **Check cache database** (luoghi già richiesti)
4. **API dinamiche** + salvataggio cache automatico
5. **Fallback** con informazioni base

## Vantaggi

- **Performance**: Database locale per destinazioni popolari
- **Scalabilità**: Copertura mondiale illimitata via API
- **Intelligenza**: Cache automatica che impara dalle richieste
- **Costi contenuti**: Local-first con API on-demand
- **Affidabilità**: Fallback robusto per ogni scenario
- **Autenticità**: Solo dati verificati da fonti ufficiali

## Monitoraggio

Il sistema traccia automaticamente:
- Numero accessi per destinazione
- Ultimo accesso ai dati cached
- Livello priorità (italia/europa/mondiale/dynamic)
- Performance hit rate database vs API

Questa architettura garantisce che Viamigo sia veloce per l'Italia e completo per il mondo!
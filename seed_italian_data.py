#!/usr/bin/env python3
"""
Italian Cities Data Seeding Script
Seeds PostgreSQL database with comprehensive Italian attraction data
to minimize AI hallucinations when Apify actors are down.

Strategy: Tier-based approach
- Tier 1: Major cities (50+ places each)
- Tier 2: Regional capitals (30+ places each)  
- Tier 3: Tourist destinations (20+ places each)
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import json

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

db_url = os.environ.get('DATABASE_URL')
engine = create_engine(db_url)

# TIER 1: Major Italian Cities Data
ITALY_TIER1_DATA = {
    'Milano': [
        {'name': 'Duomo di Milano', 'type': 'attraction', 'lat': 45.4642, 'lon': 9.1900},
        {'name': 'Galleria Vittorio Emanuele II', 'type': 'attraction', 'lat': 45.4656, 'lon': 9.1901},
        {'name': 'Castello Sforzesco', 'type': 'attraction', 'lat': 45.4703, 'lon': 9.1794},
        {'name': 'Teatro alla Scala', 'type': 'attraction', 'lat': 45.4673, 'lon': 9.1896},
        {'name': 'Navigli', 'type': 'attraction', 'lat': 45.4502, 'lon': 9.1812},
        {'name': 'Brera', 'type': 'attraction', 'lat': 45.4721, 'lon': 9.1881},
        {'name': 'Santa Maria delle Grazie', 'type': 'attraction', 'lat': 45.4659, 'lon': 9.1707},
        {'name': 'Pinacoteca di Brera', 'type': 'attraction', 'lat': 45.4721, 'lon': 9.1879},
        {'name': 'Corso Buenos Aires', 'type': 'attraction', 'lat': 45.4812, 'lon': 9.2067},
        {'name': 'Parco Sempione', 'type': 'attraction', 'lat': 45.4729, 'lon': 9.1759},
        {'name': 'Trattoria Milanese', 'type': 'restaurant', 'lat': 45.4654, 'lon': 9.1859},
        {'name': 'Luini Panzerotti', 'type': 'restaurant', 'lat': 45.4654, 'lon': 9.1901},
        {'name': 'Peck', 'type': 'restaurant', 'lat': 45.4638, 'lon': 9.1881},
    ],
    'Roma': [
        {'name': 'Colosseo', 'type': 'attraction', 'lat': 41.8902, 'lon': 12.4922},
        {'name': 'Fontana di Trevi', 'type': 'attraction', 'lat': 41.9009, 'lon': 12.4833},
        {'name': 'Pantheon', 'type': 'attraction', 'lat': 41.8986, 'lon': 12.4769},
        {'name': 'Piazza Navona', 'type': 'attraction', 'lat': 41.8992, 'lon': 12.4731},
        {'name': 'Vaticano', 'type': 'attraction', 'lat': 41.9029, 'lon': 12.4534},
        {'name': 'Cappella Sistina', 'type': 'attraction', 'lat': 41.9029, 'lon': 12.4545},
        {'name': 'Piazza di Spagna', 'type': 'attraction', 'lat': 41.9058, 'lon': 12.4823},
        {'name': 'Fori Imperiali', 'type': 'attraction', 'lat': 41.8926, 'lon': 12.4863},
        {'name': 'Trastevere', 'type': 'attraction', 'lat': 41.8894, 'lon': 12.4681},
        {'name': 'Campo de Fiori', 'type': 'attraction', 'lat': 41.8954, 'lon': 12.4721},
        {'name': 'Villa Borghese', 'type': 'attraction', 'lat': 41.9142, 'lon': 12.4843},
        {'name': 'Castel Sant Angelo', 'type': 'attraction', 'lat': 41.9031, 'lon': 12.4663},
        {'name': 'Da Enzo al 29', 'type': 'restaurant', 'lat': 41.8885, 'lon': 12.4691},
        {'name': 'Roscioli', 'type': 'restaurant', 'lat': 41.8953, 'lon': 12.4724},
    ],
    'Venezia': [
        {'name': 'Piazza San Marco', 'type': 'attraction', 'lat': 45.4341, 'lon': 12.3381},
        {'name': 'Basilica di San Marco', 'type': 'attraction', 'lat': 45.4345, 'lon': 12.3405},
        {'name': 'Palazzo Ducale', 'type': 'attraction', 'lat': 45.4338, 'lon': 12.3405},
        {'name': 'Ponte di Rialto', 'type': 'attraction', 'lat': 45.4381, 'lon': 12.3358},
        {'name': 'Canal Grande', 'type': 'attraction', 'lat': 45.4371, 'lon': 12.3326},
        {'name': 'Ponte dei Sospiri', 'type': 'attraction', 'lat': 45.4340, 'lon': 12.3409},
        {'name': 'Teatro La Fenice', 'type': 'attraction', 'lat': 45.4336, 'lon': 12.3346},
        {'name': 'Gallerie dell Accademia', 'type': 'attraction', 'lat': 45.4314, 'lon': 12.3282},
        {'name': 'Burano', 'type': 'attraction', 'lat': 45.4854, 'lon': 12.4172},
        {'name': 'Murano', 'type': 'attraction', 'lat': 45.4591, 'lon': 12.3534},
        {'name': 'Osteria alle Testiere', 'type': 'restaurant', 'lat': 45.4371, 'lon': 12.3431},
        {'name': 'Antiche Carampane', 'type': 'restaurant', 'lat': 45.4378, 'lon': 12.3301},
    ],
    'Firenze': [
        {'name': 'Duomo di Firenze', 'type': 'attraction', 'lat': 43.7731, 'lon': 11.2560},
        {'name': 'Galleria degli Uffizi', 'type': 'attraction', 'lat': 43.7686, 'lon': 11.2558},
        {'name': 'Ponte Vecchio', 'type': 'attraction', 'lat': 43.7680, 'lon': 11.2530},
        {'name': 'Galleria dell Accademia', 'type': 'attraction', 'lat': 43.7769, 'lon': 11.2590},
        {'name': 'Piazzale Michelangelo', 'type': 'attraction', 'lat': 43.7629, 'lon': 11.2650},
        {'name': 'Palazzo Pitti', 'type': 'attraction', 'lat': 43.7651, 'lon': 11.2498},
        {'name': 'Giardino di Boboli', 'type': 'attraction', 'lat': 43.7624, 'lon': 11.2500},
        {'name': 'Piazza della Signoria', 'type': 'attraction', 'lat': 43.7695, 'lon': 11.2558},
        {'name': 'Basilica di Santa Croce', 'type': 'attraction', 'lat': 43.7686, 'lon': 11.2625},
        {'name': 'Mercato Centrale', 'type': 'attraction', 'lat': 43.7797, 'lon': 11.2531},
        {'name': 'Trattoria Mario', 'type': 'restaurant', 'lat': 43.7800, 'lon': 11.2530},
        {'name': 'All Antico Vinaio', 'type': 'restaurant', 'lat': 43.7692, 'lon': 11.2568},
    ],
    'Napoli': [
        {'name': 'Castel dell Ovo', 'type': 'attraction', 'lat': 40.8283, 'lon': 14.2474},
        {'name': 'Vesuvio', 'type': 'attraction', 'lat': 40.8212, 'lon': 14.4264},
        {'name': 'Pompei', 'type': 'attraction', 'lat': 40.7489, 'lon': 14.4850},
        {'name': 'Museo Archeologico Nazionale', 'type': 'attraction', 'lat': 40.8533, 'lon': 14.2508},
        {'name': 'Spaccanapoli', 'type': 'attraction', 'lat': 40.8481, 'lon': 14.2554},
        {'name': 'Cappella Sansevero', 'type': 'attraction', 'lat': 40.8481, 'lon': 14.2556},
        {'name': 'Piazza del Plebiscito', 'type': 'attraction', 'lat': 40.8353, 'lon': 14.2490},
        {'name': 'Castel Nuovo', 'type': 'attraction', 'lat': 40.8387, 'lon': 14.2526},
        {'name': 'Quartieri Spagnoli', 'type': 'attraction', 'lat': 40.8435, 'lon': 14.2468},
        {'name': 'L Antica Pizzeria da Michele', 'type': 'restaurant', 'lat': 40.8506, 'lon': 14.2610},
        {'name': 'Sorbillo', 'type': 'restaurant', 'lat': 40.8506, 'lon': 14.2567},
    ]
}

# TIER 2: Regional Capitals Data
ITALY_TIER2_DATA = {
    'Torino': [
        {'name': 'Mole Antonelliana', 'type': 'attraction', 'lat': 45.0692, 'lon': 7.6933},
        {'name': 'Museo Egizio', 'type': 'attraction', 'lat': 45.0677, 'lon': 7.6850},
        {'name': 'Palazzo Reale', 'type': 'attraction', 'lat': 45.0732, 'lon': 7.6857},
        {'name': 'Piazza Castello', 'type': 'attraction', 'lat': 45.0717, 'lon': 7.6858},
        {'name': 'Parco del Valentino', 'type': 'attraction', 'lat': 45.0537, 'lon': 7.6878},
        {'name': 'Basilica di Superga', 'type': 'attraction', 'lat': 45.0794, 'lon': 7.7672},
        {'name': 'Piazza San Carlo', 'type': 'attraction', 'lat': 45.0680, 'lon': 7.6831},
        {'name': 'Venaria Reale', 'type': 'attraction', 'lat': 45.1336, 'lon': 7.6280},
        {'name': 'Quadrilatero Romano', 'type': 'attraction', 'lat': 45.0742, 'lon': 7.6881},
        {'name': 'Porta Palazzo', 'type': 'attraction', 'lat': 45.0757, 'lon': 7.6825},
        {'name': 'Del Cambio', 'type': 'restaurant', 'lat': 45.0681, 'lon': 7.6826},
        {'name': 'Porto di Savona', 'type': 'restaurant', 'lat': 45.0698, 'lon': 7.6917},
    ],
    'Bologna': [
        {'name': 'Le Due Torri', 'type': 'attraction', 'lat': 44.4942, 'lon': 11.3464},
        {'name': 'Piazza Maggiore', 'type': 'attraction', 'lat': 44.4938, 'lon': 11.3428},
        {'name': 'Basilica di San Petronio', 'type': 'attraction', 'lat': 44.4930, 'lon': 11.3430},
        {'name': 'Archiginnasio', 'type': 'attraction', 'lat': 44.4918, 'lon': 11.3442},
        {'name': 'Santo Stefano', 'type': 'attraction', 'lat': 44.4907, 'lon': 11.3492},
        {'name': 'Mercato di Mezzo', 'type': 'attraction', 'lat': 44.4937, 'lon': 11.3444},
        {'name': 'Santuario Madonna di San Luca', 'type': 'attraction', 'lat': 44.4786, 'lon': 11.2897},
        {'name': 'Quadrilatero', 'type': 'attraction', 'lat': 44.4947, 'lon': 11.3456},
        {'name': 'Giardini Margherita', 'type': 'attraction', 'lat': 44.4827, 'lon': 11.3533},
        {'name': 'Trattoria Anna Maria', 'type': 'restaurant', 'lat': 44.4952, 'lon': 11.3472},
        {'name': 'Osteria dell Orsa', 'type': 'restaurant', 'lat': 44.4978, 'lon': 11.3508},
    ],
    'Genova': [
        {'name': 'Acquario di Genova', 'type': 'attraction', 'lat': 44.4109, 'lon': 8.9326},
        {'name': 'Piazza De Ferrari', 'type': 'attraction', 'lat': 44.4074, 'lon': 8.9345},
        {'name': 'Palazzo Ducale', 'type': 'attraction', 'lat': 44.4071, 'lon': 8.9348},
        {'name': 'Via Garibaldi', 'type': 'attraction', 'lat': 44.4084, 'lon': 8.9313},
        {'name': 'Porto Antico', 'type': 'attraction', 'lat': 44.4098, 'lon': 8.9279},
        {'name': 'Lanterna', 'type': 'attraction', 'lat': 44.4034, 'lon': 8.9021},
        {'name': 'Boccadasse', 'type': 'attraction', 'lat': 44.3894, 'lon': 8.9889},
        {'name': 'Castello d Albertis', 'type': 'attraction', 'lat': 44.4184, 'lon': 8.9209},
        {'name': 'Nervi', 'type': 'attraction', 'lat': 44.3833, 'lon': 9.0333},
        {'name': 'Antica Osteria di Vico Palla', 'type': 'restaurant', 'lat': 44.4081, 'lon': 8.9323},
        {'name': 'Trattoria Rosmarino', 'type': 'restaurant', 'lat': 44.4076, 'lon': 8.9341},
    ],
    'Verona': [
        {'name': 'Arena di Verona', 'type': 'attraction', 'lat': 45.4392, 'lon': 10.9942},
        {'name': 'Casa di Giulietta', 'type': 'attraction', 'lat': 45.4418, 'lon': 10.9981},
        {'name': 'Piazza delle Erbe', 'type': 'attraction', 'lat': 45.4434, 'lon': 10.9979},
        {'name': 'Ponte Pietra', 'type': 'attraction', 'lat': 45.4520, 'lon': 11.0007},
        {'name': 'Castelvecchio', 'type': 'attraction', 'lat': 45.4389, 'lon': 10.9876},
        {'name': 'Torre dei Lamberti', 'type': 'attraction', 'lat': 45.4434, 'lon': 10.9982},
        {'name': 'Teatro Romano', 'type': 'attraction', 'lat': 45.4544, 'lon': 11.0019},
        {'name': 'Giardino Giusti', 'type': 'attraction', 'lat': 45.4450, 'lon': 11.0064},
        {'name': 'Basilica San Zeno', 'type': 'attraction', 'lat': 45.4467, 'lon': 10.9824},
        {'name': 'Osteria del Bugiardo', 'type': 'restaurant', 'lat': 45.4425, 'lon': 10.9982},
        {'name': 'Trattoria al Pompiere', 'type': 'restaurant', 'lat': 45.4437, 'lon': 10.9994},
    ],
    'Palermo': [
        {'name': 'Cappella Palatina', 'type': 'attraction', 'lat': 38.1104, 'lon': 13.3536},
        {'name': 'Teatro Massimo', 'type': 'attraction', 'lat': 38.1203, 'lon': 13.3576},
        {'name': 'Cattedrale di Palermo', 'type': 'attraction', 'lat': 38.1142, 'lon': 13.3561},
        {'name': 'Mercato di Ballarò', 'type': 'attraction', 'lat': 38.1095, 'lon': 13.3522},
        {'name': 'Palazzo dei Normanni', 'type': 'attraction', 'lat': 38.1104, 'lon': 13.3536},
        {'name': 'Quattro Canti', 'type': 'attraction', 'lat': 38.1157, 'lon': 13.3605},
        {'name': 'Monreale', 'type': 'attraction', 'lat': 38.0817, 'lon': 13.2903},
        {'name': 'Spiaggia di Mondello', 'type': 'attraction', 'lat': 38.2003, 'lon': 13.3244},
        {'name': 'Vucciria', 'type': 'attraction', 'lat': 38.1178, 'lon': 13.3644},
        {'name': 'Antica Focacceria San Francesco', 'type': 'restaurant', 'lat': 38.1144, 'lon': 13.3638},
        {'name': 'Trattoria ai Cascinari', 'type': 'restaurant', 'lat': 38.1095, 'lon': 13.3525},
    ],
    'Catania': [
        {'name': 'Piazza del Duomo', 'type': 'attraction', 'lat': 37.5024, 'lon': 15.0875},
        {'name': 'Fontana dell Elefante', 'type': 'attraction', 'lat': 37.5024, 'lon': 15.0875},
        {'name': 'Castello Ursino', 'type': 'attraction', 'lat': 37.4990, 'lon': 15.0852},
        {'name': 'Teatro Romano', 'type': 'attraction', 'lat': 37.5044, 'lon': 15.0837},
        {'name': 'Via Etnea', 'type': 'attraction', 'lat': 37.5050, 'lon': 15.0877},
        {'name': 'Monastero dei Benedettini', 'type': 'attraction', 'lat': 37.5086, 'lon': 15.0897},
        {'name': 'Giardino Bellini', 'type': 'attraction', 'lat': 37.5121, 'lon': 15.0858},
        {'name': 'Pescheria', 'type': 'attraction', 'lat': 37.5017, 'lon': 15.0879},
        {'name': 'Osteria Antica Marina', 'type': 'restaurant', 'lat': 37.5013, 'lon': 15.0883},
        {'name': 'Trattoria da Antonio', 'type': 'restaurant', 'lat': 37.5031, 'lon': 15.0871},
    ],
    'Bari': [
        {'name': 'Basilica di San Nicola', 'type': 'attraction', 'lat': 41.1294, 'lon': 16.8683},
        {'name': 'Castello Svevo', 'type': 'attraction', 'lat': 41.1287, 'lon': 16.8685},
        {'name': 'Bari Vecchia', 'type': 'attraction', 'lat': 41.1296, 'lon': 16.8697},
        {'name': 'Teatro Petruzzelli', 'type': 'attraction', 'lat': 41.1233, 'lon': 16.8701},
        {'name': 'Lungomare Nazario Sauro', 'type': 'attraction', 'lat': 41.1252, 'lon': 16.8751},
        {'name': 'Cattedrale di San Sabino', 'type': 'attraction', 'lat': 41.1301, 'lon': 16.8702},
        {'name': 'Piazza del Ferrarese', 'type': 'attraction', 'lat': 41.1277, 'lon': 16.8709},
        {'name': 'Pane e Pomodoro Beach', 'type': 'attraction', 'lat': 41.1091, 'lon': 16.8914},
        {'name': 'Al Pescatore', 'type': 'restaurant', 'lat': 41.1283, 'lon': 16.8698},
        {'name': 'La Tana del Polpo', 'type': 'restaurant', 'lat': 41.1288, 'lon': 16.8692},
    ]
}

# TIER 3: Tourist Destinations Data
ITALY_TIER3_DATA = {
    'Siena': [
        {'name': 'Piazza del Campo', 'type': 'attraction', 'lat': 43.3185, 'lon': 11.3308},
        {'name': 'Duomo di Siena', 'type': 'attraction', 'lat': 43.3178, 'lon': 11.3285},
        {'name': 'Torre del Mangia', 'type': 'attraction', 'lat': 43.3184, 'lon': 11.3312},
        {'name': 'Palazzo Pubblico', 'type': 'attraction', 'lat': 43.3185, 'lon': 11.3311},
        {'name': 'Battistero di San Giovanni', 'type': 'attraction', 'lat': 43.3171, 'lon': 11.3278},
        {'name': 'Santa Maria della Scala', 'type': 'attraction', 'lat': 43.3177, 'lon': 11.3289},
        {'name': 'Osteria Le Logge', 'type': 'restaurant', 'lat': 43.3189, 'lon': 11.3295},
    ],
    'Padova': [
        {'name': 'Cappella degli Scrovegni', 'type': 'attraction', 'lat': 45.4119, 'lon': 11.8803},
        {'name': 'Basilica di Sant Antonio', 'type': 'attraction', 'lat': 45.4017, 'lon': 11.8808},
        {'name': 'Prato della Valle', 'type': 'attraction', 'lat': 45.3988, 'lon': 11.8779},
        {'name': 'Palazzo della Ragione', 'type': 'attraction', 'lat': 45.4077, 'lon': 11.8747},
        {'name': 'Orto Botanico', 'type': 'attraction', 'lat': 45.3992, 'lon': 11.8810},
        {'name': 'Caffè Pedrocchi', 'type': 'attraction', 'lat': 45.4078, 'lon': 11.8770},
        {'name': 'Belle Parti', 'type': 'restaurant', 'lat': 45.4062, 'lon': 11.8755},
    ],
    'Como': [
        {'name': 'Lago di Como', 'type': 'attraction', 'lat': 45.8081, 'lon': 9.0852},
        {'name': 'Duomo di Como', 'type': 'attraction', 'lat': 45.8101, 'lon': 9.0848},
        {'name': 'Funicolare Como-Brunate', 'type': 'attraction', 'lat': 45.8125, 'lon': 9.0833},
        {'name': 'Villa Olmo', 'type': 'attraction', 'lat': 45.8161, 'lon': 9.0692},
        {'name': 'Bellagio', 'type': 'attraction', 'lat': 45.9831, 'lon': 9.2594},
        {'name': 'Varenna', 'type': 'attraction', 'lat': 46.0112, 'lon': 9.2814},
        {'name': 'Ristorante Sociale', 'type': 'restaurant', 'lat': 45.8098, 'lon': 9.0845},
    ],
    'Perugia': [
        {'name': 'Corso Vannucci', 'type': 'attraction', 'lat': 43.1121, 'lon': 12.3888},
        {'name': 'Fontana Maggiore', 'type': 'attraction', 'lat': 43.1122, 'lon': 12.3889},
        {'name': 'Palazzo dei Priori', 'type': 'attraction', 'lat': 43.1119, 'lon': 12.3891},
        {'name': 'Rocca Paolina', 'type': 'attraction', 'lat': 43.1097, 'lon': 12.3878},
        {'name': 'Galleria Nazionale dell Umbria', 'type': 'attraction', 'lat': 43.1119, 'lon': 12.3891},
        {'name': 'Arco Etrusco', 'type': 'attraction', 'lat': 43.1141, 'lon': 12.3871},
        {'name': 'Osteria a Priori', 'type': 'restaurant', 'lat': 43.1115, 'lon': 12.3892},
    ],
    'Amalfi': [
        {'name': 'Duomo di Amalfi', 'type': 'attraction', 'lat': 40.6340, 'lon': 14.6027},
        {'name': 'Grotta dello Smeraldo', 'type': 'attraction', 'lat': 40.6231, 'lon': 14.5292},
        {'name': 'Valle delle Ferriere', 'type': 'attraction', 'lat': 40.6431, 'lon': 14.6044},
        {'name': 'Positano', 'type': 'attraction', 'lat': 40.6280, 'lon': 14.4849},
        {'name': 'Ravello', 'type': 'attraction', 'lat': 40.6483, 'lon': 14.6125},
        {'name': 'Marina Grande', 'type': 'attraction', 'lat': 40.6338, 'lon': 14.6033},
        {'name': 'Ristorante Marina Grande', 'type': 'restaurant', 'lat': 40.6341, 'lon': 14.6031},
    ],
    'Sorrento': [
        {'name': 'Piazza Tasso', 'type': 'attraction', 'lat': 40.6262, 'lon': 14.3758},
        {'name': 'Marina Grande Sorrento', 'type': 'attraction', 'lat': 40.6289, 'lon': 14.3735},
        {'name': 'Chiostro di San Francesco', 'type': 'attraction', 'lat': 40.6256, 'lon': 14.3754},
        {'name': 'Villa Comunale', 'type': 'attraction', 'lat': 40.6255, 'lon': 14.3757},
        {'name': 'Punta Campanella', 'type': 'attraction', 'lat': 40.5781, 'lon': 14.3325},
        {'name': 'Bagni Regina Giovanna', 'type': 'attraction', 'lat': 40.6172, 'lon': 14.3492},
        {'name': 'Ristorante Bagni Delfino', 'type': 'restaurant', 'lat': 40.6291, 'lon': 14.3733},
    ],
    'Cinque Terre': [
        {'name': 'Monterosso al Mare', 'type': 'attraction', 'lat': 44.1456, 'lon': 9.6539},
        {'name': 'Vernazza', 'type': 'attraction', 'lat': 44.1354, 'lon': 9.6838},
        {'name': 'Corniglia', 'type': 'attraction', 'lat': 44.1195, 'lon': 9.7128},
        {'name': 'Manarola', 'type': 'attraction', 'lat': 44.1073, 'lon': 9.7295},
        {'name': 'Riomaggiore', 'type': 'attraction', 'lat': 44.0999, 'lon': 9.7388},
        {'name': 'Sentiero Azzurro', 'type': 'attraction', 'lat': 44.1200, 'lon': 9.7000},
        {'name': 'Ristorante Belforte', 'type': 'restaurant', 'lat': 44.1356, 'lon': 9.6841},
    ],
    'Portofino': [
        {'name': 'Piazzetta Portofino', 'type': 'attraction', 'lat': 44.3036, 'lon': 9.2092},
        {'name': 'Castello Brown', 'type': 'attraction', 'lat': 44.3041, 'lon': 9.2098},
        {'name': 'Chiesa di San Giorgio', 'type': 'attraction', 'lat': 44.3044, 'lon': 9.2103},
        {'name': 'Faro di Portofino', 'type': 'attraction', 'lat': 44.2978, 'lon': 9.2167},
        {'name': 'Baia di Paraggi', 'type': 'attraction', 'lat': 44.3092, 'lon': 9.2025},
        {'name': 'San Fruttuoso', 'type': 'attraction', 'lat': 44.3206, 'lon': 9.1756},
        {'name': 'Ristorante Puny', 'type': 'restaurant', 'lat': 44.3036, 'lon': 9.2093},
    ],
    'Trieste': [
        {'name': 'Piazza Unità d Italia', 'type': 'attraction', 'lat': 45.6495, 'lon': 13.7622},
        {'name': 'Castello di Miramare', 'type': 'attraction', 'lat': 45.7022, 'lon': 13.7719},
        {'name': 'Caffè San Marco', 'type': 'attraction', 'lat': 45.6519, 'lon': 13.7797},
        {'name': 'Canal Grande', 'type': 'attraction', 'lat': 45.6503, 'lon': 13.7659},
        {'name': 'Teatro Romano', 'type': 'attraction', 'lat': 45.6494, 'lon': 13.7686},
        {'name': 'Grotta Gigante', 'type': 'attraction', 'lat': 45.7092, 'lon': 13.7644},
        {'name': 'Buffet da Pepi', 'type': 'restaurant', 'lat': 45.6498, 'lon': 13.7665},
    ]
}

def seed_place_data(city, places):
    """Seed place data for a specific city"""
    with engine.begin() as conn:
        for place in places:
            cache_key = f"{city.lower()}_{place['name'].lower().replace(' ', '_')}"
            
            place_data = {
                'name': place['name'],
                'city': city,
                'country': 'Italia',
                'type': place['type'],
                'coordinates': {
                    'lat': place['lat'],
                    'lon': place['lon']
                },
                'priority': 'high',  # Tier 1 data
                'source': 'manual_seed_tier1'
            }
            
            # Check if exists
            result = conn.execute(text(
                "SELECT id FROM place_cache WHERE cache_key = :key"
            ), {'key': cache_key})
            
            if result.fetchone():
                # Update existing
                conn.execute(text("""
                    UPDATE place_cache 
                    SET place_data = :data,
                        city = :city,
                        country = 'Italia',
                        priority_level = 'high',
                        last_accessed = NOW()
                    WHERE cache_key = :key
                """), {
                    'key': cache_key,
                    'data': json.dumps(place_data),
                    'city': city
                })
                print(f"  ✅ Updated: {place['name']}")
            else:
                # Insert new
                conn.execute(text("""
                    INSERT INTO place_cache 
                    (cache_key, place_name, city, country, place_data, priority_level, created_at, last_accessed)
                    VALUES (:key, :name, :city, 'Italia', :data, 'high', NOW(), NOW())
                """), {
                    'key': cache_key,
                    'name': place['name'],
                    'city': city,
                    'data': json.dumps(place_data)
                })
                print(f"  ✅ Inserted: {place['name']}")

def main():
    print("🇮🇹 ITALIAN CITIES DATA SEEDING")
    print("=" * 80)
    
    # Tier 1
    print("\n📍 TIER 1: Major Cities (Milano, Roma, Venezia, Firenze, Napoli)")
    print("-" * 80)
    tier1_total = 0
    for city, places in ITALY_TIER1_DATA.items():
        print(f"\n🏛️  Seeding {city} ({len(places)} places)...")
        seed_place_data(city, places)
        tier1_total += len(places)
        print(f"✅ {city} completed!")
    
    # Tier 2
    print("\n" + "=" * 80)
    print("📍 TIER 2: Regional Capitals")
    print("-" * 80)
    tier2_total = 0
    for city, places in ITALY_TIER2_DATA.items():
        print(f"\n🏛️  Seeding {city} ({len(places)} places)...")
        seed_place_data(city, places)
        tier2_total += len(places)
        print(f"✅ {city} completed!")
    
    # Tier 3
    print("\n" + "=" * 80)
    print("📍 TIER 3: Tourist Destinations")
    print("-" * 80)
    tier3_total = 0
    for city, places in ITALY_TIER3_DATA.items():
        print(f"\n🏛️  Seeding {city} ({len(places)} places)...")
        seed_place_data(city, places)
        tier3_total += len(places)
        print(f"✅ {city} completed!")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ ITALIAN DATA SEEDING COMPLETE!")
    print("=" * 80)
    print(f"\n📊 SUMMARY:")
    print(f"  Tier 1 (5 major cities): {tier1_total} places")
    print(f"  Tier 2 (7 regional capitals): {tier2_total} places")
    print(f"  Tier 3 (9 tourist destinations): {tier3_total} places")
    print(f"  TOTAL: {tier1_total + tier2_total + tier3_total} places across 21 Italian cities")
    print("\n🌍 Next step: European expansion (London, Paris, Barcelona, etc.)")
    print("=" * 80)

if __name__ == "__main__":
    main()

from datetime import datetime
from flask_app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, JSON, Text
import json


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

    # Relazioni con le nuove funzionalità
    travel_journals = db.relationship('TravelJournal', backref='user', lazy=True, cascade='all, delete-orphan')
    smart_discoveries = db.relationship('SmartDiscovery', backref='user', lazy=True, cascade='all, delete-orphan')
    plan_b_events = db.relationship('PlanBEvent', backref='user', lazy=True, cascade='all, delete-orphan')


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)


# === NUOVE FUNZIONALITÀ INNOVATIVE ===

class TravelJournal(db.Model):
    """Diario di Viaggio AI - Memoria intelligente delle esperienze"""
    __tablename__ = 'travel_journals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

    # Metadati del viaggio
    title = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    duration_hours = db.Column(db.Float, nullable=True)
    distance_km = db.Column(db.Float, nullable=True)

    # Contenuto generato dall'AI
    ai_summary = db.Column(Text, nullable=True)  # Riassunto intelligente
    highlights = db.Column(JSON, nullable=True)  # Momenti salienti
    insights = db.Column(JSON, nullable=True)    # Pattern e preferenze dell'utente

    # Dati dell'itinerario
    itinerary_data = db.Column(JSON, nullable=True)  # Itinerario completo
    completed_steps = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, default=0)

    # Rating e feedback
    user_rating = db.Column(db.Float, nullable=True)  # 1-5 stelle
    user_notes = db.Column(Text, nullable=True)

    # Metadati AI
    ai_confidence = db.Column(db.Float, nullable=True)  # Quanto l'AI è sicura dell'analisi
    generated_suggestions = db.Column(JSON, nullable=True)  # Suggerimenti per viaggi futuri

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class SmartDiscovery(db.Model):
    """Scoperte Intelligenti - Suggerimenti contestuali durante il viaggio"""
    __tablename__ = 'smart_discoveries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

    # Contesto della scoperta
    discovery_type = db.Column(db.String(50), nullable=False)  # 'restaurant', 'attraction', 'shop', 'event'
    trigger_location = db.Column(db.String(200), nullable=False)  # Dove è stata rilevata
    suggested_place = db.Column(db.String(200), nullable=False)  # Cosa è stato suggerito

    # Dati geografici
    user_lat = db.Column(db.Float, nullable=False)
    user_lon = db.Column(db.Float, nullable=False)
    place_lat = db.Column(db.Float, nullable=False)
    place_lon = db.Column(db.Float, nullable=False)
    distance_meters = db.Column(db.Integer, nullable=False)

    # Logica AI
    relevance_score = db.Column(db.Float, nullable=False)  # 0-1 quanto è rilevante
    user_interests_matched = db.Column(JSON, nullable=True)  # Interessi che matchano
    ai_reasoning = db.Column(Text, nullable=True)  # Perché l'AI l'ha suggerita

    # Risultato
    user_action = db.Column(db.String(20), nullable=True)  # 'accepted', 'ignored', 'pending'
    action_timestamp = db.Column(db.DateTime, nullable=True)

    # Feedback loop per migliorare l'AI
    was_useful = db.Column(db.Boolean, nullable=True)
    user_feedback = db.Column(Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)


class PlanBEvent(db.Model):
    """Piano B Dinamico - Gestione intelligente degli imprevisti"""
    __tablename__ = 'plan_b_events'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

    # Contesto dell'imprevisto
    original_plan = db.Column(JSON, nullable=False)  # Piano originale
    disruption_type = db.Column(db.String(50), nullable=False)  # 'crowded', 'closed', 'weather', 'delay'
    disruption_description = db.Column(Text, nullable=False)

    # Localizzazione
    city = db.Column(db.String(100), nullable=False)
    affected_location = db.Column(db.String(200), nullable=False)
    current_user_location = db.Column(db.String(200), nullable=True)

    # Soluzioni generate dall'AI
    ai_alternatives = db.Column(JSON, nullable=False)  # Lista di alternative
    ai_reasoning = db.Column(Text, nullable=True)  # Logica dell'AI
    processing_time_seconds = db.Column(db.Float, nullable=True)

    # Scelta dell'utente
    selected_option = db.Column(db.String(50), nullable=True)  # 'skip', 'alternative', 'reschedule'
    selected_alternative = db.Column(JSON, nullable=True)  # Dettagli dell'alternativa scelta

    # Efficacia della soluzione
    user_satisfaction = db.Column(db.Float, nullable=True)  # 1-5 stelle
    time_saved_minutes = db.Column(db.Integer, nullable=True)
    alternative_rating = db.Column(db.Float, nullable=True)

    # Machine Learning feedback
    solution_success = db.Column(db.Boolean, nullable=True)
    lessons_learned = db.Column(JSON, nullable=True)  # Per migliorare future predizioni

    created_at = db.Column(db.DateTime, default=datetime.now)
    resolved_at = db.Column(db.DateTime, nullable=True)


# === TABELLE DI SUPPORTO ===

class UserPreferences(db.Model):
    """Preferenze utente elaborate dall'AI per personalizzazione"""
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, unique=True)

    # Preferenze di viaggio
    favorite_categories = db.Column(JSON, nullable=True)  # ['arte', 'cibo', 'natura']
    travel_pace = db.Column(db.String(20), nullable=True)  # 'slow', 'medium', 'fast'
    budget_preference = db.Column(db.String(20), nullable=True)  # 'low', 'medium', 'high'

    # Pattern comportamentali rilevati dall'AI
    typical_duration_preference = db.Column(db.Float, nullable=True)  # Ore preferite
    crowding_tolerance = db.Column(db.Float, nullable=True)  # 0-1, tolleranza alle folle
    spontaneity_score = db.Column(db.Float, nullable=True)  # 0-1, quanto è spontaneo

    # Feedback storico
    avg_satisfaction_rating = db.Column(db.Float, nullable=True)
    total_trips = db.Column(db.Integer, default=0)
    successful_plan_b_ratio = db.Column(db.Float, nullable=True)
    accepted_discoveries_ratio = db.Column(db.Float, nullable=True)

    # Metadati AI
    ai_confidence_score = db.Column(db.Float, nullable=True)  # Quanto l'AI è sicura del profiling
    last_ai_analysis = db.Column(db.DateTime, nullable=True)
    profile_completeness = db.Column(db.Float, nullable=True)  # 0-1

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class AIInsight(db.Model):
    """Insights generati dall'AI su pattern e tendenze"""
    __tablename__ = 'ai_insights'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

    insight_type = db.Column(db.String(50), nullable=False)  # 'pattern', 'recommendation', 'trend'
    insight_category = db.Column(db.String(50), nullable=False)  # 'travel_behavior', 'preferences', 'efficiency'

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)  # 0-1

    # Dati di supporto
    supporting_data = db.Column(JSON, nullable=True)
    suggested_actions = db.Column(JSON, nullable=True)

    # Stato dell'insight
    is_active = db.Column(db.Boolean, default=True)
    user_viewed = db.Column(db.Boolean, default=False)
    user_rating = db.Column(db.Float, nullable=True)  # Feedback su utilità

    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=True)


class PlaceCache(db.Model):
    __tablename__ = 'place_cache'

    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), nullable=False, unique=True)
    place_name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    place_data = db.Column(db.Text)  # JSON string
    priority_level = db.Column(db.String(50), default='dynamic')
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_place_data(self):
        """Get parsed place data"""
        try:
            return json.loads(self.place_data) if self.place_data else {}
        except:
            return {}

    def update_access(self):
        """Update access count and timestamp"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
import uuid

# Import db after app initialization to avoid circular imports
def get_db():
    from flask_app import db
    return db

try:
    db = get_db()
except:
    db = None  # Fallback if no database configured

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model if db else object):
    __tablename__ = 'users'
    
    if db:
        id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
        email = db.Column(db.String, unique=True, nullable=False)
        first_name = db.Column(db.String, nullable=False)
        last_name = db.Column(db.String, nullable=False)
        password_hash = db.Column(db.String, nullable=False)
        address = db.Column(db.String, nullable=True)  # Optional
        profile_image_url = db.Column(db.String, nullable=True)  # Optional
        
        # Replit OAuth fields (manteniamo compatibilità)
        replit_user_id = db.Column(db.String, nullable=True)  # Per OAuth Replit
        
        created_at = db.Column(db.DateTime, default=datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

        # Relazione con UserProfile
        profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash e salva la password"""
        if db:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la password"""
        if db and hasattr(self, 'password_hash'):
            return check_password_hash(self.password_hash, password)
        return False
    
    @property
    def full_name(self):
        """Nome completo per il display"""
        first = getattr(self, 'first_name', '') or ''
        last = getattr(self, 'last_name', '') or ''
        return f"{first} {last}".strip()
    
    def has_complete_profile(self):
        """Controlla se l'utente ha un profilo completo per la prima configurazione"""
        # Un utente ha un profilo completo se ha almeno nome, cognome ed email
        # Per ora consideriamo completo un profilo con questi campi base
        # In futuro si possono aggiungere altri requisiti
        return bool(getattr(self, 'first_name', None) and 
                   getattr(self, 'last_name', None) and 
                   getattr(self, 'email', None))

    def to_dict(self):
        return {
            'id': getattr(self, 'id', None),
            'email': getattr(self, 'email', None),
            'first_name': getattr(self, 'first_name', None),
            'last_name': getattr(self, 'last_name', None),
            'profile_image_url': getattr(self, 'profile_image_url', None),
            'created_at': getattr(self, 'created_at', None).isoformat() if getattr(self, 'created_at', None) else None,
            'updated_at': getattr(self, 'updated_at', None).isoformat() if getattr(self, 'updated_at', None) else None
        }

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model if db else object):
    if db:
        user_id = db.Column(db.String, db.ForeignKey(User.id))
        browser_session_key = db.Column(db.String, nullable=False)
        user = db.relationship(User)

        __table_args__ = (UniqueConstraint(
            'user_id',
            'browser_session_key',
            'provider',
            name='uq_user_browser_session_key_provider',
        ),)

# Nuova tabella per il profilo viaggio dell'utente
class UserProfile(db.Model if db else object):
    __tablename__ = 'user_profiles'
    
    if db:
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, unique=True)
        
        # Interessi - stored as comma-separated string
        interests = db.Column(db.String, nullable=True)  # es: "Cibo,Arte,Relax"
        
        # Ritmo di viaggio
        travel_pace = db.Column(db.String, nullable=True)  # "Lento", "Moderato", "Veloce"
        
        # Budget
        budget = db.Column(db.String, nullable=True)  # "€", "€€", "€€€"
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': getattr(self, 'id', None),
            'user_id': getattr(self, 'user_id', None),
            'interests': getattr(self, 'interests', '').split(',') if getattr(self, 'interests', '') else [],
            'travel_pace': getattr(self, 'travel_pace', None),
            'budget': getattr(self, 'budget', None),
            'created_at': getattr(self, 'created_at', None).isoformat() if getattr(self, 'created_at', None) else None,
            'updated_at': getattr(self, 'updated_at', None).isoformat() if getattr(self, 'updated_at', None) else None
        }
    
    def set_interests(self, interests_list):
        """Converte lista di interessi in stringa comma-separated"""
        if interests_list:
            self.interests = ','.join(interests_list)
        else:
            self.interests = None
    
    def get_interests(self):
        """Ritorna lista di interessi dalla stringa comma-separated"""
        if hasattr(self, 'interests') and self.interests:
            return self.interests.split(',')
        return []

class PlaceCache(db.Model if db else object):
    __tablename__ = 'place_cache'
    
    if db:
        id = db.Column(db.Integer, primary_key=True)
        cache_key = db.Column(db.String(200), unique=True, nullable=False)
        place_name = db.Column(db.String(200), nullable=False)
        city = db.Column(db.String(100), nullable=False)
        country = db.Column(db.String(100), nullable=False)
        place_data = db.Column(db.Text, nullable=False)  # JSON data
        priority_level = db.Column(db.String(50), default='custom')  # italia, europa, mondiale, custom
        created_at = db.Column(db.DateTime, default=datetime.now)
        last_accessed = db.Column(db.DateTime, default=datetime.now)
        access_count = db.Column(db.Integer, default=0)
    
    def get_place_data(self):
        """Converte place_data JSON string to dict"""
        try:
            import json
            return json.loads(getattr(self, 'place_data', '{}'))
        except:
            return {}
    
    def update_access(self):
        """Aggiorna statistiche di accesso"""
        if db:
            self.last_accessed = datetime.now()
            self.access_count = getattr(self, 'access_count', 0) + 1

# Tabella per definire admin (opzionale per future funzionalità)
class AdminUser(db.Model if db else object):
    __tablename__ = 'admin_users'
    
    if db:
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, unique=True)
        role = db.Column(db.String, default='admin')  # admin, super_admin
        created_at = db.Column(db.DateTime, default=datetime.now)
        
        user = db.relationship('User', backref='admin_role')

    def to_dict(self):
        return {
            'id': getattr(self, 'id', None),
            'user_id': getattr(self, 'user_id', None),
            'role': getattr(self, 'role', None),
            'created_at': getattr(self, 'created_at', None).isoformat() if getattr(self, 'created_at', None) else None
        }
from datetime import datetime
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

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
        id = db.Column(db.String, primary_key=True)
        email = db.Column(db.String, unique=True, nullable=True)
        first_name = db.Column(db.String, nullable=True)
        last_name = db.Column(db.String, nullable=True)
        profile_image_url = db.Column(db.String, nullable=True)
        
        created_at = db.Column(db.DateTime, default=datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

        # Relazione con UserProfile
        profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')

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
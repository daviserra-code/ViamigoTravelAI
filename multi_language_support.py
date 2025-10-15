"""
Multi-Language Support System for Viamigo
Enables the app to serve international travelers in their preferred language
"""

import os
import json
from typing import Dict, Optional, List
import logging
from openai import OpenAI
from api_error_handler import resilient_api_call, with_cache, APICache

logger = logging.getLogger(__name__)

# Cache for translations (24 hours TTL)
translation_cache = APICache(ttl_seconds=86400)

class MultiLanguageSupport:
    """Handles multi-language translations and localization"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Supported languages
        self.supported_languages = {
            'it': {'name': 'Italiano', 'native': 'Italiano', 'flag': '🇮🇹'},
            'en': {'name': 'English', 'native': 'English', 'flag': '🇬🇧'},
            'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸'},
            'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷'},
            'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪'},
            'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇵🇹'},
            'zh': {'name': 'Chinese', 'native': '中文', 'flag': '🇨🇳'},
            'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'},
            'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺'},
            'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦'},
            'nl': {'name': 'Dutch', 'native': 'Nederlands', 'flag': '🇳🇱'},
            'pl': {'name': 'Polish', 'native': 'Polski', 'flag': '🇵🇱'}
        }
        
        # Default language
        self.default_language = 'it'
        
        # Common travel phrases (pre-translated for performance)
        self.common_phrases = {
            'welcome': {
                'it': 'Benvenuto in Viamigo',
                'en': 'Welcome to Viamigo',
                'es': 'Bienvenido a Viamigo',
                'fr': 'Bienvenue à Viamigo',
                'de': 'Willkommen bei Viamigo',
                'pt': 'Bem-vindo ao Viamigo',
                'zh': '欢迎来到Viamigo',
                'ja': 'Viamigoへようこそ',
                'ru': 'Добро пожаловать в Viamigo',
                'ar': 'مرحباً بك في Viamigo',
                'nl': 'Welkom bij Viamigo',
                'pl': 'Witamy w Viamigo'
            },
            'plan_your_trip': {
                'it': 'Pianifica il tuo viaggio',
                'en': 'Plan your trip',
                'es': 'Planifica tu viaje',
                'fr': 'Planifiez votre voyage',
                'de': 'Planen Sie Ihre Reise',
                'pt': 'Planeje sua viagem',
                'zh': '计划您的旅行',
                'ja': '旅行を計画する',
                'ru': 'Спланируйте поездку',
                'ar': 'خطط لرحلتك',
                'nl': 'Plan je reis',
                'pl': 'Zaplanuj swoją podróż'
            },
            'weather_alert': {
                'it': 'Allerta meteo',
                'en': 'Weather alert',
                'es': 'Alerta meteorológica',
                'fr': 'Alerte météo',
                'de': 'Wetterwarnung',
                'pt': 'Alerta meteorológico',
                'zh': '天气警报',
                'ja': '天気警報',
                'ru': 'Погодное предупреждение',
                'ar': 'تنبيه الطقس',
                'nl': 'Weerwaarschuwing',
                'pl': 'Alert pogodowy'
            },
            'crowd_level': {
                'it': 'Livello di affollamento',
                'en': 'Crowd level',
                'es': 'Nivel de multitud',
                'fr': 'Niveau de foule',
                'de': 'Auslastung',
                'pt': 'Nível de lotação',
                'zh': '拥挤程度',
                'ja': '混雑度',
                'ru': 'Уровень загруженности',
                'ar': 'مستوى الازدحام',
                'nl': 'Drukte niveau',
                'pl': 'Poziom tłoku'
            },
            'plan_b_activated': {
                'it': 'Piano B attivato',
                'en': 'Plan B activated',
                'es': 'Plan B activado',
                'fr': 'Plan B activé',
                'de': 'Plan B aktiviert',
                'pt': 'Plano B ativado',
                'zh': 'B计划已激活',
                'ja': 'プランBが有効',
                'ru': 'План Б активирован',
                'ar': 'تم تفعيل الخطة البديلة',
                'nl': 'Plan B geactiveerd',
                'pl': 'Plan B aktywowany'
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        
        # Quick detection based on common patterns
        if any(char in text for char in '你好中文'):
            return 'zh'
        if any(char in text for char in 'こんにちは日本'):
            return 'ja'
        if any(char in text for char in 'مرحبا'):
            return 'ar'
        if any(char in text for char in 'Привет'):
            return 'ru'
        
        # Use AI for more accurate detection
        try:
            prompt = f"Detect the language of this text and respond with ONLY the ISO 639-1 code (e.g., 'en', 'it', 'es'): '{text[:100]}'"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a language detection system. Respond only with ISO 639-1 language codes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                timeout=5
            )
            
            detected = response.choices[0].message.content.strip().lower()
            
            # Validate detected language
            if detected in self.supported_languages:
                return detected
            else:
                return 'en'  # Default to English if unsupported
                
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'
    
    @resilient_api_call('translation', fallback_data=None)
    @with_cache(translation_cache, lambda *args, **kwargs: f"trans_{args[1][:50]}_{args[2]}_{args[3]}")
    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'en', 'it')
            source_language: Source language code (auto-detect if None)
        """
        
        # Check if translation is needed
        if source_language == target_language:
            return text
        
        # Check common phrases cache first
        for phrase_key, translations in self.common_phrases.items():
            if text in translations.values():
                return translations.get(target_language, text)
        
        # Use AI for translation
        try:
            lang_name = self.supported_languages[target_language]['name']
            
            prompt = f"""
            Translate the following text to {lang_name}.
            Maintain the tone and context for a travel app.
            
            Text: {text}
            
            Respond with ONLY the translated text, no explanations.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": f"You are a professional translator specializing in travel and tourism. Translate accurately to {lang_name}."},
                    {"role": "user", "content": prompt}
                ],
                timeout=10
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Return original text if translation fails
    
    def translate_itinerary(self, itinerary: List[Dict], target_language: str) -> List[Dict]:
        """Translate an entire itinerary to the target language"""
        
        if target_language == 'it':
            return itinerary  # No translation needed for Italian
        
        translated = []
        
        for item in itinerary:
            translated_item = item.copy()
            
            # Translate text fields
            fields_to_translate = ['title', 'description', 'address', 'tips', 'note']
            
            for field in fields_to_translate:
                if field in translated_item and translated_item[field]:
                    translated_item[field] = self.translate(
                        translated_item[field],
                        target_language
                    )
            
            # Translate nested fields
            if 'details' in translated_item:
                for detail_field in fields_to_translate:
                    if detail_field in translated_item['details']:
                        translated_item['details'][detail_field] = self.translate(
                            translated_item['details'][detail_field],
                            target_language
                        )
            
            translated.append(translated_item)
        
        return translated
    
    def localize_ui(self, language: str) -> Dict:
        """Get localized UI strings for the specified language"""
        
        ui_strings = {
            'navigation': {
                'home': self.translate('Home', language, 'en'),
                'plan': self.translate('Plan Trip', language, 'en'),
                'profile': self.translate('Profile', language, 'en'),
                'settings': self.translate('Settings', language, 'en'),
                'logout': self.translate('Logout', language, 'en')
            },
            'buttons': {
                'search': self.translate('Search', language, 'en'),
                'save': self.translate('Save', language, 'en'),
                'cancel': self.translate('Cancel', language, 'en'),
                'continue': self.translate('Continue', language, 'en'),
                'back': self.translate('Back', language, 'en'),
                'next': self.translate('Next', language, 'en'),
                'finish': self.translate('Finish', language, 'en'),
                'add': self.translate('Add', language, 'en'),
                'remove': self.translate('Remove', language, 'en'),
                'edit': self.translate('Edit', language, 'en')
            },
            'messages': {
                'loading': self.translate('Loading...', language, 'en'),
                'error': self.translate('An error occurred', language, 'en'),
                'success': self.translate('Success!', language, 'en'),
                'no_results': self.translate('No results found', language, 'en'),
                'try_again': self.translate('Please try again', language, 'en')
            },
            'features': {
                'weather_aware': self.translate('Weather-Aware Planning', language, 'en'),
                'crowd_prediction': self.translate('Crowd Prediction', language, 'en'),
                'plan_b': self.translate('Smart Plan B', language, 'en'),
                'discoveries': self.translate('Intelligent Discoveries', language, 'en'),
                'travel_diary': self.translate('AI Travel Diary', language, 'en')
            },
            'time': {
                'morning': self.translate('Morning', language, 'en'),
                'afternoon': self.translate('Afternoon', language, 'en'),
                'evening': self.translate('Evening', language, 'en'),
                'night': self.translate('Night', language, 'en'),
                'today': self.translate('Today', language, 'en'),
                'tomorrow': self.translate('Tomorrow', language, 'en'),
                'yesterday': self.translate('Yesterday', language, 'en')
            },
            'weather': {
                'sunny': self.translate('Sunny', language, 'en'),
                'cloudy': self.translate('Cloudy', language, 'en'),
                'rainy': self.translate('Rainy', language, 'en'),
                'snowy': self.translate('Snowy', language, 'en'),
                'windy': self.translate('Windy', language, 'en'),
                'stormy': self.translate('Stormy', language, 'en')
            },
            'crowd_levels': {
                'very_quiet': self.translate('Very Quiet', language, 'en'),
                'quiet': self.translate('Quiet', language, 'en'),
                'moderate': self.translate('Moderate', language, 'en'),
                'crowded': self.translate('Crowded', language, 'en'),
                'very_crowded': self.translate('Very Crowded', language, 'en')
            }
        }
        
        return ui_strings
    
    def format_currency(self, amount: float, currency: str = 'EUR', language: str = 'en') -> str:
        """Format currency according to locale"""
        
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'CNY': '¥'
        }
        
        symbol = currency_symbols.get(currency, currency)
        
        # Format based on language conventions
        if language in ['en', 'ja', 'zh']:
            return f"{symbol}{amount:.2f}"
        else:  # European style
            return f"{amount:.2f} {symbol}"
    
    def format_date_time(self, datetime_obj, language: str = 'en', format_type: str = 'short') -> str:
        """Format date and time according to locale"""
        
        # This would ideally use proper locale formatting
        # For now, using simple formatting
        
        if format_type == 'short':
            if language == 'en':
                return datetime_obj.strftime('%m/%d/%Y %I:%M %p')
            elif language == 'it':
                return datetime_obj.strftime('%d/%m/%Y %H:%M')
            elif language in ['fr', 'es', 'pt']:
                return datetime_obj.strftime('%d/%m/%Y %H:%M')
            elif language == 'de':
                return datetime_obj.strftime('%d.%m.%Y %H:%M')
            elif language == 'ja':
                return datetime_obj.strftime('%Y年%m月%d日 %H:%M')
            elif language == 'zh':
                return datetime_obj.strftime('%Y年%m月%d日 %H:%M')
            else:
                return datetime_obj.strftime('%Y-%m-%d %H:%M')
        else:  # long format
            # Would implement full date names in each language
            return datetime_obj.strftime('%A, %B %d, %Y at %H:%M')
    
    def get_language_specific_tips(self, city: str, language: str) -> List[str]:
        """Get city tips in the user's language"""
        
        tips = {
            'it': [
                "Rispetta gli orari di riposo pomeridiano (14:00-16:00)",
                "La cena è solitamente dopo le 20:00",
                "Molti musei sono chiusi il lunedì",
                "Copri le spalle nelle chiese"
            ],
            'en': [
                "Respect afternoon rest hours (2-4 PM)",
                "Dinner is typically after 8 PM",
                "Many museums are closed on Mondays",
                "Cover shoulders in churches"
            ],
            'es': [
                "Respeta las horas de descanso (14:00-16:00)",
                "La cena es típicamente después de las 20:00",
                "Muchos museos cierran los lunes",
                "Cubre los hombros en las iglesias"
            ],
            'fr': [
                "Respectez les heures de repos (14h-16h)",
                "Le dîner est généralement après 20h",
                "Beaucoup de musées sont fermés le lundi",
                "Couvrez vos épaules dans les églises"
            ],
            'de': [
                "Respektieren Sie die Ruhezeiten (14-16 Uhr)",
                "Das Abendessen ist normalerweise nach 20 Uhr",
                "Viele Museen sind montags geschlossen",
                "Bedecken Sie Ihre Schultern in Kirchen"
            ]
        }
        
        return tips.get(language, tips['en'])


# Global multi-language support instance
multi_language = MultiLanguageSupport()
"""
Enhanced Error Handling and Circuit Breaker for External APIs
Provides resilient API calling with automatic fallbacks
"""

import time
import functools
import logging
from typing import Any, Callable, Optional, Dict
from collections import deque
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker pattern implementation for API calls"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        
    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception(f"Circuit breaker is open. Service unavailable.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    def _on_success(self):
        self.failure_count = 0
        self.state = 'closed'
        
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
    def _should_attempt_reset(self):
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)


class APIErrorHandler:
    """Comprehensive error handling for external API calls"""
    
    def __init__(self):
        self.circuit_breakers = {}
        self.retry_config = {
            'max_retries': 3,
            'initial_delay': 1,
            'backoff_factor': 2,
            'max_delay': 10
        }
        
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def with_retry(self, func: Callable, service_name: str, 
                   fallback_data: Optional[Any] = None) -> Any:
        """
        Execute function with retry logic and circuit breaker
        
        Args:
            func: Function to execute
            service_name: Name of the service for circuit breaker
            fallback_data: Data to return if all retries fail
            
        Returns:
            Function result or fallback data
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        last_exception = None
        delay = self.retry_config['initial_delay']
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                # Try to execute through circuit breaker
                result = circuit_breaker.call(func)
                
                # Log successful recovery if this was a retry
                if attempt > 0:
                    logger.info(f"{service_name}: Recovered after {attempt} retries")
                    
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"{service_name}: Attempt {attempt + 1} failed: {str(e)}")
                
                # Check if circuit is open
                if circuit_breaker.state == 'open':
                    logger.error(f"{service_name}: Circuit breaker is open, using fallback")
                    break
                    
                # Wait before retry (exponential backoff)
                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(min(delay, self.retry_config['max_delay']))
                    delay *= self.retry_config['backoff_factor']
        
        # All retries failed, use fallback
        logger.error(f"{service_name}: All retries failed, using fallback data")
        return fallback_data if fallback_data is not None else self._generate_default_fallback(service_name)
    
    def _generate_default_fallback(self, service_name: str) -> Dict:
        """Generate default fallback response based on service"""
        
        fallback_responses = {
            'openai': {
                'status': 'fallback',
                'message': 'AI service temporarily unavailable',
                'data': None,
                'timestamp': datetime.now().isoformat()
            },
            'scrapingdog': {
                'status': 'fallback',
                'attractions': [],
                'message': 'External data service unavailable',
                'timestamp': datetime.now().isoformat()
            },
            'nominatim': {
                'status': 'fallback',
                'coordinates': None,
                'message': 'Geocoding service unavailable',
                'timestamp': datetime.now().isoformat()
            },
            'default': {
                'status': 'fallback',
                'message': f'{service_name} service temporarily unavailable',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return fallback_responses.get(service_name, fallback_responses['default'])


# Global error handler instance
api_error_handler = APIErrorHandler()


def resilient_api_call(service_name: str, fallback_data: Optional[Any] = None):
    """
    Decorator for making API calls resilient with automatic retry and fallback
    
    Usage:
        @resilient_api_call('openai', fallback_data={'response': 'Default response'})
        def call_openai_api():
            # API call logic here
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return api_error_handler.with_retry(
                lambda: func(*args, **kwargs),
                service_name,
                fallback_data
            )
        return wrapper
    return decorator


# Cache implementation for expensive API calls
class APICache:
    """Simple time-based cache for API responses"""
    
    def __init__(self, ttl_seconds=300):  # 5 minutes default
        self.cache = {}
        self.ttl = ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                # Remove expired entry
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key}")
        return None
        
    def set(self, key: str, value: Any) -> None:
        """Set cache value with current timestamp"""
        self.cache[key] = (value, time.time())
        logger.debug(f"Cache set for key: {key}")
        
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Cache cleared")


# Global cache instances for different services
cache_openai = APICache(ttl_seconds=600)  # 10 minutes for AI responses
cache_scrapingdog = APICache(ttl_seconds=3600)  # 1 hour for scraped data
cache_nominatim = APICache(ttl_seconds=86400)  # 24 hours for geocoding


def with_cache(cache_instance: APICache, cache_key_func: Callable):
    """
    Decorator for caching API responses
    
    Usage:
        @with_cache(cache_openai, lambda *args: f"key_{args[0]}")
        def expensive_api_call(param):
            # API call logic here
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Check cache first
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_instance.set(cache_key, result)
                
            return result
        return wrapper
    return decorator
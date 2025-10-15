
"""
Enhanced Error Handling and Circuit Breaker for External APIs
Provides resilient API calling with automatic fallbacks
"""

import time
import functools
import logging
from typing import Any, Callable, Optional, Dict, List
from collections import deque
from datetime import datetime, timedelta
import json
import asyncio
from contextlib import asynccontextmanager

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
        self.failure_history = deque(maxlen=100)  # Track failure patterns
        
    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
                logger.info(f"Circuit breaker moving to half-open state")
            else:
                raise Exception(f"Circuit breaker is open. Service unavailable. Last failure: {self.last_failure_time}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure(str(e))
            raise e
            
    def _on_success(self):
        if self.state == 'half-open':
            logger.info("Circuit breaker test call successful, closing circuit")
        self.failure_count = 0
        self.state = 'closed'
        
    def _on_failure(self, error_msg):
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.failure_history.append({
            'timestamp': self.last_failure_time,
            'error': error_msg
        })
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures. Last error: {error_msg}")
            
    def _should_attempt_reset(self):
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def get_health_status(self):
        """Get current health status"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure': self.last_failure_time,
            'recent_failures': list(self.failure_history)[-5:]  # Last 5 failures
        }


class APIErrorHandler:
    """Comprehensive error handling for external API calls"""
    
    def __init__(self):
        self.circuit_breakers = {}
        self.retry_config = {
            'max_retries': 3,
            'initial_delay': 1,
            'backoff_factor': 2,
            'max_delay': 30
        }
        self.timeout_config = {
            'openai': 60,  # GPT-4/GPT-5 needs more time
            'scrapingdog': 30,
            'nominatim': 15,
            'geoapify': 20,
            'apify': 45,
            'default': 10
        }
        
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=120,  # 2 minutes recovery time
                expected_exception=Exception
            )
        return self.circuit_breakers[service_name]
    
    def with_retry_and_timeout(self, func: Callable, service_name: str, 
                              fallback_data: Optional[Any] = None,
                              custom_timeout: Optional[int] = None) -> Any:
        """
        Execute function with retry logic, timeout, and circuit breaker
        
        Args:
            func: Function to execute
            service_name: Name of the service for circuit breaker
            fallback_data: Data to return if all retries fail
            custom_timeout: Override default timeout for this call
            
        Returns:
            Function result or fallback data
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        timeout = custom_timeout or self.timeout_config.get(service_name, self.timeout_config['default'])
        
        last_exception = None
        delay = self.retry_config['initial_delay']
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                # Execute with timeout and circuit breaker
                start_time = time.time()
                
                def timeout_wrapper():
                    return circuit_breaker.call(func)
                
                result = self._execute_with_timeout(timeout_wrapper, timeout)
                
                execution_time = time.time() - start_time
                
                # Log successful recovery if this was a retry
                if attempt > 0:
                    logger.info(f"{service_name}: Recovered after {attempt} retries in {execution_time:.2f}s")
                else:
                    logger.debug(f"{service_name}: Success in {execution_time:.2f}s")
                    
                return result
                
            except TimeoutError as e:
                last_exception = e
                logger.warning(f"{service_name}: Timeout after {timeout}s on attempt {attempt + 1}")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"{service_name}: Attempt {attempt + 1} failed: {str(e)}")
                
                # Check if circuit is open
                if circuit_breaker.state == 'open':
                    logger.error(f"{service_name}: Circuit breaker is open, using fallback")
                    break
                    
            # Wait before retry (exponential backoff)
            if attempt < self.retry_config['max_retries'] - 1:
                sleep_time = min(delay, self.retry_config['max_delay'])
                logger.debug(f"{service_name}: Waiting {sleep_time}s before retry")
                time.sleep(sleep_time)
                delay *= self.retry_config['backoff_factor']
        
        # All retries failed, use fallback
        logger.error(f"{service_name}: All retries failed. Last error: {last_exception}")
        return self._get_intelligent_fallback(service_name, fallback_data, last_exception)
    
    def _execute_with_timeout(self, func: Callable, timeout: int):
        """Execute function with timeout using threading instead of signal"""
        import threading
        import queue
        
        result_queue = queue.Queue()
        exception_queue = queue.Queue()
        
        def worker():
            try:
                result = func()
                result_queue.put(result)
            except Exception as e:
                exception_queue.put(e)
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Thread is still running, timeout occurred
            raise TimeoutError(f"Function execution timed out after {timeout} seconds")
        
        # Check for exceptions
        if not exception_queue.empty():
            raise exception_queue.get()
        
        # Get result
        if not result_queue.empty():
            return result_queue.get()
        else:
            raise RuntimeError("Function completed but no result returned")
    
    def _get_intelligent_fallback(self, service_name: str, fallback_data: Optional[Any], 
                                error: Exception) -> Dict:
        """Generate intelligent fallback response based on service and error"""
        
        base_response = {
            'status': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        if fallback_data:
            base_response.update(fallback_data)
            return base_response
        
        intelligent_fallbacks = {
            'openai': {
                'response': 'Mi dispiace, il servizio AI è temporaneamente non disponibile. Per favore riprova tra qualche minuto.',
                'suggestions': [
                    'Verifica la tua connessione internet',
                    'Riprova con una query più semplice',
                    'Il servizio potrebbe essere sovraccarico, riprova tra 5-10 minuti'
                ],
                'alternative_action': 'Puoi continuare a esplorare usando le funzionalità base dell\'app'
            },
            'scrapingdog': {
                'attractions': [],
                'message': 'Dati luoghi temporaneamente non disponibili',
                'suggestions': [
                    'Usando dati cached precedenti',
                    'Prova con una città diversa',
                    'Verifica che il nome della città sia corretto'
                ],
                'alternative_action': 'Vengono mostrati luoghi popolari generici'
            },
            'nominatim': {
                'coordinates': None,
                'message': 'Geocoding temporaneamente non disponibile',
                'suggestions': [
                    'Verifica l\'ortografia del luogo',
                    'Prova con il nome in inglese',
                    'Usa coordinate GPS se disponibili'
                ],
                'alternative_action': 'Usando coordinate di default per la regione'
            },
            'apify': {
                'places': [],
                'message': 'Servizio dati luoghi premium non disponibile',
                'suggestions': [
                    'Passaggio automatico a fonti alternative',
                    'Alcuni dettagli potrebbero essere limitati',
                    'Riprova tra 10-15 minuti per dati completi'
                ],
                'alternative_action': 'Usando database locale e fonti gratuite'
            }
        }
        
        service_fallback = intelligent_fallbacks.get(service_name, {
            'message': f'{service_name} temporaneamente non disponibile',
            'suggestions': ['Riprova tra qualche minuto'],
            'alternative_action': 'Funzionalità base disponibili'
        })
        
        base_response.update(service_fallback)
        return base_response
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'services': {}
        }
        
        unhealthy_services = 0
        
        for service_name, circuit_breaker in self.circuit_breakers.items():
            service_health = circuit_breaker.get_health_status()
            service_health['timeout_config'] = self.timeout_config.get(service_name, self.timeout_config['default'])
            
            if service_health['state'] == 'open':
                service_health['status'] = 'unhealthy'
                unhealthy_services += 1
            elif service_health['state'] == 'half-open':
                service_health['status'] = 'recovering'
            else:
                service_health['status'] = 'healthy'
            
            health_status['services'][service_name] = service_health
        
        # Determine overall status
        total_services = len(self.circuit_breakers)
        if unhealthy_services == 0:
            health_status['overall_status'] = 'healthy'
        elif unhealthy_services < total_services / 2:
            health_status['overall_status'] = 'degraded'
        else:
            health_status['overall_status'] = 'unhealthy'
        
        health_status['healthy_services'] = total_services - unhealthy_services
        health_status['total_services'] = total_services
        
        return health_status


# Global error handler instance
api_error_handler = APIErrorHandler()


def resilient_api_call(service_name: str, fallback_data: Optional[Any] = None, 
                      timeout: Optional[int] = None):
    """
    Decorator for making API calls resilient with automatic retry, timeout and fallback
    
    Usage:
        @resilient_api_call('openai', timeout=60, fallback_data={'response': 'Default response'})
        def call_openai_api():
            # API call logic here
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return api_error_handler.with_retry_and_timeout(
                lambda: func(*args, **kwargs),
                service_name,
                fallback_data,
                timeout
            )
        return wrapper
    return decorator


# Enhanced cache with better error handling
class APICache:
    """Enhanced time-based cache for API responses with error handling"""
    
    def __init__(self, ttl_seconds=300, max_size=1000):
        self.cache = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.access_times = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        try:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    self.access_times[key] = time.time()
                    logger.debug(f"Cache hit for key: {key}")
                    return value
                else:
                    # Remove expired entry
                    self._remove_key(key)
                    logger.debug(f"Cache expired for key: {key}")
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        return None
        
    def set(self, key: str, value: Any) -> None:
        """Set cache value with current timestamp"""
        try:
            # Ensure cache doesn't grow too large
            if len(self.cache) >= self.max_size:
                self._cleanup_old_entries()
            
            current_time = time.time()
            self.cache[key] = (value, current_time)
            self.access_times[key] = current_time
            logger.debug(f"Cache set for key: {key}")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
        
    def _remove_key(self, key: str) -> None:
        """Safely remove key from cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def _cleanup_old_entries(self) -> None:
        """Remove old entries when cache is full"""
        # Remove oldest 20% of entries
        cleanup_count = max(1, self.max_size // 5)
        
        # Sort by access time and remove oldest
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        for key, _ in sorted_keys[:cleanup_count]:
            self._remove_key(key)
        
        logger.info(f"Cache cleanup: removed {cleanup_count} old entries")
        
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        current_time = time.time()
        expired_count = sum(1 for _, timestamp in self.cache.values() 
                          if current_time - timestamp >= self.ttl)
        
        return {
            'total_entries': len(self.cache),
            'expired_entries': expired_count,
            'valid_entries': len(self.cache) - expired_count,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl
        }


# Global cache instances with better configurations
cache_openai = APICache(ttl_seconds=1800, max_size=500)  # 30 minutes for AI responses
cache_scrapingdog = APICache(ttl_seconds=7200, max_size=1000)  # 2 hours for scraped data
cache_nominatim = APICache(ttl_seconds=86400, max_size=2000)  # 24 hours for geocoding
cache_apify = APICache(ttl_seconds=3600, max_size=800)  # 1 hour for Apify data


def with_cache(cache_instance: APICache, cache_key_func: Callable):
    """
    Decorator for caching API responses with error handling
    
    Usage:
        @with_cache(cache_openai, lambda prompt: f"openai_{hash(prompt)}")
        def expensive_api_call(prompt):
            # API call logic here
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
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
                
            except Exception as e:
                logger.error(f"Cache decorator error: {e}")
                # If caching fails, still try to execute the function
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


def log_api_call(service_name: str):
    """Decorator to log API calls for monitoring"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{service_name} API call successful in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{service_name} API call failed after {execution_time:.2f}s: {e}")
                raise
        return wrapper
    return decorator


import time
from typing import Dict, Any, Optional
from functools import wraps

class AdvancedCache:
    """Cache avanzato con TTL e LRU"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Ottieni valore da cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Controlla TTL
        if time.time() > entry['expires']:
            self.delete(key)
            return None
        
        # Aggiorna access time per LRU
        self.access_times[key] = time.time()
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Imposta valore in cache"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl,
            'created': time.time()
        }
        self.access_times[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Elimina da cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Rimuovi elemento meno recentemente usato"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self.delete(lru_key)

# Cache globale
global_cache = AdvancedCache()

def cached(ttl: int = 300):
    """Decorator per cache automatico"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crea chiave cache
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Prova cache
            result = global_cache.get(cache_key)
            if result is not None:
                return result
            
            # Esegui funzione e caching
            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

"""
Cache utilities for the Ridges API.
Provides TTL-based caching for database operations to reduce load and improve response times.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

class CacheManager:
    """Thread-safe cache manager with TTL support."""
    
    def __init__(self, ttl: int = 60, maxsize: int = 1000):
        """
        Initialize cache manager.
        
        Args:
            ttl: Time-to-live in seconds (default: 60)
            maxsize: Maximum number of cached items (default: 1000)
        """
        self.ttl = ttl
        self.maxsize = maxsize
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            try:
                value = self._cache[key]
                self._stats['hits'] += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            except KeyError:
                self._stats['misses'] += 1
                logger.debug(f"Cache miss for key: {key}")
                return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            old_size = len(self._cache)
            self._cache[key] = value
            self._stats['sets'] += 1
            
            # Track evictions
            if len(self._cache) < old_size:
                self._stats['evictions'] += 1
                
            logger.debug(f"Cache set for key: {key}")

    def delete(self, key: str) -> bool:
        """Delete specific key from cache."""
        with self._lock:
            try:
                del self._cache[key]
                logger.debug(f"Cache deleted for key: {key}")
                return True
            except KeyError:
                return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'hit_rate': hit_rate,
                'cache_size': len(self._cache),
                'max_size': self.maxsize,
                'ttl': self.ttl
            }

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from function arguments."""
        # Create a deterministic string from args and kwargs
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
        return f"{prefix}_{key_hash}"


# Global cache instance
cache_manager = CacheManager(ttl=60, maxsize=1000)


def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Optional custom TTL (uses default if None)
    
    Usage:
        @cached("challenges")
        def get_challenges():
            return expensive_db_call()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_clear = lambda: cache_manager.clear()
        wrapper.cache_stats = lambda: cache_manager.get_stats()
        wrapper.cache_delete = lambda *args, **kwargs: cache_manager.delete(
            cache_manager.generate_key(prefix, *args, **kwargs)
        )
        
        return wrapper
    return decorator


def cache_key_for_challenges(challenge_id: Optional[str] = None) -> str:
    """Generate cache key for challenge queries."""
    if challenge_id:
        return f"challenge_{challenge_id}"
    return "challenges_all"


def cache_key_for_miner_responses(**kwargs) -> str:
    """Generate cache key for miner response queries."""
    # Create a hash of all parameters for unique caching
    key_data = sorted(kwargs.items())
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
    return f"miner_responses_{key_hash}"


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    Returns number of entries removed.
    """
    with cache_manager._lock:
        keys_to_remove = [key for key in cache_manager._cache.keys() if pattern in key]
        for key in keys_to_remove:
            cache_manager.delete(key)
        
        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")
        
        return len(keys_to_remove)
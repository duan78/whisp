"""
Cache Manager Module with LRU (Least Recently Used) Cache Implementation

This module provides an efficient caching mechanism to optimize performance
of frequently accessed data in Whisp Assistant.
"""

import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import threading


class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) Cache implementation.

    This cache automatically removes the oldest entries when it reaches
    its maximum size, ensuring memory efficiency while maintaining fast
    access to frequently used data.

    Example:
        >>> cache = LRUCache(max_size=100)
        >>> cache.set('user_123', {'name': 'Alice'})
        >>> user = cache.get('user_123')
        >>> print(user)  # {'name': 'Alice'}
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize the LRU cache.

        Args:
            max_size: Maximum number of items to store in the cache.
                     When the cache is full, the oldest item is removed.
        """
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.

        Args:
            key: The key to retrieve

        Returns:
            The cached value, or None if the key doesn't exist
        """
        with self._lock:
            if key in self.cache:
                # Update timestamp to mark as recently used
                self.timestamps[key] = time.time()
                return self.cache[key]
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Store an item in the cache.

        If the cache is full, the least recently used item is removed.

        Args:
            key: The key to store
            value: The value to cache
        """
        with self._lock:
            # If key already exists, update it
            if key in self.cache:
                self.cache[key] = value
                self.timestamps[key] = time.time()
                return

            # If cache is full, remove the oldest item
            if len(self.cache) >= self.max_size:
                oldest = min(self.timestamps, key=self.timestamps.get)
                del self.cache[oldest]
                del self.timestamps[oldest]

            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()

    def delete(self, key: str) -> bool:
        """
        Remove an item from the cache.

        Args:
            key: The key to remove

        Returns:
            True if the key was found and removed, False otherwise
        """
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all items from the cache."""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()

    def size(self) -> int:
        """Return the current number of items in the cache."""
        with self._lock:
            return len(self.cache)

    def keys(self) -> list:
        """Return a list of all keys in the cache."""
        with self._lock:
            return list(self.cache.keys())

    def cleanup_old_entries(self, max_age_seconds: float) -> int:
        """
        Remove entries older than the specified age.

        Args:
            max_age_seconds: Maximum age in seconds for cache entries

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            keys_to_remove = [
                key for key, timestamp in self.timestamps.items()
                if current_time - timestamp > max_age_seconds
            ]

            for key in keys_to_remove:
                del self.cache[key]
                del self.timestamps[key]

            return len(keys_to_remove)


class CachedFunction:
    """
    Decorator for caching function results with LRU eviction.

    Example:
        >>> @CachedFunction(max_size=50, ttl=300)
        ... def expensive_function(param):
        ...     # Expensive computation
        ...     return result
    """

    def __init__(self, max_size: int = 100, ttl: Optional[float] = None):
        """
        Initialize the cached function decorator.

        Args:
            max_size: Maximum number of cached results
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = LRUCache(max_size=max_size)

    def __call__(self, func: Callable) -> Callable:
        """Wrap the function with caching logic."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call the function and cache the result
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result)

            # Cleanup old entries if TTL is set
            if self.ttl:
                self.cache.cleanup_old_entries(self.ttl)

            return result

        # Add cache control methods to the wrapped function
        wrapper.cache_clear = self.cache.clear
        wrapper.cache_info = lambda: {
            'size': self.cache.size(),
            'max_size': self.max_size,
            'ttl': self.ttl
        }

        return wrapper


# Global cache instances for common use cases

# Cache for configuration data
config_cache = LRUCache(max_size=50)

# Cache for command aliases
aliases_cache = LRUCache(max_size=100)

# Cache for user preferences
preferences_cache = LRUCache(max_size=200)

# Cache for STT metrics ( Speech-to-Text )
stt_metrics_cache = LRUCache(max_size=50)

# Cache for TTS results (Text-to-Speech)
tts_cache = LRUCache(max_size=100)


def clear_all_caches() -> None:
    """Clear all global cache instances."""
    config_cache.clear()
    aliases_cache.clear()
    preferences_cache.clear()
    stt_metrics_cache.clear()
    tts_cache.clear()


def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """
    Get statistics for all global cache instances.

    Returns:
        Dictionary with cache statistics
    """
    return {
        'config_cache': {
            'size': config_cache.size(),
            'max_size': 50
        },
        'aliases_cache': {
            'size': aliases_cache.size(),
            'max_size': 100
        },
        'preferences_cache': {
            'size': preferences_cache.size(),
            'max_size': 200
        },
        'stt_metrics_cache': {
            'size': stt_metrics_cache.size(),
            'max_size': 50
        },
        'tts_cache': {
            'size': tts_cache.size(),
            'max_size': 100
        }
    }

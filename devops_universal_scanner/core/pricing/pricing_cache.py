"""
Pricing Cache
In-memory cache for pricing data with TTL
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class PricingCache:
    """
    Simple in-memory cache for pricing data

    Operations:
    1. get - Get cached value
    2. set - Set cached value with TTL
    3. clear - Clear cache
    4. size - Get cache size
    """

    def __init__(self, ttl: int = 3600):
        """
        Initialize cache

        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry['expires']:
            # Expired, remove it
            del self._cache[key]
            return None

        return entry['value']

    def set(self, key: str, value: Any):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = {
            'value': value,
            'expires': time.time() + self.ttl,
            'created': time.time()
        }

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()

    def size(self) -> int:
        """Get number of cached entries"""
        # Clean up expired entries first
        current_time = time.time()
        expired_keys = [k for k, v in self._cache.items() if current_time > v['expires']]
        for key in expired_keys:
            del self._cache[key]

        return len(self._cache)

    def cleanup_expired(self):
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [k for k, v in self._cache.items() if current_time > v['expires']]
        for key in expired_keys:
            del self._cache[key]

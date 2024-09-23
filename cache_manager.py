# cache_manager.py

from cachetools import TTLCache, cached
from config import Config

# Initialize a TTLCache
cache = TTLCache(maxsize=Config.CACHE_MAXSIZE, ttl=Config.CACHE_TTL)

def get_cached_suggestion(prompt):
    return cache.get(prompt)

def set_cached_suggestion(prompt, suggestion):
    cache[prompt] = suggestion

import os
import re
import threading
import unicodedata
from typing import Any, Dict, Optional
from cachetools import TTLCache

# Regex patterns for Arabic text normalization
TASHKEEL_REGEX = re.compile(r"[\u0617-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TATWEEL_REGEX = re.compile(r"\u0640")
PUNCTUATION_REGEX = re.compile(r"[\.,;:!?\(\)\[\]\{\}\'\"«»ـ،؟؛—\-_/\\]")
WHITESPACE_REGEX = re.compile(r"\s+")

def normalize_arabic_cache_key(text: str) -> str:
    """
    Normalizes Arabic text to produce a canonical cache key invariant to:
    - Tashkeel (diacritics, harakat, tanween, shaddah, quranic marks)
    - Tatweel / Kashida (ـ)
    - Alef variants (إ, أ, آ, ٱ, ا -> ا)
    - Taa marbuta and Haa (ة -> ه)
    - Yaa and Alef Maqsura (ى, ي -> ي)
    - Punctuation, symbols, and irregular spacing
    """
    if not text:
        return ""
    
    # 1. Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    
    # 2. Strip Tashkeel (harakat, tanween, shaddah)
    text = TASHKEEL_REGEX.sub("", text)
    
    # 3. Strip Tatweel
    text = TATWEEL_REGEX.sub("", text)
    
    # 4. Standardize Alef forms
    text = re.sub(r"[إأآٱا]", "ا", text)
    
    # 5. Standardize Yaa and Alef Maqsura
    text = re.sub(r"[ىي]", "ي", text)
    
    # 6. Standardize Taa Marbuta and Haa
    text = re.sub(r"ة", "ه", text)
    
    # 7. Strip punctuation and symbols
    text = PUNCTUATION_REGEX.sub(" ", text)
    
    # 8. Collapse whitespace and trim
    text = WHITESPACE_REGEX.sub(" ", text).strip().lower()
    
    return text

class ArabicVerificationCache:
    """
    Thread-safe in-memory cache with Arabic-aware key normalization
    and comprehensive hit/miss statistics.
    """
    def __init__(self, maxsize: int = 10000, ttl: int = 3600):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        key = normalize_arabic_cache_key(query)
        if not key:
            return None
        with self._lock:
            val = self._cache.get(key)
            if val is not None:
                self._hits += 1
                return val
            self._misses += 1
            return None

    def set(self, query: str, value: Dict[str, Any]) -> None:
        key = normalize_arabic_cache_key(query)
        if not key:
            return
        with self._lock:
            self._cache[key] = value

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total * 100) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "maxsize": self._cache.maxsize,
                "ttl_seconds": self._cache.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "total_lookups": total,
                "hit_ratio_percent": round(hit_ratio, 2)
            }

# Global singleton instance configured via environment variables
CACHE_MAXSIZE = int(os.getenv("CACHE_MAXSIZE", 10000))
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
verification_cache = ArabicVerificationCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)

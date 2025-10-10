"""
Token Cache System för Dynamic Token Resolution.
Hanterar caching av token-information för att minska API-anrop och förbättra prestanda.
"""
import json
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TokenCache:
    """Cache-system för token-information med filbaserad persistens."""

    def __init__(self, cache_file: str = "token_cache.json", cache_duration: int = 3600):
        """
        Initiera token cache.

        Args:
            cache_file: Filnamn för cache-persistens
            cache_duration: Cache-varaktighet i sekunder (default 1 timme)
        """
        self.cache_file = os.path.join(os.path.dirname(__file__), cache_file)
        self.cache_duration = cache_duration
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Ladda cache från fil."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory_cache = data.get('cache', {})
                    logger.info(f"Loaded {len(self.memory_cache)} cached tokens from {self.cache_file}")
            else:
                logger.info("No existing cache file found, starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load cache from file: {e}")
            self.memory_cache = {}

    def _save_cache(self) -> None:
        """Spara cache till fil."""
        try:
            data = {
                'cache': self.memory_cache,
                'last_updated': datetime.now().isoformat(),
                'cache_duration': self.cache_duration
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.memory_cache)} tokens to cache")
        except Exception as e:
            logger.error(f"Failed to save cache to file: {e}")

    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Kontrollera om cache-entry har gått ut."""
        if 'timestamp' not in cache_entry:
            return True

        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        expiry_time = cached_time + timedelta(seconds=self.cache_duration)

        return datetime.now() > expiry_time

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Hämta värde från cache.

        Args:
            key: Cache-nyckel

        Returns:
            Cache-värde eller None om inte finns eller utgått
        """
        if key not in self.memory_cache:
            return None

        cache_entry = self.memory_cache[key]

        if self._is_expired(cache_entry):
            logger.debug(f"Cache entry expired for key: {key}")
            del self.memory_cache[key]
            self._save_cache()
            return None

        logger.debug(f"Cache hit for key: {key}")
        return cache_entry.get('data')

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Sätt värde i cache.

        Args:
            key: Cache-nyckel
            value: Värde att cacha
        """
        cache_entry = {
            'data': value,
            'timestamp': datetime.now().isoformat(),
            'key': key
        }

        self.memory_cache[key] = cache_entry
        self._save_cache()

        logger.debug(f"Cached token data for key: {key}")

    def delete(self, key: str) -> None:
        """
        Ta bort värde från cache.

        Args:
            key: Cache-nyckel att ta bort
        """
        if key in self.memory_cache:
            del self.memory_cache[key]
            self._save_cache()
            logger.debug(f"Removed cache entry for key: {key}")

    def clear(self) -> None:
        """Rensa hela cachen."""
        self.memory_cache.clear()
        self._save_cache()
        logger.info("Cleared entire token cache")

    def get_stats(self) -> Dict[str, Any]:
        """Hämta cache-statistik."""
        total_entries = len(self.memory_cache)
        expired_entries = sum(1 for entry in self.memory_cache.values() if self._is_expired(entry))
        valid_entries = total_entries - expired_entries

        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_file': self.cache_file,
            'cache_duration_seconds': self.cache_duration,
            'cache_duration_hours': self.cache_duration / 3600
        }

    def cleanup_expired(self) -> int:
        """
        Rensa utgångna cache-entries.

        Returns:
            Antal rensade entries
        """
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self.memory_cache[key]

        if expired_keys:
            self._save_cache()
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def search_similar(self, search_term: str, limit: int = 10) -> list:
        """
        Sök efter liknande tokens i cachen.

        Args:
            search_term: Sökterm
            limit: Max antal resultat

        Returns:
            Lista med matchande tokens
        """
        results = []
        search_lower = search_term.lower()

        for key, entry in self.memory_cache.items():
            if self._is_expired(entry):
                continue

            token_data = entry.get('data', {})

            # Sök i olika fält
            searchable_fields = [
                token_data.get('symbol', '').lower(),
                token_data.get('name', '').lower(),
                token_data.get('address', '').lower(),
                key.lower()
            ]

            if any(search_lower in field for field in searchable_fields):
                results.append({
                    'key': key,
                    'data': token_data,
                    'match_score': self._calculate_match_score(search_term, token_data)
                })

        # Sortera efter match score och returnera limit antal
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:limit]

    def _calculate_match_score(self, search_term: str, token_data: Dict[str, Any]) -> float:
        """Beräkna match score för sökresultat."""
        search_lower = search_term.lower()
        score = 0.0

        # Exakt match på symbol ger högsta poäng
        if token_data.get('symbol', '').lower() == search_lower:
            score += 10.0

        # Exakt match på namn ger hög poäng
        if token_data.get('name', '').lower() == search_lower:
            score += 8.0

        # Partial match på symbol
        if search_lower in token_data.get('symbol', '').lower():
            score += 5.0

        # Partial match på namn
        if search_lower in token_data.get('name', '').lower():
            score += 3.0

        # Match på address
        if search_lower in token_data.get('address', '').lower():
            score += 2.0

        return score
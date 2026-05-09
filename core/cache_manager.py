from datetime import datetime, timedelta
from logger.logger import get_logger

class CacheManager:

    def __init__(self, cache_name='cache'):
        self.kv_store = None
        self.cache_name = cache_name
        self._logger = get_logger(__name__)

    async def __aenter__(self):
        from crawlee.storages import KeyValueStore
        self.kv_store = await KeyValueStore.open(name=self.cache_name)
        return self

    async def __aexit__(self, *args):
        # KeyValueStore does not need explicit close
        pass


    async def get(self, key):
        """
        Retrieve (data, True) from the cache if exists and not expired. Else (None, False)
        """
        cached = await self.kv_store.get_value(key)
        if cached:
            timestamp = cached.get('timestamp')
            ttl = cached.get('ttl', 0)

            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            expired_at = timestamp + timedelta(seconds=ttl)

            if expired_at > datetime.now():
                self._logger.debug(f"Cache HIT for key: {key}")
                return cached.get('data'), True

        self._logger.debug(f"Cache expired for key: {key}")
        return None, False

    async def set(self, key, data, url, ttl=900):
        """
        Save data with TTL
        """
        entry = {
            'url': url,
            'ttl': ttl,
            'timestamp': datetime.now().isoformat(),
            'data': data,
        }
        self._logger.debug(f"Saving in cache: KEY {key} with TTL {ttl}")
        await self.kv_store.set_value(key, entry)
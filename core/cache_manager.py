from crawlee.storages import KeyValueStore
from datetime import datetime, timedelta


class CacheManager:

    def __init__(self, cache_name='cache'):
        self.kv_store = None
        self.cache_name = cache_name

    async def __aenter__(self):
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
                return cached.get('data'), True

        return None, False

    async def set(self, key, data, ttl_seconds=900):
        """
        Save data with TTL
        """
        entry = {
            'data': data,
            'ttl': ttl_seconds,
            'timestamp': datetime.now().isoformat(),
        }
        await self.kv_store.set_value(key, entry)
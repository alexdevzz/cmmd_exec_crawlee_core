import hashlib
from abc import ABC, abstractmethod


class BaseScrapingService(ABC):
    """
    Servicio base que combina cache y crawler genérico.
    Las subclases deben implementar extract_data().
    """

    def __init__(self):
        self.crawler_type = 'bs4'
        self.max_concurrency = 5
        self.cache_name = 'scraping-cache'
        self._crawler = None # lazy init
        self.url = 'https://www.google.com/'
        self.ttl_seconds = 900
        self.cache_key = None

    def _get_crawler(self):
        if self._crawler is None:
            from core.generic_crawler import GenericCrawler
            self._crawler = GenericCrawler(crawler_type=self.crawler_type, max_concurrency=self.max_concurrency)
        return self._crawler

    @abstractmethod
    async def extract_data(self, context):
        """
        Método que deben implementar las subclases.
        :param context: BeautifulSoupContext o PlaywrightContext
        :return: Diccionario con los datos extraídos
        """
        pass

    async def run(self):
        """
        Obtiene datos de la URL, usando caché si está vigente.
        Si no hay caché o expiró, ejecuta el crawler y guarda.
        """

        # 0.1 Settear la cache_key si es 'None'
        if self.cache_key is None:
            self.cache_key = f'cache_{hashlib.md5(self.url.encode()).hexdigest()}'

        # 1. Consultar cache
        from core.cache_manager import CacheManager
        async with CacheManager(self.cache_name) as cache:
            data, found = await cache.get(self.cache_key)
            if found:
                print(f'[{self.__class__.__name__}] Using cache for: {self.url}')
                return data

        # 2. No esta en cache: usar crawler
        print(f"[{self.__class__.__name__}] Scraping (without cache): {self.url}")
        crawler = self._get_crawler()
        # el estractor es nuestro metodo extract_data
        result = await crawler.scrape(self.url, self.extract_data)

        # 3. Guardar en cache
        async with CacheManager(self.cache_name) as cache:
            await cache.set(self.cache_key, result, self.url, ttl=self.ttl_seconds)
            print(f'[{self.__class__.__name__}] Data saved on cache for: {self.url}')

        return result




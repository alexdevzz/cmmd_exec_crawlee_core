import hashlib
import uuid
from abc import ABC, abstractmethod

from config.config import get_config
from logger.logger import get_logger


# cargar la configuracion
from config.config import load_config
config = load_config()

# Configurar logging
from logger.logger import setup_logging
setup_logging()

# Añadir configuraciones extras a Crawlee antes de que se inicialice.
# Configurar el directorio de almacenamiento de Crawlee (antes de importar otras cosas)
from crawlee.configuration import Configuration
Configuration.get_global_configuration().storage_dir = config['storage']['path']


class BaseScrapingService(ABC):
    """
    Servicio base que combina cache y crawler genérico.
    Las subclases deben implementar extract_data().
    """

    def __init__(self):
        cfg = get_config()
        self.crawler_type = cfg['crawler']['type']
        self.max_concurrency = cfg['crawler']['max_concurrency']
        self.cache_name = cfg['cache']['name']
        self.cache_key_prefix = cfg['cache']['key_prefix']
        self.ttl_seconds = cfg['cache']['ttl_seconds']
        self.url = 'https://www.google.com/'
        self._cache_key = None
        self._crawler = None # lazy init
        self._logger = get_logger(self.__class__.__name__)


    @property
    def cache_key(self):
        if self._cache_key is not None:
            return self._cache_key
        cfg = get_config()
        key = cfg['cache']['key']
        if key == 'encrypt-url':
            return f"{hashlib.md5(self.url.encode('utf-8')).hexdigest()}"
        if key == 'url':
            return f"{self.url}"
        if key == 'uuid':
            return self._generate_ramdom_uuid()
        return self._generate_ramdom_uuid()

    @cache_key.setter
    def cache_key(self, value):
        self._cache_key = value

    def __str__(self):
        return (f'ScrapingService(crawler_type={self.crawler_type}, '
                f'max_concurrency={self.max_concurrency}, '
                f'cache_name={self.cache_name}, '
                f'cache_key_prefix={self.cache_key_prefix}, '
                f'ttl_seconds={self.ttl_seconds}, '
                f'url={self.url}, '
                f'cache_key={self.cache_key})')


    @staticmethod
    def _generate_ramdom_uuid():
        return str(uuid.uuid4())

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

        # 1. Consultar cache
        from core.cache_manager import CacheManager
        async with CacheManager(self.cache_name) as cache:
            cache_path = self.cache_key_prefix + self.cache_key
            data, found = await cache.get(cache_path)
            if found:
                self._logger.info(f'Using cache for: {self.url}')
                return data

        # 2. No está en cache: usar crawler
        self._logger.info(f"Not cache found. Scraping: {self.url}")
        crawler = self._get_crawler()
        # el extractor es nuestro método extract_data
        result = await crawler.scrape(self.url, self.extract_data)

        # 3. Guardar en cache
        async with CacheManager(self.cache_name) as cache:
            self._logger.info(f'Data saved on cache for: {self.url}')
            await cache.set(cache_path, result, self.url, ttl=self.ttl_seconds)

        return result








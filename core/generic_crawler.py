import asyncio

from crawlee.crawlers import BeautifulSoupCrawler, PlaywrightCrawler
from crawlee.router import Router


class GenericCrawler:

    def __init__(self, crawler_type='bs4', max_concurrency=5):
        self.crawler_type = crawler_type
        self.max_concurrency = max_concurrency
        self._crawler = None
        self._router = Router()


    def _create_crawler(self):
        if self.crawler_type == 'bs4':
            return BeautifulSoupCrawler(
                max_requests_per_crawl = 1,
                max_concurrency = self.max_concurrency,
                router = self._router,
            )
        elif self.crawler_type == 'playwright':
            return PlaywrightCrawler(
                max_requests_per_crawl = 1,
                max_concurrency = self.max_concurrency,
                router = self._router,
                headless=True,
            )
        else:
            raise ValueError(f'Invalid crawler type: {self.crawler_type}')


    async def scrape(self, url, extractor):
        """
        Ejecuta el crawler para una URL y aplica el extractor.
        extractor es una función que recibe el contexto (BeautifulSoupCrawlingContext o PlaywrightCrawlingContext)
        y devuelve un diccionario con los datos extraídos.
        """

        # limpiar el router anterior por si acaso
        self._router = Router()
        result_data = {}

        # definir handler dinamico
        @self._router.default_handler
        async def handler(context):
            nonlocal result_data
            # llamar el extractor proporcionado
            extracted = await extractor(context) if asyncio.iscoroutinefunction(extractor) else extractor(context)
            result_data = extracted
            # no es necesario enqueue links

        # crear crawler si no existe
        if self._crawler is None:
            self._crawler = self._create_crawler()

        # ejecutar con una sola URL
        await self._crawler.run([url])
        return result_data
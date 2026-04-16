
class GenericCrawler:

    def __init__(self, crawler_type='bs4', max_concurrency=5):
        self.crawler_type = crawler_type
        self.max_concurrency = max_concurrency

    def _create_crawler(self, router):
        from crawlee import ConcurrencySettings
        concurrency = ConcurrencySettings(
            max_concurrency=self.max_concurrency,
            desired_concurrency=1
        )

        if self.crawler_type == 'bs4':
            from crawlee.crawlers import BeautifulSoupCrawler
            return BeautifulSoupCrawler(
                max_requests_per_crawl = 1,
                concurrency_settings = concurrency,
                request_handler = router
            )
        elif self.crawler_type == 'playwright':
            from crawlee.crawlers import PlaywrightCrawler
            return PlaywrightCrawler(
                max_requests_per_crawl = 1,
                concurrency_settings = concurrency,
                request_handler = router,
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

        from crawlee.router import Router
        router = Router()
        result_data = {}

        # definir handler dinamico
        @router.default_handler
        async def handler(context):
            nonlocal result_data
            # llamar el extractor proporcionado
            import asyncio
            extracted = await extractor(context) if asyncio.iscoroutinefunction(extractor) else extractor(context)
            result_data = extracted
            # no es necesario enqueue links

        crawler = self._create_crawler(router)

        # ejecutar con una sola URL
        await crawler.run([url])
        return result_data
import sys
from pathlib import Path

from config.config import get_config
import logging


def setup_logging():
    """
    Configura el logging global según config.yml
    """
    config = get_config()
    logger_cfg = config.get('logging', {})

    level = getattr(logging, logger_cfg.get('level', 'INFO').upper(), logging.INFO)
    fmt = logger_cfg.get('format', '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    datefmt = logger_cfg.get('datefmt', '%Y-%m-%d %H:%M:%S')

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()  # Evita duplicados si se llama varias veces

    # Handler de archivo (siempre)
    log_file = logger_cfg.get('file', 'logs/scraper.log')
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        root_logger.addHandler(file_handler)

    # Handler de consola (Opcional)
    use_console = logger_cfg.get('console', True)
    if use_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        root_logger.addHandler(console_handler)


    # Nivel específico para Crawlee
    crawlee_level = logger_cfg.get('crawlee_level')
    if crawlee_level:
        logging.getLogger('crawlee').setLevel(getattr(logging, crawlee_level.upper()))

    # Nivel específico para Asyncio
    asyncio_level = logger_cfg.get('asyncio_level')
    if asyncio_level:
        logging.getLogger('asyncio').setLevel(getattr(logging, asyncio_level.upper()))


def get_logger(name):
    """
    Devuelve el logger con el nombre dado
    """
    return logging.getLogger(name)



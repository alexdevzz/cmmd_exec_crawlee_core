# 🕷️ Scraping Framework with Crawlee (Core)

Framework modular de scraping construido sobre [Crawlee](https://crawlee.dev/) que proporciona una arquitectura reutilizable con sistema de caché integrado, configuración externalizada y logging estructurado.

## 📦 Estructura del proyecto

```
├── config/
│   ├── config.yaml               # Configuración centralizada de la aplicación
│   └── config.py                 # Archivo de python para cargar y leer la configuración
├── core/
│   ├── base_scraping_service.py  # Clase abstracta que orquesta caché + crawler
│   ├── cache_manager.py          # Envoltorio de KeyValueStore con soporte TTL
│   └── generic_crawler.py        # Fábrica de crawlers (BS4 / Playwright)
├── logger/
│   └── logger.py                 # Sistema de logging configurable vía YAML
├── .gitignore                    # Exclusiones de git
├── .requirements.txt             # Listado de librerias a instalar
└── README.md
```

---

## 🧱 Componentes principales

### 1. `BaseScrapingService` (abstracta)

**Propósito**: Proveer un flujo de trabajo común para cualquier scraper. Es la clase de la que se debe heredar y luego sobrescribir sus atributos para cada scraping.

**Flujo interno del método `run()`**:

1. **Consulta la caché**: si los datos existen y no han expirado, los devuelve inmediatamente.
2. **Ejecuta el crawler**: si no hay caché válida, invoca al `GenericCrawler` para que visite la URL y extraiga los datos mediante el método abstracto `extract_data()`.
3. **Guarda en caché**: almacena el resultado con un TTL configurable.

**Atributos configurables**:

| Atributo | Origen | Descripción |
|---|---|---|
| `crawler_type` | `config.yaml` | `'bs4'` o `'playwright'` |
| `max_concurrency` | `config.yaml` | Número máximo de peticiones simultáneas |
| `cache_name` | `config.yaml` | Nombre del `KeyValueStore` |
| `cache_key_prefix` | `config.yaml` | Prefijo para las claves de caché |
| `ttl_seconds` | `config.yaml` | Tiempo de vida de la caché en segundos |
| `url` | Subclase | URL objetivo del scraping |
| `cache_key` | Propiedad dinámica | `cache_key_prefix + md5(url)` |

### 2. `CacheManager`

**Propósito**: envoltorio asíncrono alrededor de `KeyValueStore` de Crawlee que añade expiración de entradas.

- Utiliza `async with` para abrir/cerrar el almacén.
- `get(key)`: recupera una entrada, comprueba su timestamp y TTL, y devuelve `(data, True)` si aún es válida, o `(None, False)` en caso contrario.
- `set(key, data, ttl)`: guarda un diccionario con `data`, `ttl` y `timestamp` en formato ISO 8601.

### 3. `GenericCrawler`

**Propósito**: fábrica de crawlers que simplifica la creación de rastreadores de una sola URL.

- Soporta `BeautifulSoupCrawler` y `PlaywrightCrawler`.
- Configura `ConcurrencySettings` desde `max_concurrency`.
- El método `scrape(url, extractor)`:
  1. Crea un `Router` con un `default_handler` que ejecuta la función `extractor`.
  2. El resultado de `extractor` se guarda en una variable `result_data` mediante `nonlocal`.
  3. Ejecuta el crawler con `max_requests_per_crawl=1` (una sola URL).

### 4. Sistema de logging (`logger.py`)

- Lee la configuración de `config.yaml` (sección `logging`).
- Soporta salida a consola y a archivo.
- Permite silenciar el logger interno de Crawlee (`crawlee_level`).
- Función `setup_logging()` se llama una vez al inicio de la aplicación.
- Función `get_logger(name)` para obtener un logger configurado en cualquier módulo.

---

## ⚙️ Configuración (`config.yaml`)

```yaml
# Configuraciones

# Todas estas configuraciones son aplicadas por defecto
# siempre y cuando no sean sobrescritas por herencia.

crawler:
  type: bs4                           # 'bs4' o 'playwright'
  max_concurrency: 5                  # Concurrencia maxima

cache:
  name: scraping-cache                # Nombre del KeyValueStore de Crawlee (directorio)

  key: encrypt-url                    # Nombre de la cache para los servicios (subdirectorio)
                                      # puede ser: [encrypt-url, url, uuid, "nombre sobrescrito en clase hija"]

  key_prefix: cache_                  # Prefijo para las claves dentro de la cache
  ttl_seconds: 900                    # Tiempo de vida por defecto

storage:
  path: ./crawlee_storage             # Directorio donde Crawlee guarda sus datos
                                      # Contiene dentro a cache:name y cache:key (directorio principal)

logging:
  level: DEBUG                         # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: logs/scraper.log               # Si quieres guardar en archivo, déjalo vació para solo consola
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  datefmt: "%Y-%m-%d %H:%M:%S"

  crawlee_level: WARNING              # Opcional: nivel específico para Crawlee
  asyncio_level: WARNING              # Opcional: nivel específico para Asyncio
```

---

## 🚀 Instalación y uso

```bash
pip install -r requirements.txt   # (crawlee, pyyaml, etc.)
```

En tu `main.py`:

```python
import asyncio
import sys

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

# importar modulos que usan Crawlee
from horoscope.horoscope import HoroscopeScraper

if __name__ == '__main__':

  args = sys.argv[1:]

  scraper = HoroscopeScraper()      # Clase que hereda de BaseScrapingService 
  data = asyncio.run(scraper.run())

  print(data)
```

---

## 🧪 Tecnología utilizada

- **Crawlee for Python**: motor de crawling y scraping.
- **BeautifulSoup4** / **Playwright**: parsers HTML y navegadores headless.
- **PyYAML**: lectura de configuración externa.
- **Logging estándar de Python**: sistema de trazado estructurado.




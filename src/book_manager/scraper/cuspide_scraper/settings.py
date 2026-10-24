import sys
from pathlib import Path

BOT_NAME = "cuspide_scraper"

SPIDER_MODULES = ["cuspide_scraper.spiders"]
NEWSPIDER_MODULE = "cuspide_scraper.spiders"

# Agrega la carpeta src/ al sys.path para poder importar book_manager
# al ejecutar el comando `scrapy crawl` desde esta carpeta.
RUTA_SRC = Path(__file__).resolve().parents[3]
if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 4
# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 2
#CONCURRENT_REQUESTS_PER_IP = 16
# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Enable and configure the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1.0
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 10.0
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}

# Configure item pipelines
ITEM_PIPELINES = {
    "cuspide_scraper.pipelines.ValidacionPipeline": 100,
    "cuspide_scraper.pipelines.DuplicadosPipeline": 200,
    "cuspide_scraper.pipelines.LimpiezaPipeline": 300,
    "cuspide_scraper.pipelines.JsonPipeline": 400,
}

CUSPIDE_JSON_PATH = "downloads/cuspide.json"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"

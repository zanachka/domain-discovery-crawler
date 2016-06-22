BOT_NAME = 'dd_crawler'

SPIDER_MODULES = ['dd_crawler.spiders']
NEWSPIDER_MODULE = 'dd_crawler.spiders'

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/51.0.2704.84 Safari/537.36')

# Scrapy-redis settings
# Enables scheduling storing requests queue in redis.
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# Don't cleanup redis queues, allows to pause/resume crawls.
SCHEDULER_PERSIST = True
# SCHEDULER_QUEUE_CLASS = 'dd_crawler.queue.RequestQueue'
SCHEDULER_QUEUE_CLASS = 'dd_crawler.queue.CompactRequestQueue'

DEPTH_PRIORITY = 1

HTTPCACHE_ENABLED = False
REDIRECT_ENABLED = True
COOKIES_ENABLED = True
DOWNLOAD_TIMEOUT = 240
RETRY_ENABLED = False
DOWNLOAD_MAXSIZE = 1*1024*1024

# Auto throttling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_DEBUG = False
AUTOTHROTTLE_MAX_DELAY = 3.0
AUTOTHROTTLE_START_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = False

# Concurrency
CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 10
DOWNLOAD_DELAY = 0.0

REACTOR_THREADPOOL_MAXSIZE = 32
DNS_TIMEOUT = 180

LOG_LEVEL = 'INFO'

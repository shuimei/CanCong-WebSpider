# 定义 Scrapy 项目
BOT_NAME = 'webspider'

SPIDER_MODULES = ['webspider.spiders']
NEWSPIDER_MODULE = 'webspider.spiders'

# 请求遵守robots.txt规则（可以设为False忽略）
ROBOTSTXT_OBEY = False

# 并发请求数量
CONCURRENT_REQUESTS = 4

# 请求延迟（秒）
DOWNLOAD_DELAY = 2

# 随机化延迟(0.5 * to 1.5 * DOWNLOAD_DELAY)
RANDOMIZE_DOWNLOAD_DELAY = True

# 支持JavaScript渲染
DOWNLOADER_MIDDLEWARES = {
    'webspider.middlewares.JSMiddleware': 585,
    'webspider.middlewares.DuplicateFilterMiddleware': 590,
}

# 数据处理管道
ITEM_PIPELINES = {
    'webspider.pipelines.UrlFilterPipeline': 300,
    'webspider.pipelines.HtmlSavePipeline': 400,
    'webspider.pipelines.StatisticsPipeline': 500,
}

# 用户代理
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# 请求头
DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en',
}

# 数据库配置
DATABASE_URL = 'spider_urls.db'
WEBPAGES_DIR = 'webpages'

# 日志配置
LOG_LEVEL = 'INFO'
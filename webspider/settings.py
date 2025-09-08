from webspider.config import DatabaseConfig, AppConfig

# 定义 Scrapy 项目
BOT_NAME = 'webspider'

SPIDER_MODULES = ['webspider.spiders']
NEWSPIDER_MODULE = 'webspider.spiders'

# 请求遵守robots.txt规则（可以设为False忽略）
ROBOTSTXT_OBEY = False

# 并发请求数量 - 提高并发数
CONCURRENT_REQUESTS = 8

# 请求延迟（秒） - 减少延迟提高效率
DOWNLOAD_DELAY = 1

# 随机化延迟(0.5 * to 1.5 * DOWNLOAD_DELAY)
RANDOMIZE_DOWNLOAD_DELAY = True

# 支持JavaScript渲染（暂时禁用以避免超时问题）
DOWNLOADER_MIDDLEWARES = {
    # 'webspider.middlewares.JSMiddleware': 585,  # 暂时禁用
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

# 数据库配置 - 使用PostgreSQL
db_config = DatabaseConfig()
DATABASE_URL = db_config.get_postgres_url()
WEBPAGES_DIR = AppConfig.WEBPAGES_DIR

# 日志配置 - 设置为WARNING级别以减少干扰信息
LOG_LEVEL = 'WARNING'
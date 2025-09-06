import scrapy


class UrlItem(scrapy.Item):
    """URL数据项"""
    url = scrapy.Field()          # URL地址
    source_url = scrapy.Field()   # 来源URL
    depth = scrapy.Field()        # 抓取深度
    title = scrapy.Field()        # 页面标题
    status = scrapy.Field()       # 抓取状态


class PageItem(scrapy.Item):
    """网页内容数据项"""
    url = scrapy.Field()          # URL地址
    html_content = scrapy.Field() # HTML内容
    title = scrapy.Field()        # 页面标题
    extracted_urls = scrapy.Field() # 提取的URL列表
    crawl_time = scrapy.Field()   # 抓取时间
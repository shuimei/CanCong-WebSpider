import time
import asyncio
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured, IgnoreRequest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webspider.database import UrlDatabase


class JSMiddleware:
    """JavaScript渲染中间件"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.driver = None
        self.setup_driver()
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def setup_driver(self):
        """设置Chrome WebDriver"""
        try:
            from selenium.webdriver.chrome.service import Service
            try:
                # 尝试使用webdriver-manager自动管理ChromeDriver
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except ImportError:
                # 如果没有webdriver-manager，使用系统PATH中的ChromeDriver
                service = None
            
            options = Options()
            options.add_argument('--headless')  # 无界面模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            if service:
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.implicitly_wait(10)
            # 隐藏webdriver特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            print(f"初始化Chrome WebDriver失败: {e}")
            print("将使用普通HTTP请求，不进行JavaScript渲染")
            self.driver = None
    
    def process_request(self, request, spider):
        """处理请求，对需要JS渲染的页面使用Selenium"""
        if not self.driver:
            return None
        
        render_js = request.meta.get('render_js', False)
        if not render_js:
            return None
        
        try:
            spider.logger.info(f"使用Selenium渲染: {request.url}")
            
            # 使用Selenium获取页面
            self.driver.get(request.url)
            
            # 等待页面加载完成
            time.sleep(3)
            
            # 等待特定元素加载（可选）
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            # 获取渲染后的HTML
            html = self.driver.page_source
            
            # 创建响应对象
            response = HtmlResponse(
                url=request.url,
                body=html.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            
            return response
            
        except Exception as e:
            spider.logger.error(f"Selenium渲染失败 {request.url}: {e}")
            return None
    
    def spider_closed(self, spider):
        """爬虫关闭时清理资源"""
        if self.driver:
            self.driver.quit()


class DuplicateFilterMiddleware:
    """去重中间件"""
    
    def __init__(self):
        self.db = UrlDatabase()
    
    def process_request(self, request, spider):
        """检查请求是否重复"""
        url = request.url
        
        # 检查URL是否已经抓取过
        if self.db.is_crawled(url):
            spider.logger.info(f"URL已抓取过，跳过: {url}")
            raise IgnoreRequest(f"URL已抓取过: {url}")
        
        # 标记URL为正在抓取
        self.db.mark_crawling(url)
        
        return None


class RetryMiddleware:
    """重试中间件"""
    
    def __init__(self, max_retries=3, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def process_response(self, request, response, spider):
        """处理响应"""
        if response.status >= 400:
            retries = request.meta.get('retry_times', 0)
            if retries < self.max_retries:
                spider.logger.warning(f"HTTP {response.status}，重试 {retries + 1}/{self.max_retries}: {request.url}")
                new_request = request.copy()
                new_request.meta['retry_times'] = retries + 1
                new_request.dont_filter = True
                return new_request
            else:
                spider.logger.error(f"重试失败，放弃: {request.url}")
        
        return response
    
    def process_exception(self, request, exception, spider):
        """处理异常"""
        retries = request.meta.get('retry_times', 0)
        if retries < self.max_retries:
            spider.logger.warning(f"请求异常，重试 {retries + 1}/{self.max_retries}: {request.url}")
            new_request = request.copy()
            new_request.meta['retry_times'] = retries + 1
            new_request.dont_filter = True
            return new_request
        else:
            spider.logger.error(f"重试失败，放弃: {request.url}")
            return None
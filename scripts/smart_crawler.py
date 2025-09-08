#!/usr/bin/env python3
"""
智能网页爬虫脚本
自动检测网页是否需要JavaScript渲染，只对需要JS的网页启用渲染
"""

import os
import sys
import time
import requests
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase
from webspider.config import DatabaseConfig

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("警告: Selenium未安装，JavaScript渲染功能不可用")


class SmartCrawler:
    """智能网页爬虫"""
    
    def __init__(self, output_dir='webpages', workers=5, timeout=30, 
                 enable_js_detection=True, js_workers=2):
        """
        初始化智能爬虫
        
        Args:
            output_dir: 输出目录
            workers: 并发线程数
            timeout: 请求超时时间（秒）
            enable_js_detection: 是否启用JS需求检测
            js_workers: JavaScript渲染工作线程数
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.timeout = timeout
        self.enable_js_detection = enable_js_detection
        self.js_workers = js_workers
        self.db = UrlDatabase()
        self.webdriver_pool = None
        
        # 检查Selenium是否可用
        if not SELENIUM_AVAILABLE:
            print("警告: Selenium不可用，无法进行JavaScript渲染")
            self.enable_js_detection = False
        
        # 初始化WebDriver池（如果启用JS检测）
        if self.enable_js_detection and SELENIUM_AVAILABLE:
            self.webdriver_pool = WebDriverPool(pool_size=self.js_workers, timeout=self.timeout)
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"智能爬虫初始化完成:")
        print(f"  输出目录: {self.output_dir}")
        print(f"  并发数: {self.workers}")
        print(f"  超时时间: {self.timeout}秒")
        print(f"  JS检测: {'启用' if self.enable_js_detection else '禁用'}")
        if self.enable_js_detection:
            print(f"  JS工作线程数: {self.js_workers}")
    
    def needs_javascript_rendering(self, url, html_content):
        """
        检测网页是否需要JavaScript渲染
        
        Args:
            url: 网页URL
            html_content: HTML内容
            
        Returns:
            bool: 是否需要JavaScript渲染
        """
        if not self.enable_js_detection:
            return False
        
        # 检查常见的需要JS渲染的特征
        js_indicators = [
            # 检查script标签中的现代框架
            r'<script[^>]*src[^>]*react',
            r'<script[^>]*src[^>]*vue',
            r'<script[^>]*src[^>]*angular',
            r'<script[^>]*src[^>]*backbone',
            
            # 检查内联脚本中的现代框架
            r'ReactDOM\.render',
            r'new\s+Vue\(',
            r'angular\.module\(',
            
            # 检查常见的SPA特征
            r'<noscript>',
            r'<app-root>',
            r'<react-root>',
            r'<div[^>]*id=["\']app["\']',
            r'<div[^>]*id=["\']root["\']',
            
            # 检查AJAX加载内容的迹象
            r'data-src=',
            r'loading=["\']lazy["\']',
            
            # 检查空的内容区域（可能是JS填充的）
            r'<div[^>]*class=["\'][^"\']*container[^"\']*["\'][^>]*>\s*</div>',
            r'<div[^>]*id=["\'][^"\']*content[^"\']*["\'][^>]*>\s*</div>',
        ]
        
        # 检查HTML内容是否包含JS渲染指示器
        for pattern in js_indicators:
            if re.search(pattern, html_content, re.IGNORECASE):
                print(f"检测到需要JS渲染的特征: {pattern}")
                return True
        
        # 检查是否有大量空的或占位符内容
        if self.has_placeholder_content(html_content):
            print("检测到占位符内容，可能需要JS渲染")
            return True
        
        # 检查URL模式
        js_url_patterns = [
            r'/spa/',
            r'/app/',
            r'/dashboard/',
            r'/admin/',
        ]
        
        for pattern in js_url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                print(f"URL模式表明需要JS渲染: {pattern}")
                return True
        
        return False
    
    def has_placeholder_content(self, html_content):
        """
        检查HTML是否包含占位符内容（可能是JS填充的）
        
        Args:
            html_content: HTML内容
            
        Returns:
            bool: 是否包含占位符内容
        """
        # 移除script和style标签后检查内容
        content_without_scripts = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 检查是否有大量空的div或其他元素
        empty_elements = re.findall(r'<(div|section|article)[^>]*>\s*</\1>', content_without_scripts, re.IGNORECASE)
        
        # 检查是否有加载指示器
        loading_indicators = [
            r'loading',
            r'loader',
            r'spinner',
            r'正在加载',
            r'加载中',
        ]
        
        has_loading = any(re.search(pattern, content_without_scripts, re.IGNORECASE) 
                         for pattern in loading_indicators)
        
        # 如果有很多空元素或有加载指示器，则可能是占位符内容
        return len(empty_elements) > 10 or has_loading
    
    def get_pending_urls(self, limit=None):
        """获取待抓取的URL列表"""
        try:
            urls = self.db.get_pending_urls(limit or 1000)
            return [url_info[0] for url_info in urls]  # 只需要URL字符串
        except Exception as e:
            print(f"获取待抓取URL失败: {e}")
            return []
    
    def sanitize_filename(self, url):
        """将URL转换为安全的文件名"""
        parsed = urlparse(url)
        # 使用域名和路径作为文件名基础
        domain = parsed.netloc.replace(':', '_')
        path = parsed.path.strip('/')
        
        if path:
            # 替换不安全的字符
            safe_path = path.replace('/', '_').replace('\\', '_')
            filename = f"{domain}_{safe_path}"
        else:
            filename = domain
            
        # 限制文件名长度
        if len(filename) > 150:
            filename = filename[:150]
            
        return filename
    
    def save_webpage(self, url, content, rendered=False):
        """保存网页内容到文件"""
        try:
            # 生成安全的文件名
            filename = self.sanitize_filename(url)
            if rendered:
                filename += "_js"
            filepath = self.output_dir / f"{filename}.html"
            
            # 如果文件已存在，添加序号
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                filepath = self.output_dir / f"{original_filepath.stem}_{counter}{original_filepath.suffix}"
                counter += 1
            
            # 保存内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            render_status = " (JS渲染)" if rendered else ""
            print(f"已保存: {url}{render_status} -> {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"保存网页失败 {url}: {e}")
            return None
    
    def fetch_url_with_requests(self, url, worker_id=0):
        """使用requests获取URL内容"""
        try:
            print(f"[Worker-{worker_id}] 开始抓取: {url}")
            
            # 发送HTTP请求
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 检查响应状态
            if response.status_code == 200:
                html_content = response.text
                
                # 检测是否需要JavaScript渲染
                needs_js = self.needs_javascript_rendering(url, html_content)
                
                if needs_js and self.enable_js_detection and self.webdriver_pool:
                    print(f"[Worker-{worker_id}] 检测到需要JS渲染: {url}")
                    # 使用Selenium重新抓取
                    return self.fetch_url_with_selenium(url, worker_id, fallback_html=html_content)
                else:
                    # 保存网页内容
                    filepath = self.save_webpage(url, html_content, rendered=False)
                    
                    if filepath:
                        # 更新数据库状态为成功
                        self.db.mark_success(url, html_file_path=filepath)
                        print(f"[Worker-{worker_id}] 完成抓取: {url}")
                        return True
                    else:
                        # 保存失败，标记为失败
                        self.db.mark_failed(url, "保存文件失败")
                        print(f"[Worker-{worker_id}] 保存失败: {url}")
                        return False
            else:
                # HTTP错误，标记为失败
                error_msg = f"HTTP {response.status_code}"
                self.db.mark_failed(url, error_msg)
                print(f"[Worker-{worker_id}] HTTP错误 {response.status_code}: {url}")
                return False
                
        except requests.exceptions.Timeout:
            error_msg = f"请求超时 ({self.timeout}秒)"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] 超时: {url}")
            return False
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] 请求异常: {url} - {e}")
            return False
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] 未知错误: {url} - {e}")
            return False
    
    def fetch_url_with_selenium(self, url, worker_id=0, fallback_html=None):
        """使用Selenium获取URL内容（支持JavaScript渲染）"""
        driver = None
        try:
            print(f"[Worker-{worker_id}] 开始JS渲染抓取: {url}")
            
            # 从池中获取WebDriver
            driver = self.webdriver_pool.get_driver(timeout=10)
            if not driver:
                # 如果无法获取WebDriver，使用回退HTML或普通请求
                if fallback_html:
                    filepath = self.save_webpage(url, fallback_html, rendered=False)
                    if filepath:
                        self.db.mark_success(url, html_file_path=filepath)
                        print(f"[Worker-{worker_id}] 使用回退内容: {url}")
                        return True
                print(f"[Worker-{worker_id}] 无法获取WebDriver: {url}")
                return False
            
            # 设置页面加载超时
            driver.set_page_load_timeout(min(self.timeout, 30))
            
            # 访问页面
            driver.get(url)
            
            # 等待页面加载完成
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                pass
            
            # 获取渲染后的HTML
            html_content = driver.page_source
            
            # 保存网页内容
            filepath = self.save_webpage(url, html_content, rendered=True)
            
            if filepath:
                # 更新数据库状态为成功
                self.db.mark_success(url, html_file_path=filepath)
                print(f"[Worker-{worker_id}] 完成JS渲染抓取: {url}")
                return True
            else:
                # 保存失败，标记为失败
                self.db.mark_failed(url, "保存文件失败")
                print(f"[Worker-{worker_id}] JS渲染保存失败: {url}")
                return False
                
        except TimeoutException:
            error_msg = f"页面加载超时 ({min(self.timeout, 30)}秒)"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] JS渲染超时: {url}")
            return False
        except WebDriverException as e:
            error_msg = f"WebDriver异常: {str(e)}"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] WebDriver异常: {url} - {e}")
            return False
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] JS渲染未知错误: {url} - {e}")
            return False
        finally:
            # 将WebDriver返回到池中
            if driver:
                self.webdriver_pool.return_driver(driver)
    
    def fetch_url(self, url, worker_id=0):
        """获取单个URL的内容"""
        return self.fetch_url_with_requests(url, worker_id)
    
    def crawl_urls(self, urls):
        """多线程抓取URL列表"""
        if not urls:
            print("没有URL需要抓取")
            return 0
        
        print(f"开始抓取 {len(urls)} 个URL，使用 {self.workers} 个线程")
        print("-" * 60)
        
        # 记录开始时间
        start_time = time.time()
        successful_count = 0
        failed_count = 0
        
        # 使用线程池执行抓取任务
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # 提交任务
            future_to_url = {
                executor.submit(self.fetch_url, url, i+1): url 
                for i, url in enumerate(urls)
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        successful_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"执行异常 {url}: {e}")
        
        # 显示统计信息
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("抓取任务完成统计")
        print("=" * 60)
        print(f"总URL数:     {len(urls)}")
        print(f"成功完成:    {successful_count}")
        print(f"失败:        {failed_count}")
        print(f"总耗时:      {elapsed_time:.1f} 秒")
        
        if len(urls) > 0:
            success_rate = (successful_count / len(urls)) * 100
            print(f"成功率:      {success_rate:.1f}%")
        
        return successful_count
    
    def print_stats(self):
        """打印数据库统计信息"""
        try:
            stats = self.db.get_stats()
            print("\n数据库统计信息:")
            print(f"  总URL数:    {stats['total']}")
            print(f"  待抓取:     {stats['pending']}")
            print(f"  抓取成功:   {stats['success']}")
            print(f"  抓取失败:   {stats['failed']}")
            print(f"  正在抓取:   {stats['crawling']}")
        except Exception as e:
            print(f"获取统计信息失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self.webdriver_pool:
            self.webdriver_pool.close_all()


class WebDriverPool:
    """WebDriver池管理类"""
    
    def __init__(self, pool_size=2, timeout=30):
        self.pool_size = pool_size
        self.timeout = timeout
        from queue import Queue
        self.pool = Queue(maxsize=pool_size)
        import threading
        self.lock = threading.Lock()
        self.active_drivers = 0
        self.max_drivers = pool_size
        
    def _create_driver(self):
        """创建WebDriver实例"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # 禁用Google服务连接，减少错误日志
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-translate')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-default-apps')
            options.add_argument('--no-first-run')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 创建WebDriver实例
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(5)
            
            # 隐藏webdriver特征
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            with self.lock:
                self.active_drivers += 1
            
            return driver
        except Exception as e:
            print(f"初始化Chrome WebDriver失败: {e}")
            return None
    
    def get_driver(self, timeout=30):
        """从池中获取WebDriver实例"""
        try:
            return self.pool.get(block=False)
        except:
            with self.lock:
                if self.active_drivers < self.max_drivers:
                    return self._create_driver()
            try:
                return self.pool.get(block=True, timeout=timeout)
            except:
                return None
    
    def return_driver(self, driver):
        """将WebDriver实例返回到池中"""
        if driver:
            try:
                driver.execute_script("window.stop();")
                self.pool.put_nowait(driver)
            except:
                self.close_driver(driver)
    
    def close_driver(self, driver):
        """关闭WebDriver实例"""
        if driver:
            try:
                driver.quit()
            except:
                pass
            with self.lock:
                self.active_drivers = max(0, self.active_drivers - 1)
    
    def close_all(self):
        """关闭所有WebDriver实例"""
        while True:
            try:
                driver = self.pool.get(block=False)
                self.close_driver(driver)
            except:
                break
        
        with self.lock:
            self.active_drivers = 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能网页爬虫（自动检测JS需求）')
    parser.add_argument('--limit', '-l', type=int, default=100,
                       help='抓取URL数量限制（默认100）')
    parser.add_argument('--workers', '-w', type=int, default=5,
                       help='并发线程数（默认5）')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                       help='请求超时时间（秒，默认30）')
    parser.add_argument('--js-workers', type=int, default=2,
                       help='JavaScript渲染工作线程数（默认2）')
    parser.add_argument('--output', '-o', default='webpages',
                       help='输出目录（默认webpages）')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='只显示统计信息，不抓取网页')
    parser.add_argument('--url', '-u', action='append',
                       help='指定要抓取的URL（可多次使用）')
    parser.add_argument('--disable-js-detection', action='store_true',
                       help='禁用JavaScript需求检测')
    
    args = parser.parse_args()
    
    # 创建爬虫实例
    crawler = SmartCrawler(
        output_dir=args.output,
        workers=args.workers,
        timeout=args.timeout,
        enable_js_detection=not args.disable_js_detection,
        js_workers=args.js_workers
    )
    
    try:
        if args.stats:
            # 只显示统计信息
            crawler.print_stats()
            return
        
        # 获取要抓取的URL列表
        if args.url:
            # 使用命令行指定的URL
            urls = args.url
            print(f"使用命令行指定的 {len(urls)} 个URL")
        else:
            # 从数据库获取待抓取的URL
            urls = crawler.get_pending_urls(args.limit)
            print(f"从数据库获取了 {len(urls)} 个待抓取URL")
        
        if not urls:
            print("没有找到需要抓取的URL")
            return
        
        # 显示抓取计划
        print("\n抓取计划:")
        for i, url in enumerate(urls[:10], 1):
            print(f"  {i}. {url}")
        if len(urls) > 10:
            print(f"  ... 还有 {len(urls) - 10} 个URL")
        print()
        
        # 开始抓取
        successful_count = crawler.crawl_urls(urls)
        
        # 显示最终统计
        crawler.print_stats()
        
        # 返回状态码
        sys.exit(0 if successful_count > 0 else 1)
    
    finally:
        # 清理资源
        crawler.cleanup()


if __name__ == '__main__':
    main()
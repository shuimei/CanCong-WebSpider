#!/usr/bin/env python3
"""
优化的网页爬虫脚本（支持JavaScript渲染）
通过复用WebDriver实例来提高JavaScript渲染性能
"""

import os
import sys
import time
import requests
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from queue import Queue, Empty
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


class WebDriverPool:
    """WebDriver池管理类"""
    
    def __init__(self, pool_size=2, timeout=30):
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.active_drivers = 0
        self.max_drivers = pool_size
        
    def _create_driver(self):
        """创建WebDriver实例"""
        try:
            options = Options()
            options.add_argument('--headless')  # 无界面模式
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
            driver.implicitly_wait(5)  # 减少隐式等待时间
            
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
            # 尝试从池中获取现有的WebDriver
            return self.pool.get(block=False)
        except Empty:
            # 池中没有可用的WebDriver，尝试创建新的
            with self.lock:
                if self.active_drivers < self.max_drivers:
                    return self._create_driver()
            # 如果已达到最大驱动数，等待池中的WebDriver
            try:
                return self.pool.get(block=True, timeout=timeout)
            except Empty:
                return None
    
    def return_driver(self, driver):
        """将WebDriver实例返回到池中"""
        if driver:
            try:
                # 清理页面状态但不关闭浏览器
                driver.execute_script("window.stop();")
                # 将WebDriver放回池中
                self.pool.put_nowait(driver)
            except:
                # 如果无法放回池中，关闭WebDriver
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
            except Empty:
                break
        
        # 确保所有活动的驱动都被关闭
        with self.lock:
            self.active_drivers = 0


class OptimizedCrawlerJS:
    """优化的网页爬虫（支持JavaScript渲染）"""
    
    def __init__(self, output_dir='webpages', workers=3, timeout=30, enable_js=False, js_workers=2):
        """
        初始化优化爬虫
        
        Args:
            output_dir: 输出目录
            workers: 并发线程数
            timeout: 请求超时时间（秒）
            enable_js: 是否启用JavaScript渲染
            js_workers: JavaScript渲染的工作线程数（WebDriver池大小）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.timeout = timeout
        self.enable_js = enable_js and SELENIUM_AVAILABLE
        self.js_workers = min(js_workers, workers)  # WebDriver池大小不超过总工作线程数
        self.db = UrlDatabase()
        self.webdriver_pool = None
        
        # 检查是否启用了JavaScript渲染
        if enable_js and not SELENIUM_AVAILABLE:
            print("警告: 无法启用JavaScript渲染，因为Selenium不可用")
            self.enable_js = False
        
        # 初始化WebDriver池（如果启用JS渲染）
        if self.enable_js:
            self.webdriver_pool = WebDriverPool(pool_size=self.js_workers, timeout=self.timeout)
        
        # 请求头（用于requests）
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"优化爬虫初始化完成:")
        print(f"  输出目录: {self.output_dir}")
        print(f"  并发数: {self.workers}")
        print(f"  超时时间: {self.timeout}秒")
        print(f"  JavaScript渲染: {'启用' if self.enable_js else '禁用'}")
        if self.enable_js:
            print(f"  JS工作线程数: {self.js_workers}")
    
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
    
    def save_webpage(self, url, content):
        """保存网页内容到文件"""
        try:
            # 生成安全的文件名
            filename = self.sanitize_filename(url)
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
            
            print(f"已保存: {url} -> {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"保存网页失败 {url}: {e}")
            return None
    
    def fetch_url_with_requests(self, url, worker_id=0):
        """使用requests获取URL内容（无JavaScript渲染）"""
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
                # 保存网页内容
                filepath = self.save_webpage(url, response.text)
                
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
    
    def fetch_url_with_selenium(self, url, worker_id=0):
        """使用Selenium获取URL内容（支持JavaScript渲染）"""
        driver = None
        try:
            print(f"[Worker-{worker_id}] 开始抓取 (JS渲染): {url}")
            
            # 从池中获取WebDriver
            driver = self.webdriver_pool.get_driver(timeout=10)
            if not driver:
                # 如果无法获取WebDriver，回退到requests
                print(f"[Worker-{worker_id}] 无法获取WebDriver，回退到普通请求: {url}")
                return self.fetch_url_with_requests(url, worker_id)
            
            # 设置页面加载超时
            driver.set_page_load_timeout(min(self.timeout, 30))  # 限制页面加载超时为30秒以内
            
            # 访问页面
            driver.get(url)
            
            # 等待页面加载完成（减少等待时间）
            try:
                WebDriverWait(driver, 5).until(  # 减少等待时间到5秒
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                pass  # 即使超时也继续，获取已加载的内容
            
            # 获取渲染后的HTML
            html_content = driver.page_source
            
            # 保存网页内容
            filepath = self.save_webpage(url, html_content)
            
            if filepath:
                # 更新数据库状态为成功
                self.db.mark_success(url, html_file_path=filepath)
                print(f"[Worker-{worker_id}] 完成抓取 (JS渲染): {url}")
                return True
            else:
                # 保存失败，标记为失败
                self.db.mark_failed(url, "保存文件失败")
                print(f"[Worker-{worker_id}] 保存失败 (JS渲染): {url}")
                return False
                
        except TimeoutException:
            error_msg = f"页面加载超时 ({min(self.timeout, 30)}秒)"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] 页面加载超时 (JS渲染): {url}")
            return False
        except WebDriverException as e:
            error_msg = f"WebDriver异常: {str(e)}"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] WebDriver异常 (JS渲染): {url} - {e}")
            return False
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            self.db.mark_failed(url, error_msg)
            print(f"[Worker-{worker_id}] 未知错误 (JS渲染): {url} - {e}")
            return False
        finally:
            # 将WebDriver返回到池中
            if driver:
                self.webdriver_pool.return_driver(driver)
    
    def fetch_url(self, url, worker_id=0):
        """获取单个URL的内容"""
        if self.enable_js:
            return self.fetch_url_with_selenium(url, worker_id)
        else:
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='优化的网页爬虫（支持JavaScript渲染）')
    parser.add_argument('--limit', '-l', type=int, default=100,
                       help='抓取URL数量限制（默认100）')
    parser.add_argument('--workers', '-w', type=int, default=3,
                       help='并发线程数（默认3）')
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
    parser.add_argument('--enable-js', action='store_true',
                       help='启用JavaScript渲染')
    
    args = parser.parse_args()
    
    # 创建爬虫实例
    crawler = OptimizedCrawlerJS(
        output_dir=args.output,
        workers=args.workers,
        timeout=args.timeout,
        enable_js=args.enable_js,
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
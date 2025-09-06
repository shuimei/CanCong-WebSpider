#!/usr/bin/env python3
"""
多URL爬虫运行脚本
支持多个起始URL、多进程并发和JavaScript渲染
专为Web界面调用优化
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from webspider.database import UrlDatabase
from webspider.spiders.webspider import WebSpider


class MultiCrawlerRunner:
    """多URL爬虫运行器"""
    
    def __init__(self, database_path: str, output_dir: str, workers: int = 2):
        self.database_path = database_path
        self.output_dir = output_dir
        self.workers = workers
        self.db = UrlDatabase(database_path)
        
        # 确保输出目录存在
        Path(output_dir).mkdir(exist_ok=True)
        
        print(f"初始化爬虫运行器:")
        print(f"  数据库路径: {database_path}")
        print(f"  输出目录: {output_dir}")
        print(f"  并发数: {workers}")
    
    def run_single_crawler(self, start_url: str, max_depth: int = 3, 
                          enable_js: bool = False, worker_id: int = 0):
        """运行单个爬虫实例"""
        try:
            print(f"[Worker-{worker_id}] 开始抓取: {start_url}")
            
            # 配置Scrapy设置
            settings = get_project_settings()
            settings.set('DOWNLOAD_DELAY', 1.5)  # 稍微减少延迟以提高效率
            settings.set('CONCURRENT_REQUESTS', 2)  # 每个进程内部并发
            settings.set('WEBPAGES_DIR', self.output_dir)
            settings.set('DATABASE_URL', self.database_path)
            
            # 设置USER_AGENT
            settings.set('USER_AGENT', f'WebCrawler-Worker-{worker_id} (+http://www.example.com/bot)')
            
            # 启用管道
            settings.set('ITEM_PIPELINES', {
                'webspider.pipelines.UrlFilterPipeline': 300,
                'webspider.pipelines.HtmlSavePipeline': 400,
                'webspider.pipelines.StatisticsPipeline': 500,
            })
            
            # JavaScript渲染配置
            if enable_js:
                print(f"[Worker-{worker_id}] JavaScript渲染已启用")
                # 这里可以添加Selenium相关配置
            
            # 启动爬虫
            process = CrawlerProcess(settings)
            process.crawl(
                WebSpider, 
                start_url=start_url, 
                max_depth=max_depth, 
                enable_keyword_filter=True
            )
            process.start()
            
            print(f"[Worker-{worker_id}] 完成抓取: {start_url}")
            return True
            
        except Exception as e:
            print(f"[Worker-{worker_id}] 抓取失败 {start_url}: {e}")
            return False
    
    def run_multi_crawlers(self, start_urls: list, max_depth: int = 3, enable_js: bool = False):
        """运行多个爬虫实例"""
        if not start_urls:
            print("错误: 没有提供起始URL")
            return False
        
        print(f"开始多进程抓取，共 {len(start_urls)} 个URL，{self.workers} 个worker")
        print("-" * 60)
        
        # 记录起始时间
        start_time = time.time()
        
        # 显示抓取计划
        for i, url in enumerate(start_urls):
            print(f"  {i+1}. {url}")
        print("-" * 60)
        
        successful_count = 0
        failed_count = 0
        
        # 使用线程池执行多个爬虫
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # 提交任务
            future_to_url = {}
            for i, url in enumerate(start_urls):
                future = executor.submit(
                    self.run_single_crawler, 
                    url, 
                    max_depth, 
                    enable_js, 
                    i + 1
                )
                future_to_url[future] = url
            
            # 收集结果
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        successful_count += 1
                        print(f"✓ 成功完成: {url}")
                    else:
                        failed_count += 1
                        print(f"✗ 抓取失败: {url}")
                except Exception as e:
                    failed_count += 1
                    print(f"✗ 执行异常: {url} - {e}")
        
        # 显示最终统计
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("抓取任务完成统计")
        print("=" * 60)
        print(f"总URL数:     {len(start_urls)}")
        print(f"成功完成:    {successful_count}")
        print(f"失败:        {failed_count}")
        print(f"总耗时:      {elapsed_time:.1f} 秒")
        
        if len(start_urls) > 0:
            success_rate = (successful_count / len(start_urls)) * 100
            print(f"成功率:      {success_rate:.1f}%")
        
        # 显示数据库统计
        print("\n数据库统计信息:")
        self.show_database_stats()
        
        return successful_count > 0
    
    def show_database_stats(self):
        """显示数据库统计信息"""
        try:
            stats = self.db.get_stats()
            print(f"  数据库总URL: {stats['total']}")
            print(f"  待抓取:      {stats['pending']}")
            print(f"  成功:        {stats['success']}")
            print(f"  失败:        {stats['failed']}")
            print(f"  进行中:      {stats['crawling']}")
        except Exception as e:
            print(f"  获取数据库统计失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='多URL网页爬虫程序')
    parser.add_argument('--url', action='append', help='起始URL地址（可多次使用）')
    parser.add_argument('--urls-file', help='包含URL列表的文件路径')
    parser.add_argument('--depth', '-d', type=int, default=3, help='最大抓取深度 (默认: 3)')
    parser.add_argument('--workers', '-w', type=int, default=2, 
                       help='并发worker数 (默认: 2, 范围: 1-10)')
    parser.add_argument('--output', '-o', default='webpages', help='输出目录 (默认: webpages)')
    parser.add_argument('--database', '--db', default='spider_urls.db', 
                       help='数据库文件 (默认: spider_urls.db)')
    parser.add_argument('--enable-js', action='store_true', help='启用JavaScript渲染')
    parser.add_argument('--stats', action='store_true', help='显示统计信息后退出')
    parser.add_argument('--clean', action='store_true', help='清理数据库中长时间未完成的任务')
    
    args = parser.parse_args()
    
    # 验证workers参数
    if args.workers < 1 or args.workers > 10:
        print(f"错误: workers数量必须在1-10之间，当前值: {args.workers}")
        return 1
    
    # 初始化数据库
    db = UrlDatabase(args.database)
    
    # 处理特殊命令
    if args.stats:
        show_database_stats(db)
        return 0
    
    if args.clean:
        count = db.cleanup_stale_crawling()
        print(f"已清理 {count} 个长时间未完成的任务")
        show_database_stats(db)
        return 0
    
    # 获取URL列表
    start_urls = []
    
    if args.url:
        start_urls.extend(args.url)
    
    if args.urls_file:
        try:
            with open(args.urls_file, 'r', encoding='utf-8') as f:
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                start_urls.extend(file_urls)
        except FileNotFoundError:
            print(f"错误: 找不到URL文件: {args.urls_file}")
            return 1
        except Exception as e:
            print(f"错误: 读取URL文件失败: {e}")
            return 1
    
    if not start_urls:
        print("错误: 必须提供至少一个起始URL")
        print("使用 --url URL 或 --urls-file FILE 来指定URL")
        parser.print_help()
        return 1
    
    # 去重并验证URL
    unique_urls = []
    for url in start_urls:
        if url not in unique_urls:
            if url.startswith('http://') or url.startswith('https://'):
                unique_urls.append(url)
            else:
                print(f"警告: 跳过无效URL: {url}")
    
    if not unique_urls:
        print("错误: 没有有效的URL")
        return 1
    
    print(f"配置信息:")
    print(f"  URL数量: {len(unique_urls)}")
    print(f"  最大深度: {args.depth}")
    print(f"  Worker数: {args.workers}")
    print(f"  输出目录: {args.output}")
    print(f"  JavaScript渲染: {args.enable_js}")
    print("")
    
    # 创建并运行爬虫
    try:
        runner = MultiCrawlerRunner(args.database, args.output, args.workers)
        success = runner.run_multi_crawlers(unique_urls, args.depth, args.enable_js)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n用户中断，正在停止爬虫...")
        return 1
    except Exception as e:
        print(f"爬虫运行出错: {e}")
        return 1


def show_database_stats(db):
    """显示数据库统计信息"""
    stats = db.get_stats()
    
    print("=" * 40)
    print("数据库统计信息")
    print("=" * 40)
    print(f"总URL数:    {stats['total']}")
    print(f"待抓取:     {stats['pending']}")
    print(f"抓取成功:   {stats['success']}")
    print(f"抓取失败:   {stats['failed']}")
    print(f"正在抓取:   {stats['crawling']}")
    print("=" * 40)


if __name__ == "__main__":
    sys.exit(main())
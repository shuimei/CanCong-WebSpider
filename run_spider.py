#!/usr/bin/env python3
"""
网页爬虫主运行脚本
支持JavaScript渲染、URL去重和状态管理
"""

import os
import sys
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from webspider.database import UrlDatabase
from webspider.spiders.webspider import WebSpider


def get_random_pending_url(db):
    """从数据库获取随机待抓取URL"""
    return db.get_random_pending_url()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网页爬虫程序')
    parser.add_argument('url', nargs='?', help='起始URL地址')
    parser.add_argument('--depth', '-d', type=int, default=2, help='最大抓取深度 (默认: 2)')
    parser.add_argument('--delay', type=float, default=2, help='请求延迟秒数 (默认: 2)')
    parser.add_argument('--concurrent', '-c', type=int, default=4, help='并发请求数 (默认: 4)')
    parser.add_argument('--output', '-o', default='webpages', help='输出目录 (默认: webpages)')
    parser.add_argument('--database', '--db', default='spider_urls.db', help='数据库文件 (默认: spider_urls.db)')
    parser.add_argument('--stats', action='store_true', help='显示统计信息后退出')
    parser.add_argument('--clean', action='store_true', help='清理数据库中长时间未完成的任务')
    parser.add_argument('--reset', action='store_true', help='重置数据库')
    parser.add_argument('--random', '-r', action='store_true', help='从数据库中随机选择一个待抓取的URL开始')
    parser.add_argument('--no-filter', action='store_true', help='禁用关键词过滤，抓取所有页面')
    parser.add_argument('--keyword-filter', action='store_true', default=True, help='启用关键词过滤（默认启用）')
    
    args = parser.parse_args()
    
    # 初始化数据库
    db = UrlDatabase(args.database)
    
    # 处理特殊命令
    if args.stats:
        show_statistics(db)
        return
    
    if args.clean:
        clean_stale_tasks(db)
        return
    
    if args.reset:
        reset_database(args.database)
        return
    
    # 处理随机选择URL
    start_url = args.url
    if args.random:
        random_url_info = get_random_pending_url(db)
        if random_url_info:
            start_url = random_url_info[0]
            print(f"从数据库中随机选择URL: {start_url}")
        else:
            if not start_url:
                print("错误: 数据库中没有待抓取的URL，且未提供起始URL")
                print("请先使用普通模式添加一些URL，或者提供一个起始URL")
                return
            print("数据库中没有待抓取的URL，使用提供的起始URL")
    elif not start_url:
        print("错误: 必须提供起始URL或使用 --random 选项")
        parser.print_help()
        return
    
    # 确保输出目录存在
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # 配置Scrapy设置
    settings = get_project_settings()
    settings.set('DOWNLOAD_DELAY', args.delay)
    settings.set('CONCURRENT_REQUESTS', args.concurrent)
    settings.set('WEBPAGES_DIR', args.output)
    settings.set('DATABASE_URL', args.database)
    
    # 启用统计管道
    settings.set('ITEM_PIPELINES', {
        'webspider.pipelines.UrlFilterPipeline': 300,
        'webspider.pipelines.HtmlSavePipeline': 400,
        'webspider.pipelines.StatisticsPipeline': 500,
    })
    
    # 判断是否启用关键词过滤
    enable_keyword_filter = not args.no_filter
    
    print(f"开始爬取: {start_url}")
    print(f"最大深度: {args.depth}")
    print(f"输出目录: {args.output}")
    print(f"数据库文件: {args.database}")
    print(f"关键词过滤: {'\u542f\u7528' if enable_keyword_filter else '\u7981\u7528'}")
    if enable_keyword_filter:
        print("过滤规则: 只抓取与矿山、自然资源、地质相关的网页")
    if args.random:
        print("模式: 随机选择待抓取URL")
    print("-" * 50)
    
    # 启动爬虫
    try:
        process = CrawlerProcess(settings)
        process.crawl(WebSpider, start_url=start_url, max_depth=args.depth, enable_keyword_filter=enable_keyword_filter)
        process.start()
    except KeyboardInterrupt:
        print("\n用户中断，正在停止爬虫...")
    except Exception as e:
        print(f"爬虫运行出错: {e}")
    finally:
        # 显示最终统计
        print("\n最终统计信息:")
        show_statistics(db)


def show_statistics(db):
    """显示统计信息"""
    stats = db.get_stats()
    
    print("=" * 40)
    print("爬虫统计信息")
    print("=" * 40)
    print(f"总URL数:    {stats['total']}")
    print(f"待抓取:     {stats['pending']}")
    print(f"抓取成功:   {stats['success']}")
    print(f"抓取失败:   {stats['failed']}")
    print(f"正在抓取:   {stats['crawling']}")
    print("=" * 40)
    
    if stats['total'] > 0:
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"成功率:     {success_rate:.1f}%")
    
    # 显示最近的一些URL
    import sqlite3
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        print("\n最近成功抓取的URL:")
        cursor.execute('''
            SELECT url, title, crawled_time FROM urls 
            WHERE status = 'success' 
            ORDER BY crawled_time DESC 
            LIMIT 5
        ''')
        
        for url, title, crawled_time in cursor.fetchall():
            title = title or "无标题"
            print(f"  {url[:60]}... - {title[:30]}")
        
        print("\n最近失败的URL:")
        cursor.execute('''
            SELECT url, error_message FROM urls 
            WHERE status = 'failed' 
            ORDER BY crawled_time DESC 
            LIMIT 5
        ''')
        
        for url, error_message in cursor.fetchall():
            error_message = error_message or "未知错误"
            print(f"  {url[:60]}... - {error_message[:30]}")


def clean_stale_tasks(db):
    """清理长时间未完成的任务"""
    count = db.cleanup_stale_crawling()
    print(f"已清理 {count} 个长时间未完成的任务")
    show_statistics(db)


def reset_database(db_path):
    """重置数据库"""
    import sqlite3
    
    confirm = input("确定要重置数据库吗？这将删除所有数据 (y/N): ")
    if confirm.lower() != 'y':
        print("取消重置")
        return
    
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # 重新初始化数据库
        db = UrlDatabase(db_path)
        print("数据库已重置")
        
    except Exception as e:
        print(f"重置数据库失败: {e}")


def run_interactive():
    """交互式运行模式"""
    print("网页爬虫 - 交互式模式")
    print("=" * 30)
    
    # 初始化数据库查看待抓取URL
    db = UrlDatabase('spider_urls.db')
    stats = db.get_stats()
    
    if stats['pending'] > 0:
        print(f"数据库中有 {stats['pending']} 个待抓取的URL")
        choice = input("是否使用随机选择模式? (y/N): ").strip().lower()
        if choice == 'y':
            # 随机选择模式
            random_url_info = get_random_pending_url(db)
            if random_url_info:
                print(f"随机选择URL: {random_url_info[0]}")
                
                try:
                    depth = int(input("最大抓取深度 (默认2): ") or "2")
                    delay = float(input("请求延迟秒数 (默认2): ") or "2")
                except ValueError:
                    print("输入无效，使用默认值")
                    depth = 2
                    delay = 2
                
                # 构建命令行参数
                sys.argv = ['spider.py', '--random', '--depth', str(depth), '--delay', str(delay)]
                print(f"\n开始随机抓取...")
                main()
                return
    
    while True:
        try:
            url = input("\n请输入要爬取的URL (输入 'quit' 退出): ").strip()
            
            if url.lower() in ['quit', 'exit', 'q']:
                break
            
            if not url:
                continue
            
            if not url.startswith(('http://', 'https://')):
                print("请输入完整的URL (包含 http:// 或 https://)")
                continue
            
            # 获取其他参数
            try:
                depth = int(input("最大抓取深度 (默认2): ") or "2")
                delay = float(input("请求延迟秒数 (默认2): ") or "2")
            except ValueError:
                print("输入无效，使用默认值")
                depth = 2
                delay = 2
            
            # 构建命令行参数
            sys.argv = ['spider.py', url, '--depth', str(depth), '--delay', str(delay)]
            
            print(f"\n开始爬取: {url}")
            main()
            
        except KeyboardInterrupt:
            print("\n\n程序被中断")
            break
        except Exception as e:
            print(f"运行出错: {e}")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # 如果没有命令行参数，进入交互模式
        run_interactive()
    else:
        main()
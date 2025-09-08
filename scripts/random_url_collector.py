#!/usr/bin/env python3
"""
随机URL收集器
从数据库中随机选择一个URL，收集其页面中的链接并存储到数据库中
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.url_collector import UrlCollector
from webspider.database import UrlDatabase


def collect_from_random_url(enable_keyword_filter=True, blacklist_file=None):
    """从随机URL开始收集更多URL"""
    print("随机URL收集器")
    print(f"关键词过滤: {'启用' if enable_keyword_filter else '禁用'}")
    if blacklist_file:
        print(f"屏蔽列表文件: {blacklist_file}")
    
    # 从数据库获取一个随机URL
    db = UrlDatabase()
    random_url_result = db.get_random_pending_url()
    
    if not random_url_result:
        print("数据库中没有待抓取的URL")
        return
    
    url, source_url, depth = random_url_result
    print(f"选择随机URL进行收集: {url}")
    
    # 创建URL收集器实例
    collector = UrlCollector(
        start_urls=[url],
        max_depth=2,  # 收集两层深度
        workers=5,
        enable_keyword_filter=enable_keyword_filter,
        blacklist_file=blacklist_file
    )
    
    # 显示收集前统计信息
    print("\n收集前数据库统计:")
    collector.print_database_stats()
    
    # 开始收集URL
    print(f"\n开始从 {url} 收集URL...")
    collector.collect_urls()
    
    # 显示收集后统计信息
    print("\n收集后数据库统计:")
    collector.print_database_stats()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='随机URL收集器')
    parser.add_argument('--no-filter', action='store_true', help='禁用关键词过滤，抓取所有页面')
    parser.add_argument('--blacklist', '-b', help='屏蔽URL列表文件路径')
    
    args = parser.parse_args()
    
    # 判断是否启用关键词过滤
    enable_keyword_filter = not args.no_filter
    
    collect_from_random_url(enable_keyword_filter, args.blacklist)


if __name__ == '__main__':
    main()
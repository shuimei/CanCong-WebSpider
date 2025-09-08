#!/usr/bin/env python3
"""
测试屏蔽规则功能
验证URL屏蔽是否正常工作
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.url_collector import UrlCollector


def test_blacklist_function():
    """测试屏蔽规则功能"""
    print("测试屏蔽规则功能")
    print("=" * 50)
    
    # 创建带屏蔽列表的URL收集器
    collector = UrlCollector(
        blacklist_file="blacklist.txt"
    )
    
    # 测试屏蔽规则加载
    print(f"加载的屏蔽规则数量: {len(collector.blacklist_patterns)}")
    print("前10个屏蔽规则:")
    for i, pattern in enumerate(list(collector.blacklist_patterns)[:10]):
        print(f"  {i+1}. {pattern}")
    
    # 测试URL屏蔽检查
    test_urls = [
        "https://www.facebook.com",
        "https://www.google.com",
        "https://www.taobao.com",
        "https://www.cgs.gov.cn",
        "https://example.com/download/file.zip",
        "https://news.sina.com.cn",
        "https://example.com/page"
    ]
    
    print("\nURL屏蔽检查测试:")
    for url in test_urls:
        is_blacklisted = collector.is_blacklisted(url)
        status = "🚫 屏蔽" if is_blacklisted else "✅ 允许"
        print(f"  {status} {url}")
    
    # 测试should_crawl_url方法
    print("\nURL抓取检查测试:")
    for url in test_urls:
        should_crawl = collector.should_crawl_url(url)
        status = "✅ 抓取" if should_crawl else "🚫 不抓取"
        print(f"  {status} {url}")


def test_with_different_blacklist():
    """测试使用不同的屏蔽列表"""
    print("\n" + "=" * 50)
    print("测试使用空屏蔽列表")
    
    # 创建不使用屏蔽列表的URL收集器
    collector_no_blacklist = UrlCollector()
    
    test_urls = [
        "https://www.facebook.com",
        "https://www.google.com",
        "https://www.taobao.com"
    ]
    
    print("不使用屏蔽列表时的检查结果:")
    for url in test_urls:
        should_crawl = collector_no_blacklist.should_crawl_url(url)
        status = "✅ 抓取" if should_crawl else "🚫 不抓取"
        print(f"  {status} {url}")


def main():
    """主函数"""
    test_blacklist_function()
    test_with_different_blacklist()
    
    print("\n" + "=" * 50)
    print("使用方法:")
    print("1. 使用默认屏蔽列表:")
    print("   python scripts/url_collector.py --blacklist blacklist.txt --url https://example.com")
    print("")
    print("2. 使用自定义屏蔽列表:")
    print("   python scripts/url_collector.py --blacklist my_blacklist.txt --from-database")
    print("")
    print("3. 随机URL收集器使用屏蔽列表:")
    print("   python scripts/random_url_collector.py --blacklist blacklist.txt")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
简单爬虫测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.simple_crawler import SimpleCrawler


def test_simple_crawler():
    """测试简单爬虫功能"""
    print("测试简单爬虫...")
    
    # 创建爬虫实例
    crawler = SimpleCrawler(
        output_dir='test_webpages',
        workers=2,
        timeout=10
    )
    
    # 显示统计信息
    crawler.print_stats()
    
    # 测试URL清理功能
    test_urls = [
        "https://example.com",
        "https://example.com/path/to/page",
        "https://example.com:8080/path",
        "http://www.test-site.com/very/long/path/to/some/page"
    ]
    
    print("\n测试文件名清理功能:")
    for url in test_urls:
        filename = crawler.sanitize_filename(url)
        print(f"  {url} -> {filename}")
    
    print("测试完成")


if __name__ == '__main__':
    test_simple_crawler()
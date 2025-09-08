#!/usr/bin/env python3
"""
测试带主题词筛选功能的URL收集器
演示如何使用关键词过滤来收集相关URL
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.url_collector import UrlCollector


def test_keyword_filtering():
    """测试关键词过滤功能"""
    print("测试带主题词筛选功能的URL收集器")
    
    # 创建启用关键词过滤的URL收集器实例
    collector_with_filter = UrlCollector(
        start_urls=["https://www.cgs.gov.cn"],  # 中国地质调查局官网
        max_depth=1,  # 只抓取一层深度
        workers=3,
        enable_keyword_filter=True
    )
    
    print("\n启用关键词过滤的收集器配置:")
    print(f"  起始URL: {collector_with_filter.start_urls[0]}")
    print(f"  关键词过滤: 启用")
    print(f"  关键词库大小: {len(collector_with_filter.target_keywords)}")
    
    # 创建禁用关键词过滤的URL收集器实例
    collector_without_filter = UrlCollector(
        start_urls=["https://www.cgs.gov.cn"],
        max_depth=1,
        workers=3,
        enable_keyword_filter=False
    )
    
    print("\n禁用关键词过滤的收集器配置:")
    print(f"  起始URL: {collector_without_filter.start_urls[0]}")
    print(f"  关键词过滤: 禁用")
    
    # 显示关键词库信息
    print(f"\n关键词库信息:")
    print(f"  总关键词数量: {len(collector_with_filter.target_keywords)}")
    print(f"  关键词样例: {list(collector_with_filter.target_keywords)[:10]}...")
    
    print("\n使用方法示例:")
    print("1. 启用关键词过滤（默认）:")
    print("   python scripts/url_collector.py --url https://www.cgs.gov.cn")
    print("")
    print("2. 禁用关键词过滤:")
    print("   python scripts/url_collector.py --url https://example.com --no-filter")
    print("")
    print("3. 从数据库中获取URL并收集（启用过滤）:")
    print("   python scripts/url_collector.py --from-database --limit 5")
    print("")
    print("4. 从文件读取URL并收集（禁用过滤）:")
    print("   python scripts/url_collector.py --urls-file urls.txt --no-filter")


if __name__ == '__main__':
    test_keyword_filtering()
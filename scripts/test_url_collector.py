#!/usr/bin/env python3
"""
测试URL收集器
演示如何从一个URL出发收集更多URL并存储到数据库中
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.url_collector import UrlCollector


def test_url_collection():
    """测试URL收集功能"""
    print("测试URL收集器")
    
    # 创建URL收集器实例
    collector = UrlCollector(
        start_urls=["http://example.com"],  # 使用一个测试URL
        max_depth=1,  # 只抓取一层深度
        workers=3
    )
    
    # 显示初始统计信息
    print("\n收集前数据库统计:")
    collector.print_database_stats()
    
    # 由于我们不想实际访问外部网站，这里只是演示代码结构
    print("\nURL收集器已配置完成，可以开始收集URL。")
    print("使用以下命令实际运行收集器:")
    print("  python scripts/url_collector.py --url http://example.com --depth 2")
    print("  python scripts/url_collector.py --from-database --limit 5")
    
    # 显示收集后统计信息（模拟）
    print("\n收集后数据库统计（模拟）:")
    collector.print_database_stats()


if __name__ == '__main__':
    test_url_collection()
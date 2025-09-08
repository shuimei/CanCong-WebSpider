#!/usr/bin/env python3
"""
测试随机URL启动器
从数据库中读取一个随机的、未被抓取过的URL并显示
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase


def test_get_random_pending_url():
    """测试获取随机待抓取URL功能"""
    print("测试随机URL启动器")
    
    db = UrlDatabase()
    try:
        result = db.get_random_pending_url()
        if result:
            url, source_url, depth = result
            print(f"成功获取到随机URL:")
            print(f"  URL: {url}")
            print(f"  源URL: {source_url}")
            print(f"  深度: {depth}")
        else:
            print("数据库中没有待抓取的URL")
            
        # 显示统计信息
        stats = db.get_stats()
        print("\n数据库统计信息:")
        print(f"  总URL数: {stats['total']}")
        print(f"  待抓取: {stats['pending']}")
        print(f"  抓取成功: {stats['success']}")
        print(f"  抓取失败: {stats['failed']}")
        print(f"  正在抓取: {stats['crawling']}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == '__main__':
    test_get_random_pending_url()
#!/usr/bin/env python3
"""
测试数据库连接池
验证连接池是否能解决连接数限制问题
"""

import sys
from pathlib import Path
import threading
import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase


def test_connection_pool():
    """测试连接池功能"""
    print("测试数据库连接池...")
    
    # 创建多个数据库实例
    databases = []
    for i in range(5):
        db = UrlDatabase()
        databases.append(db)
        print(f"创建数据库实例 {i+1}")
    
    # 测试并发访问
    def worker(worker_id):
        try:
            db = UrlDatabase()
            stats = db.get_stats()
            print(f"Worker {worker_id}: 成功获取统计信息，总URL数: {stats['total']}")
        except Exception as e:
            print(f"Worker {worker_id}: 失败 - {e}")
    
    print("\n启动并发测试...")
    threads = []
    for i in range(7):  # 启动7个线程，超过最小连接数
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print("\n连接池测试完成!")


def test_url_operations():
    """测试URL操作"""
    print("\n测试URL操作...")
    
    db = UrlDatabase()
    
    # 添加测试URL
    test_url = "https://example.com/test_connection_pool"
    added = db.add_url(test_url, source_url="https://example.com", depth=1)
    print(f"添加URL: {added}")
    
    # 获取统计信息
    stats = db.get_stats()
    print(f"统计信息: 总URL数={stats['total']}, 待抓取={stats['pending']}")


def main():
    """主函数"""
    print("数据库连接池测试")
    print("=" * 50)
    
    test_connection_pool()
    test_url_operations()
    
    print("\n所有测试完成!")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
测试数据库连接
验证连接池是否正常工作
"""

import sys
from pathlib import Path
import threading
import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase


def test_single_connection():
    """测试单个数据库连接"""
    print("测试单个数据库连接...")
    
    try:
        db = UrlDatabase()
        stats = db.get_stats()
        print("数据库连接成功!")
        print(f"统计信息: {stats}")
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False


def test_concurrent_connections():
    """测试并发数据库连接"""
    print("\n测试并发数据库连接...")
    
    results = []
    
    def worker(worker_id):
        try:
            db = UrlDatabase()
            stats = db.get_stats()
            results.append((worker_id, True, f"Worker {worker_id}: 成功获取统计信息"))
            print(f"Worker {worker_id}: 成功")
        except Exception as e:
            results.append((worker_id, False, f"Worker {worker_id}: 失败 - {e}"))
            print(f"Worker {worker_id}: 失败 - {e}")
    
    # 创建多个线程同时访问数据库
    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    # 统计结果
    success_count = sum(1 for _, success, _ in results if success)
    print(f"\n并发测试结果: {success_count}/10 成功")
    
    return success_count > 0


def test_url_operations():
    """测试URL操作"""
    print("\n测试URL操作...")
    
    try:
        db = UrlDatabase()
        
        # 添加测试URL
        test_url = "https://example.com/test_db_connection"
        added = db.add_url(test_url, source_url="https://example.com", depth=1)
        print(f"添加URL: {added}")
        
        # 检查URL状态
        is_crawled = db.is_crawled(test_url)
        print(f"URL是否已抓取: {is_crawled}")
        
        # 标记为正在抓取
        db.mark_crawling(test_url)
        print("标记为正在抓取")
        
        # 标记为成功
        db.mark_success(test_url, title="测试页面", html_file_path="/test/path.html")
        print("标记为成功")
        
        # 获取统计信息
        stats = db.get_stats()
        print(f"统计信息: {stats}")
        
        return True
    except Exception as e:
        print(f"URL操作测试失败: {e}")
        return False


def main():
    """主函数"""
    print("数据库连接测试")
    print("=" * 50)
    
    # 测试单个连接
    single_success = test_single_connection()
    
    # 测试并发连接
    concurrent_success = test_concurrent_connections()
    
    # 测试URL操作
    url_op_success = test_url_operations()
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"  单连接测试: {'通过' if single_success else '失败'}")
    print(f"  并发测试: {'通过' if concurrent_success else '失败'}")
    print(f"  URL操作测试: {'通过' if url_op_success else '失败'}")
    
    if single_success and concurrent_success and url_op_success:
        print("\n🎉 所有测试通过，数据库连接正常!")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查数据库配置和连接。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
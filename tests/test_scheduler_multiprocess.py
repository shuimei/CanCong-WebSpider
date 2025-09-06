#!/usr/bin/env python3
"""
多进程调度器测试脚本
简单测试多进程功能是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.spider_scheduler import SpiderScheduler


def test_scheduler_initialization():
    """测试调度器初始化"""
    print("测试调度器初始化...")
    scheduler = SpiderScheduler(max_concurrent=3, delay_between_tasks=5)
    
    # 检查基本属性
    assert scheduler.max_concurrent == 3
    assert scheduler.delay_between_tasks == 5
    assert scheduler.running == False
    
    print("✅ 调度器初始化测试通过")


def test_database_stats():
    """测试数据库统计功能"""
    print("测试数据库统计功能...")
    scheduler = SpiderScheduler()
    
    stats = scheduler.get_database_stats()
    if stats:
        print(f"  总URL数: {stats['total']}")
        print(f"  已完成: {stats['completed']}")
        print(f"  待抓取: {stats['pending']}")
        print(f"  抓取中: {stats['crawling']}")
        print(f"  失败: {stats['failed']}")
        print("✅ 数据库统计测试通过")
    else:
        print("⚠️ 数据库不存在或为空")


def test_random_url_selection():
    """测试随机URL选择功能"""
    print("测试随机URL选择功能...")
    scheduler = SpiderScheduler()
    
    # 测试获取单个URL
    url = scheduler.get_random_pending_url()
    if url:
        print(f"  随机URL: {url}")
        print("✅ 单个URL选择测试通过")
    else:
        print("⚠️ 没有待抓取的URL")
        return
    
    # 测试获取多个URL
    urls = scheduler.get_multiple_random_pending_urls(3)
    if urls:
        print(f"  随机URLs ({len(urls)}个):")
        for i, url in enumerate(urls, 1):
            print(f"    {i}. {url}")
        print("✅ 多个URL选择测试通过")
    else:
        print("⚠️ 没有足够的待抓取URL")


def test_clean_stale_status():
    """测试清理异常状态功能"""
    print("测试清理异常状态功能...")
    scheduler = SpiderScheduler()
    
    try:
        scheduler.clean_stale_crawling_status()
        print("✅ 状态清理测试通过")
    except Exception as e:
        print(f"❌ 状态清理测试失败: {e}")


def main():
    """主测试函数"""
    print("🧪 多进程调度器功能测试")
    print("=" * 50)
    
    try:
        test_scheduler_initialization()
        print()
        
        test_database_stats()
        print()
        
        test_random_url_selection()
        print()
        
        test_clean_stale_status()
        print()
        
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
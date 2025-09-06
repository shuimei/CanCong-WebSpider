#!/usr/bin/env python3
"""
测试随机抓取功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from webspider.database import UrlDatabase

def test_random_selection():
    """测试随机选择功能"""
    print("🧪 测试随机抓取功能")
    print("=" * 40)
    
    # 初始化数据库
    db = UrlDatabase('spider_urls.db')
    
    # 获取统计信息
    stats = db.get_stats()
    print(f"数据库统计:")
    print(f"  总URL数: {stats['total']}")
    print(f"  待抓取: {stats['pending']}")
    print(f"  抓取成功: {stats['success']}")
    print(f"  抓取失败: {stats['failed']}")
    print()
    
    if stats['pending'] == 0:
        print("❌ 数据库中没有待抓取的URL")
        return False
    
    # 测试随机选择 5 次
    print("随机选择测试 (连续5次):")
    print("-" * 30)
    
    selected_urls = []
    for i in range(5):
        random_url_info = db.get_random_pending_url()
        if random_url_info:
            url, source_url, depth = random_url_info
            selected_urls.append(url)
            print(f"{i+1}. {url}")
            print(f"   来源: {source_url or '起始URL'}")
            print(f"   深度: {depth}")
            print()
        else:
            print(f"{i+1}. 没有找到待抓取的URL")
    
    # 检查随机性
    unique_urls = set(selected_urls)
    print(f"随机性检查:")
    print(f"  选择的URL数: {len(selected_urls)}")
    print(f"  唯一URL数: {len(unique_urls)}")
    
    if len(unique_urls) > 1:
        print("✅ 随机选择工作正常，选择了不同的URL")
    elif len(unique_urls) == 1 and stats['pending'] > 1:
        print("⚠️ 多次选择了相同的URL（可能是随机性导致的巧合）")
    elif stats['pending'] == 1:
        print("✅ 只有一个待抓取URL，选择正确")
    
    return True

if __name__ == "__main__":
    success = test_random_selection()
    
    if success:
        print("\n🎯 测试建议:")
        print("现在可以使用以下命令测试随机抓取:")
        print("  python spider.py --random --depth 1")
        print("  python spider.py -r -d 2")
        print()
        print("或者在交互式模式中测试:")
        print("  python spider.py")
    else:
        print("\n💡 建议:")
        print("先运行一次正常抓取来收集URL:")
        print("  python spider.py https://example.com --depth 1")
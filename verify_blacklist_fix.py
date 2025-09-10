#!/usr/bin/env python3
"""
验证黑名单修复的测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.url_collector import UrlCollector

def test_blacklist_fix():
    """测试黑名单修复"""
    print("测试黑名单修复...")
    
    # 创建URL收集器实例
    collector = UrlCollector(blacklist_file='blacklist.txt')
    
    # 测试被误屏蔽的URL
    test_urls = [
        "https://mp.weixin.qq.com/s/Gk7SkHVQ4UG4MjFobuc3iQ",  # 微信公众号链接
        "https://www.qq.com",  # QQ主页
        "https://weibo.com",   # 微博（应该被屏蔽）
    ]
    
    print(f"加载了 {len(collector.blacklist_patterns)} 个屏蔽规则")
    
    for url in test_urls:
        is_blacklisted = collector.is_blacklisted(url)
        print(f"URL: {url}")
        print(f"  是否在屏蔽列表中: {is_blacklisted}")
        
        if is_blacklisted:
            # 找出是哪个模式导致的屏蔽
            url_lower = url.lower()
            for pattern in collector.blacklist_patterns:
                if pattern in url_lower:
                    print(f"  匹配的屏蔽模式: {pattern}")
        print()

if __name__ == "__main__":
    test_blacklist_fix()
#!/usr/bin/env python3
"""
JavaScript渲染性能对比测试
比较简单版本和优化版本的性能差异
"""

import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.simple_crawler_js import SimpleCrawlerJS
from scripts.optimized_crawler_js import OptimizedCrawlerJS


def test_simple_js_crawler():
    """测试简单版本的JS渲染性能"""
    print("=== 测试简单版本JS渲染性能 ===")
    
    # 创建简单版本爬虫（启用JS渲染）
    crawler = SimpleCrawlerJS(
        output_dir='test_simple_js',
        workers=3,
        timeout=30,
        enable_js=True
    )
    
    # 测试少量URL
    test_urls = [
        "https://example.com",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/html"
    ]
    
    start_time = time.time()
    try:
        crawler.crawl_urls(test_urls)
    except Exception as e:
        print(f"简单版本测试出错: {e}")
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"简单版本耗时: {elapsed:.2f}秒")
    
    return elapsed


def test_optimized_js_crawler():
    """测试优化版本的JS渲染性能"""
    print("\n=== 测试优化版本JS渲染性能 ===")
    
    # 创建优化版本爬虫（启用JS渲染）
    crawler = OptimizedCrawlerJS(
        output_dir='test_optimized_js',
        workers=3,
        timeout=30,
        enable_js=True,
        js_workers=2
    )
    
    # 测试少量URL
    test_urls = [
        "https://example.com",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/html"
    ]
    
    start_time = time.time()
    try:
        crawler.crawl_urls(test_urls)
    except Exception as e:
        print(f"优化版本测试出错: {e}")
    finally:
        crawler.cleanup()
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"优化版本耗时: {elapsed:.2f}秒")
    
    return elapsed


def main():
    """主函数"""
    print("JavaScript渲染性能对比测试")
    print("=" * 50)
    
    # 测试简单版本
    simple_time = test_simple_js_crawler()
    
    # 测试优化版本
    optimized_time = test_optimized_js_crawler()
    
    # 显示结果
    print("\n" + "=" * 50)
    print("性能对比结果:")
    print(f"简单版本耗时: {simple_time:.2f}秒")
    print(f"优化版本耗时: {optimized_time:.2f}秒")
    
    if simple_time > 0 and optimized_time > 0:
        improvement = ((simple_time - optimized_time) / simple_time) * 100
        print(f"性能提升: {improvement:.1f}%")
    
    print("\n优化原理:")
    print("1. 简单版本: 每个URL都启动/关闭WebDriver实例")
    print("2. 优化版本: 复用WebDriver实例（WebDriver池）")
    print("3. 优化版本减少了浏览器启动/关闭的开销")


if __name__ == '__main__':
    main()
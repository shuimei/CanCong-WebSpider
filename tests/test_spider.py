#!/usr/bin/env python3
"""
爬虫功能测试脚本
"""

import os
import sys
from webspider.database import UrlDatabase, normalize_url, is_valid_url


def test_database():
    """测试数据库功能"""
    print("测试数据库功能...")
    
    try:
        # 使用PostgreSQL数据库（不再需要临时数据库）
        db = UrlDatabase()
        
        # 测试添加URL
        test_base_url = 'https://test-example-spider.com'
        result1 = db.add_url(f'{test_base_url}/test1', depth=0)
        result2 = db.add_url(f'{test_base_url}/test2', source_url=test_base_url, depth=1)
        result3 = db.add_url(f'{test_base_url}/test1', depth=0)  # 重复URL
        
        print(f"添加第一个URL结果: {result1}")
        print(f"添加第二个URL结果: {result2}")
        print(f"添加重复URL结果: {result3}")
        
        # 测试状态检查
        is_crawled_before = db.is_crawled(f'{test_base_url}/test1')
        print(f"测试URL初始状态（应为False）: {is_crawled_before}")
        
        # 测试状态更新
        db.mark_crawling(f'{test_base_url}/test1')
        is_crawled_after = db.is_crawled(f'{test_base_url}/test1')
        print(f"标记正在抓取后状态（应为True）: {is_crawled_after}")
        
        db.mark_success(f'{test_base_url}/test1', title='Test Page', html_file_path='/test/path.html')
        
        # 测试统计
        stats = db.get_stats()
        print(f"数据库统计: {stats}")
        
        print("✅ 数据库功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_url_utils():
    """测试URL工具函数"""
    print("测试URL工具函数...")
    
    # 测试URL标准化
    assert normalize_url('/path', 'https://example.com') == 'https://example.com/path'
    assert normalize_url('https://example.com/page#fragment') == 'https://example.com/page'
    
    # 测试URL有效性检查
    assert is_valid_url('https://example.com') == True
    assert is_valid_url('http://example.com') == True
    assert is_valid_url('ftp://example.com') == False
    assert is_valid_url('invalid-url') == False
    
    print("✅ URL工具函数测试通过")


def test_project_structure():
    """测试项目结构"""
    print("测试项目结构...")
    
    required_files = [
        'scrapy.cfg',
        'webspider/__init__.py',
        'webspider/settings.py',
        'webspider/items.py',
        'webspider/database.py',
        'webspider/middlewares.py',
        'webspider/pipelines.py',
        'webspider/spiders/__init__.py',
        'webspider/spiders/webspider.py',
        'run_spider.py',
        'spider.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺失文件: {missing_files}")
        return False
    
    print("✅ 项目结构完整")
    return True


def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from webspider.database import UrlDatabase
        from webspider.items import UrlItem, PageItem
        from webspider.spiders.webspider import WebSpider
        print("✅ 核心模块导入成功")
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    
    return True


def test_dependencies():
    """测试依赖包"""
    print("测试Python依赖包...")
    
    required_packages = [
        'scrapy',
        'selenium', 
        'bs4',  # beautifulsoup4
        'lxml'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺失依赖包: {missing_packages}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True


def main():
    """主测试函数"""
    print("🕷️ 网页爬虫项目测试")
    print("=" * 40)
    
    tests = [
        test_project_structure,
        test_imports,
        test_dependencies,
        test_url_utils,
        test_database
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"正在运行: {test.__name__}")
        try:
            result = test()
            if result is None or result:
                passed += 1
                print(f"✅ {test.__name__} 测试通过")
            else:
                failed += 1
                print(f"❌ {test.__name__} 测试失败")
        except Exception as e:
            print(f"❌ {test.__name__} 测试异常: {e}")
            failed += 1
        print()
    
    print("=" * 40)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！爬虫项目就绪。")
        print()
        print("使用方法:")
        print("  python spider.py https://example.com")
        print("  python spider.py  # 交互式模式")
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息。")
    
    return failed == 0


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
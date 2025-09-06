#!/usr/bin/env python3
"""
爬虫功能测试脚本
"""

import os
import sys
import sqlite3
from webspider.database import UrlDatabase, normalize_url, is_valid_url


def test_database():
    """测试数据库功能"""
    print("测试数据库功能...")
    
    # 使用测试数据库
    import tempfile
    import time
    test_db = f'test_spider_{int(time.time())}.db'
    
    try:
        db = UrlDatabase(test_db)
        
        # 测试添加URL
        result1 = db.add_url('https://example.com', depth=0)
        result2 = db.add_url('https://example.com/page1', source_url='https://example.com', depth=1)
        result3 = db.add_url('https://example.com', depth=0)  # 重复URL
        
        assert result1 == True, "第一个URL应该添加成功"
        assert result2 == True, "第二个URL应该添加成功"
        assert result3 == False, "重复URL应该被忽略"
        
        # 测试状态检查
        assert not db.is_crawled('https://example.com'), "新URL不应该被标记为已抓取"
        
        # 测试状态更新
        db.mark_crawling('https://example.com')
        assert db.is_crawled('https://example.com'), "URL应该被标记为正在抓取"
        
        db.mark_success('https://example.com', title='Example', html_file_path='example.html')
        
        # 测试统计
        stats = db.get_stats()
        assert stats['total'] == 2, f"总数应该是2，实际是{stats['total']}"
        assert stats['success'] == 1, f"成功数应该是1，实际是{stats['success']}"
        
        print("✅ 数据库功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False
    finally:
        # 清理测试数据库
        try:
            if os.path.exists(test_db):
                os.remove(test_db)
        except:
            pass


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
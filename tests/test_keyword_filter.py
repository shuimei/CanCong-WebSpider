#!/usr/bin/env python3
"""
测试关键词过滤功能
"""

from webspider.spiders.webspider import WebSpider


def test_keyword_filter():
    """测试关键词过滤功能"""
    
    # 创建爬虫实例
    spider = WebSpider(start_url="https://example.com", enable_keyword_filter=True)
    
    # 测试相关页面内容
    relevant_html_samples = [
        """
        <html>
        <head><title>国家自然资源部</title></head>
        <body>
        <h1>自然资源管理</h1>
        <p>加强矿产资源勘探和开发，推进地质调查工作...</p>
        </body>
        </html>
        """,
        
        """
        <html>
        <head><title>中国地质调查局</title></head>
        <body>
        <h2>地质勘探最新进展</h2>
        <p>本次地质勘探发现了大型铜矿，储量丰富...</p>
        </body>
        </html>
        """,
        
        """
        <html>
        <head><title>煤炭开采安全管理</title></head>
        <body>
        <h1>矿山安全生产</h1>
        <p>确保煤矿开采过程中的安全生产...</p>
        </body>
        </html>
        """
    ]
    
    # 测试不相关页面内容
    irrelevant_html_samples = [
        """
        <html>
        <head><title>美食推荐</title></head>
        <body>
        <h1>今日菜谱</h1>
        <p>推荐几道美味家常菜的做法...</p>
        </body>
        </html>
        """,
        
        """
        <html>
        <head><title>体育新闻</title></head>
        <body>
        <h2>足球比赛结果</h2>
        <p>昨晚的足球比赛精彩激烈...</p>
        </body>
        </html>
        """,
        
        """
        <html>
        <head><title>购物指南</title></head>
        <body>
        <h1>电子产品评测</h1>
        <p>本期为大家评测最新的智能手机...</p>
        </body>
        </html>
        """
    ]
    
    print("🧪 测试关键词过滤功能")
    print("=" * 50)
    
    print("\n✅ 测试相关页面（应该通过过滤）:")
    for i, html in enumerate(relevant_html_samples, 1):
        result = spider.is_content_relevant(html, f"https://example{i}.com")
        status = "✅ 通过" if result else "❌ 被过滤"
        print(f"  测试页面 {i}: {status}")
    
    print("\n❌ 测试不相关页面（应该被过滤）:")
    for i, html in enumerate(irrelevant_html_samples, 1):
        result = spider.is_content_relevant(html, f"https://irrelevant{i}.com")
        status = "❌ 被过滤" if not result else "⚠️ 误判为相关"
        print(f"  测试页面 {i}: {status}")
    
    # 测试URL预过滤
    print("\n🔗 测试URL预过滤功能:")
    
    relevant_urls = [
        "https://mnr.gov.cn/gk/",
        "https://www.cgs.gov.cn/",
        "https://example.com/mining/",
        "https://geology.org.cn/",
        "https://example.com/natural-resources/"
    ]
    
    irrelevant_urls = [
        "https://example.com/sports/",
        "https://example.com/food/",
        "https://example.com/entertainment/",
        "https://example.com/fashion/",
        "https://example.com/travel/"
    ]
    
    print("  相关URL（应该通过）:")
    for url in relevant_urls:
        result = spider.is_url_potentially_relevant(url)
        status = "✅ 通过" if result else "❌ 被过滤"
        print(f"    {url}: {status}")
    
    print("  不相关URL（应该被过滤）:")
    for url in irrelevant_urls:
        result = spider.is_url_potentially_relevant(url)
        status = "❌ 被过滤" if not result else "⚠️ 误判为相关"
        print(f"    {url}: {status}")
    
    print(f"\n📋 关键词库信息:")
    print(f"  总关键词数量: {len(spider.target_keywords)}")
    print(f"  关键词样例: {list(spider.target_keywords)[:10]}...")


def test_url_filtering():
    """测试URL过滤功能"""
    spider = WebSpider(start_url="https://example.com", enable_keyword_filter=True)
    
    test_urls = [
        # 应该通过的URL
        ("https://mnr.gov.cn/", True, "政府网站"),
        ("https://example.com/mining/", True, "包含mining关键词"),
        ("https://geology.org/", True, "包含geology关键词"),
        ("https://example.com/mineral/", True, "包含mineral关键词"),
        
        # 应该被过滤的URL
        ("https://example.com/sports/", False, "体育相关"),
        ("https://example.com/food/", False, "美食相关"),
        ("https://example.com/image.jpg", False, "图片文件"),
        ("https://example.com/style.css", False, "样式文件"),
        ("https://example.com/api/data", False, "API接口"),
    ]
    
    print("\n🔍 URL过滤测试:")
    print("-" * 30)
    
    for url, expected, description in test_urls:
        result = spider.should_crawl_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url} - {description}")
        if result != expected:
            print(f"   预期: {'通过' if expected else '过滤'}, 实际: {'通过' if result else '过滤'}")


if __name__ == '__main__':
    test_keyword_filter()
    test_url_filtering()
    
    print("\n🎯 使用建议:")
    print("1. 默认启用关键词过滤，只抓取相关页面")
    print("2. 使用 --no-filter 参数可以禁用过滤，抓取所有页面")
    print("3. 过滤器会检查页面标题、meta信息、标题标签和正文内容")
    print("4. URL预过滤可以减少不必要的请求，提高效率")
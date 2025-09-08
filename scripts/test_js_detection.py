#!/usr/bin/env python3
"""
测试JS需求检测功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.smart_crawler import SmartCrawler


def test_js_detection():
    """测试JS需求检测功能"""
    print("测试JS需求检测功能")
    print("=" * 50)
    
    # 创建智能爬虫实例
    crawler = SmartCrawler(
        output_dir='test_js_detection',
        workers=2,
        timeout=30,
        enable_js_detection=True,
        js_workers=1
    )
    
    # 测试不同的HTML内容
    test_cases = [
        {
            "url": "https://example.com",
            "html": """
            <html>
            <head><title>Simple Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is a simple static page.</p>
            </body>
            </html>
            """,
            "expected": False,
            "description": "简单静态页面"
        },
        {
            "url": "https://spa-example.com",
            "html": """
            <html>
            <head><title>SPA Page</title></head>
            <body>
                <div id="app"></div>
                <script src="react.js"></script>
                <script>
                    ReactDOM.render(<App />, document.getElementById('app'));
                </script>
            </body>
            </html>
            """,
            "expected": True,
            "description": "React SPA页面"
        },
        {
            "url": "https://loading-example.com",
            "html": """
            <html>
            <head><title>Loading Page</title></head>
            <body>
                <div class="container">
                    <div class="loading">正在加载...</div>
                </div>
                <div class="content"></div>
            </body>
            </html>
            """,
            "expected": True,
            "description": "包含加载指示器的页面"
        },
        {
            "url": "https://dashboard.example.com",
            "html": """
            <html>
            <head><title>Dashboard</title></head>
            <body>
                <div id="root">
                    <div class="placeholder"></div>
                    <div class="placeholder"></div>
                    <div class="placeholder"></div>
                </div>
                <script src="vue.js"></script>
            </body>
            </html>
            """,
            "expected": True,
            "description": "Vue.js仪表板页面"
        }
    ]
    
    # 测试每个案例
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {case['description']}")
        print(f"URL: {case['url']}")
        
        # 检测是否需要JS渲染
        needs_js = crawler.needs_javascript_rendering(case['url'], case['html'])
        
        print(f"检测结果: {'需要JS渲染' if needs_js else '不需要JS渲染'}")
        print(f"预期结果: {'需要JS渲染' if case['expected'] else '不需要JS渲染'}")
        print(f"检测{'正确' if needs_js == case['expected'] else '错误'}")
    
    # 清理资源
    crawler.cleanup()
    
    print("\n" + "=" * 50)
    print("JS需求检测测试完成")


if __name__ == '__main__':
    test_js_detection()
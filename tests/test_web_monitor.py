#!/usr/bin/env python3
"""
测试Web监控界面功能
"""

import time
import requests
import json
from pathlib import Path

def test_web_monitor():
    """测试Web监控界面"""
    base_url = "http://localhost:8000"
    
    print("🧪 测试Web监控界面功能")
    print("=" * 40)
    
    # 测试API接口
    tests = [
        ("主页", "GET", "/"),
        ("统计信息API", "GET", "/api/stats"),
        ("页面列表API", "GET", "/api/pages"),
        ("失败页面API", "GET", "/api/failed"),
        ("搜索API", "GET", "/api/search?q=test"),
        ("API文档", "GET", "/docs")
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, method, endpoint in tests:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {test_name}: 成功 (状态码: {response.status_code})")
                success_count += 1
                
                # 如果是JSON API，尝试解析
                if endpoint.startswith("/api/"):
                    try:
                        data = response.json()
                        if endpoint == "/api/stats":
                            print(f"   统计信息: 总数={data.get('total', 0)}, 成功={data.get('success', 0)}")
                        elif endpoint == "/api/pages":
                            print(f"   页面数量: {len(data)}")
                    except:
                        pass
            else:
                print(f"❌ {test_name}: 失败 (状态码: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_name}: 连接失败 - {e}")
        except Exception as e:
            print(f"❌ {test_name}: 未知错误 - {e}")
    
    print("=" * 40)
    print(f"测试完成: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！Web监控界面工作正常。")
        print()
        print("📋 功能说明:")
        print("- 实时监控爬虫统计信息")
        print("- 浏览已抓取的网页列表")
        print("- 在线预览HTML页面")
        print("- 搜索和过滤页面")
        print("- WebSocket实时更新")
        print("- 响应式设计，支持移动设备")
    else:
        print("⚠️ 部分测试失败，请检查服务器状态。")
    
    return success_count == total_count

if __name__ == "__main__":
    print("请确保Web监控界面已启动 (python start_monitor.py)")
    print("等待3秒后开始测试...")
    time.sleep(3)
    
    success = test_web_monitor()
    
    if success:
        print()
        print("🌐 访问地址:")
        print("  主界面: http://localhost:8000")
        print("  API文档: http://localhost:8000/docs")
        print("  WebSocket: ws://localhost:8000/ws")
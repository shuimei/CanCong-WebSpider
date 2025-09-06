#!/usr/bin/env python3
"""
测试图表功能的脚本
"""

import requests
import json
import time

def test_api():
    """测试API接口"""
    try:
        # 测试统计API
        response = requests.get('http://localhost:8000/api/stats')
        if response.status_code == 200:
            stats = response.json()
            print("✅ API统计接口正常")
            print(f"统计数据: {json.dumps(stats, ensure_ascii=False, indent=2)}")
            return stats
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API测试异常: {e}")
        return None

def test_pages_api():
    """测试页面API"""
    try:
        response = requests.get('http://localhost:8000/api/pages')
        if response.status_code == 200:
            pages = response.json()
            print(f"✅ 页面API正常，返回{len(pages)}个页面")
            return pages
        else:
            print(f"❌ 页面API请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 页面API测试异常: {e}")
        return None

def main():
    print("🧪 开始测试图表相关功能")
    print("=" * 50)
    
    # 测试API
    stats = test_api()
    pages = test_pages_api()
    
    if stats:
        print("\n📊 数据分析:")
        total = stats.get('total', 0)
        success = stats.get('success', 0)
        pending = stats.get('pending', 0)
        failed = stats.get('failed', 0)
        crawling = stats.get('crawling', 0)
        
        print(f"总数据: {total}")
        print(f"成功率: {success/total*100:.1f}%" if total > 0 else "成功率: 0%")
        print(f"失败率: {failed/total*100:.1f}%" if total > 0 else "失败率: 0%")
        
        # 检查数据是否适合图表显示
        chart_data = [success, pending, failed, crawling]
        data_sum = sum(chart_data)
        
        print(f"\n🎯 图表数据: {chart_data}")
        print(f"数据总和: {data_sum}")
        
        if data_sum > 0:
            print("✅ 数据适合图表显示")
            for i, (label, value) in enumerate([
                ('成功', success), 
                ('待抓取', pending), 
                ('失败', failed), 
                ('抓取中', crawling)
            ]):
                percentage = value / data_sum * 100
                print(f"  {label}: {value} ({percentage:.1f}%)")
        else:
            print("❌ 数据为空，图表无法显示")
    
    print("\n🌐 访问地址:")
    print("主页面: http://localhost:8000")
    print("调试页面: http://localhost:8000/chart_debug.html")
    print("API统计: http://localhost:8000/api/stats")

if __name__ == '__main__':
    main()
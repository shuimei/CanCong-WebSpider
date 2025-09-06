#!/usr/bin/env python3
"""
关键词过滤功能使用示例
"""

print("🔍 网页爬虫 - 关键词过滤功能")
print("=" * 50)

print("新增功能:")
print("✅ 智能关键词过滤，专门抓取矿山、自然资源、地质相关网页")
print("✅ URL预过滤，减少无效请求")
print("✅ 支持禁用过滤器的选项")
print()

print("📋 关键词库包含:")
print("🏔️  矿山相关: 矿山、矿业、采矿、矿井、煤矿、金矿、铁矿等")
print("🌍 自然资源: 自然资源、国土资源、资源管理、水资源、森林资源等")
print("🗻 地质相关: 地质、地质勘探、地质调查、岩石、地层、地震等")
print("🏛️  相关机构: 国土资源部、地质调查局、地质公园等")
print()

print("💡 使用方法:")
print()

print("1️⃣ 启用关键词过滤 (默认模式):")
print("   python spider.py https://mnr.gov.cn")
print("   # 只抓取与矿山、自然资源、地质相关的页面")
print()

print("2️⃣ 禁用关键词过滤:")
print("   python spider.py https://example.com --no-filter")
print("   # 抓取所有类型的页面")
print()

print("3️⃣ 随机抓取 + 关键词过滤:")
print("   python spider.py --random")
print("   # 从数据库随机选择URL，并应用关键词过滤")
print()

print("4️⃣ 深度爬取相关网站:")
print("   python spider.py https://mnr.gov.cn --depth 3 --delay 1")
print("   # 深度抓取自然资源部网站的相关内容")
print()

print("📊 过滤机制:")
print("• URL预过滤: 检查URL路径中的关键词")
print("• 内容过滤: 分析页面标题、meta信息、标题标签和正文")
print("• 权重评分: 标题权重5倍，meta信息3倍，标题标签2倍")
print("• 判断标准: 至少匹配2个关键词或权重分数≥5分")
print()

print("🎯 推荐抓取目标:")
print("• 国家自然资源部: https://mnr.gov.cn")
print("• 中国地质调查局: https://www.cgs.gov.cn")
print("• 各省自然资源厅官网")
print("• 地质相关研究机构")
print("• 矿业公司官网")
print()

print("📈 性能优化:")
print("• 减少无效请求，节省带宽和时间")
print("• 提高相关内容占比")
print("• 支持灵活开关，适应不同需求")
print()

print("⚠️  注意事项:")
print("• 关键词过滤器可能会误过滤一些相关页面")
print("• 如果需要更全面的抓取，可以使用 --no-filter")
print("• 过滤器主要针对中文内容优化，英文内容也有基本支持")

if __name__ == '__main__':
    print("\n🚀 快速开始:")
    print("选择一个开始方式:")
    print("1. python spider.py https://mnr.gov.cn  # 抓取自然资源部")
    print("2. python spider.py --random            # 随机继续之前的抓取")
    print("3. python spider.py --stats             # 查看当前统计信息")
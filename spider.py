#!/usr/bin/env python3
"""
简单的爬虫启动器
"""

import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from run_spider import main, run_interactive

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("网页爬虫程序")
        print("=" * 30)
        print("使用方法:")
        print("  python spider.py <URL> [选项]")
        print("  python spider.py --random [选项]  # 随机选择待抓取URL")
        print("  python spider.py  # 交互式模式")
        print("")
        print("选项:")
        print("  --depth, -d     最大抓取深度 (默认: 2)")
        print("  --delay         请求延迟秒数 (默认: 2)")
        print("  --concurrent, -c 并发请求数 (默认: 4)")
        print("  --output, -o    输出目录 (默认: webpages)")
        print("  --database, --db 数据库文件 (默认: spider_urls.db)")
        print("  --random, -r    随机选择待抓取URL")
        print("  --no-filter     禁用关键词过滤，抓取所有页面")
        print("  --stats         显示统计信息")
        print("  --clean         清理未完成任务")
        print("  --reset         重置数据库")
        print("")
        print("示例:")
        print("  python spider.py https://example.com")
        print("  python spider.py https://example.com --depth 3 --delay 1")
        print("  python spider.py --random --depth 2  # 随机抓取")
        print("  python spider.py https://mnr.gov.cn --no-filter  # 禁用关键词过滤")
        print("")
        
        choice = input("按Enter进入交互模式，或输入URL直接开始: ").strip()
        if choice:
            sys.argv = ['spider.py', choice]
    
    if len(sys.argv) == 1:
        run_interactive()
    else:
        main()
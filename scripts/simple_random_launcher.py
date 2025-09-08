#!/usr/bin/env python3
"""
简单随机URL启动器
从数据库中读取一个随机的、未被抓取过的URL来启动任务
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase


def get_random_pending_url():
    """获取一个随机的待抓取URL"""
    db = UrlDatabase()
    try:
        result = db.get_random_pending_url()
        if result:
            url, source_url, depth = result
            print(f"获取到随机URL: {url}")
            return url
        else:
            print("数据库中没有待抓取的URL")
            return None
    except Exception as e:
        print(f"获取随机URL失败: {e}")
        return None


def launch_crawler_task(url, max_depth=3, workers=1, output_dir='webpages'):
    """启动爬虫任务"""
    try:
        # 构建命令
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / 'run_crawler.py'),
            '--url', url,
            '--depth', str(max_depth),
            '--workers', str(workers),
            '--output', output_dir
        ]
        
        print(f"启动爬虫任务: {' '.join(cmd)}")
        
        # 启动爬虫进程并等待完成
        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).parent.parent),
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        
        if result.returncode == 0:
            print(f"爬虫任务完成: {url}")
            return True
        else:
            print(f"爬虫任务失败: {url} (返回码: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"启动爬虫任务失败: {e}")
        return False


def print_database_stats():
    """打印数据库统计信息"""
    db = UrlDatabase()
    try:
        stats = db.get_stats()
        print("\n数据库统计信息:")
        print(f"  总URL数: {stats['total']}")
        print(f"  待抓取: {stats['pending']}")
        print(f"  抓取成功: {stats['success']}")
        print(f"  抓取失败: {stats['failed']}")
        print(f"  正在抓取: {stats['crawling']}")
    except Exception as e:
        print(f"获取数据库统计失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简单随机URL启动器')
    parser.add_argument('--depth', '-d', type=int, default=3,
                       help='最大抓取深度（默认3）')
    parser.add_argument('--workers', '-w', type=int, default=1,
                       help='并发工作线程数（默认1）')
    parser.add_argument('--output', '-o', default='webpages',
                       help='输出目录（默认webpages）')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='只显示统计信息，不启动任务')
    
    args = parser.parse_args()
    
    if args.stats:
        # 只显示统计信息
        print_database_stats()
        return 0
    
    print("简单随机URL启动器")
    
    # 获取随机URL
    url = get_random_pending_url()
    if not url:
        print_database_stats()
        return 1
    
    # 启动爬虫任务
    success = launch_crawler_task(url, args.depth, args.workers, args.output)
    
    # 显示统计信息
    print_database_stats()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
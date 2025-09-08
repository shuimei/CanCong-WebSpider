#!/usr/bin/env python3
"""
高级随机URL启动器
从数据库中读取多个随机的、未被抓取过的URL来启动任务
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase


class AdvancedRandomLauncher:
    """高级随机URL启动器"""
    
    def __init__(self, max_depth=3, workers=1, output_dir='webpages', concurrent_tasks=1):
        self.max_depth = max_depth
        self.workers = workers
        self.output_dir = output_dir
        self.concurrent_tasks = concurrent_tasks
        self.db = UrlDatabase()
    
    def get_random_pending_urls(self, count):
        """获取多个随机的待抓取URL"""
        urls = []
        try:
            for i in range(count):
                result = self.db.get_random_pending_url()
                if result:
                    url, source_url, depth = result
                    urls.append(url)
                else:
                    break
            return urls
        except Exception as e:
            print(f"获取随机URL失败: {e}")
            return []
    
    def launch_single_crawler_task(self, url, task_id=0):
        """启动单个爬虫任务"""
        try:
            # 构建命令
            cmd = [
                sys.executable,
                str(Path(__file__).parent.parent / 'run_crawler.py'),
                '--url', url,
                '--depth', str(self.max_depth),
                '--workers', str(self.workers),
                '--output', self.output_dir
            ]
            
            print(f"[Task-{task_id}] 启动爬虫任务: {url}")
            
            # 启动爬虫进程并等待完成
            result = subprocess.run(
                cmd,
                cwd=str(Path(__file__).parent.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[Task-{task_id}] 爬虫任务完成: {url}")
                return True
            else:
                print(f"[Task-{task_id}] 爬虫任务失败: {url} (返回码: {result.returncode})")
                if result.stdout:
                    print(f"[Task-{task_id}] 输出: {result.stdout[:200]}...")
                return False
                
        except Exception as e:
            print(f"[Task-{task_id}] 启动爬虫任务失败: {e}")
            return False
    
    def launch_multiple_tasks(self, count):
        """启动多个随机URL任务"""
        # 获取随机URL
        urls = self.get_random_pending_urls(count)
        if not urls:
            print("没有获取到待抓取的URL")
            return False
        
        print(f"获取到 {len(urls)} 个随机URL，准备启动任务...")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        # 如果只需要启动一个任务
        if self.concurrent_tasks == 1:
            success_count = 0
            for i, url in enumerate(urls):
                if self.launch_single_crawler_task(url, i+1):
                    success_count += 1
            return success_count > 0
        
        # 并发启动多个任务
        success_count = 0
        with ThreadPoolExecutor(max_workers=self.concurrent_tasks) as executor:
            # 提交任务
            future_to_url = {
                executor.submit(self.launch_single_crawler_task, url, i+1): (url, i+1)
                for i, url in enumerate(urls)
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url, task_id = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                except Exception as e:
                    print(f"[Task-{task_id}] 执行异常: {e}")
        
        print(f"\n总共完成 {len(urls)} 个任务，成功 {success_count} 个")
        return success_count > 0
    
    def print_database_stats(self):
        """打印数据库统计信息"""
        try:
            stats = self.db.get_stats()
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
    parser = argparse.ArgumentParser(description='高级随机URL启动器')
    parser.add_argument('--count', '-c', type=int, default=1,
                       help='启动任务数量（默认1）')
    parser.add_argument('--depth', '-d', type=int, default=3,
                       help='最大抓取深度（默认3）')
    parser.add_argument('--workers', '-w', type=int, default=1,
                       help='每个任务的并发工作线程数（默认1）')
    parser.add_argument('--concurrent', '-C', type=int, default=1,
                       help='同时运行的任务数（默认1）')
    parser.add_argument('--output', '-o', default='webpages',
                       help='输出目录（默认webpages）')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='只显示统计信息，不启动任务')
    parser.add_argument('--delay', type=int, default=0,
                       help='任务间延迟秒数（默认0）')
    
    args = parser.parse_args()
    
    launcher = AdvancedRandomLauncher(
        max_depth=args.depth,
        workers=args.workers,
        output_dir=args.output,
        concurrent_tasks=args.concurrent
    )
    
    if args.stats:
        # 只显示统计信息
        launcher.print_database_stats()
        return 0
    
    print("高级随机URL启动器")
    print(f"配置: 深度={args.depth}, 工作线程={args.workers}, 并发任务={args.concurrent}")
    
    # 启动任务
    success = launcher.launch_multiple_tasks(args.count)
    
    # 显示统计信息
    launcher.print_database_stats()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
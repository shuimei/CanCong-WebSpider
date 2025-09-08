#!/usr/bin/env python3
"""
随机URL启动器
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


class RandomUrlLauncher:
    """随机URL启动器"""
    
    def __init__(self, project_dir=None, max_depth=3, workers=1, output_dir='webpages'):
        """
        初始化随机URL启动器
        
        Args:
            project_dir: 项目根目录
            max_depth: 最大抓取深度
            workers: 并发工作线程数
            output_dir: 输出目录
        """
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent.parent
        self.max_depth = max_depth
        self.workers = workers
        self.output_dir = output_dir
        self.db = UrlDatabase()
        
        print(f"随机URL启动器初始化完成:")
        print(f"  项目目录: {self.project_dir}")
        print(f"  最大深度: {self.max_depth}")
        print(f"  工作线程: {self.workers}")
        print(f"  输出目录: {self.output_dir}")
    
    def get_random_pending_url(self):
        """获取一个随机的待抓取URL"""
        try:
            result = self.db.get_random_pending_url()
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
    
    def launch_crawler_task(self, url):
        """启动爬虫任务"""
        try:
            # 构建命令
            cmd = [
                sys.executable,
                str(self.project_dir / 'run_crawler.py'),
                '--url', url,
                '--depth', str(self.max_depth),
                '--workers', str(self.workers),
                '--output', self.output_dir
            ]
            
            print(f"启动爬虫任务: {' '.join(cmd)}")
            
            # 启动爬虫进程
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时输出爬虫日志
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # 等待进程完成
            return_code = process.wait()
            
            if return_code == 0:
                print(f"爬虫任务完成: {url}")
                return True
            else:
                print(f"爬虫任务失败: {url} (返回码: {return_code})")
                return False
                
        except Exception as e:
            print(f"启动爬虫任务失败: {e}")
            return False
    
    def launch_single_task(self):
        """启动单个随机URL任务"""
        # 获取随机URL
        url = self.get_random_pending_url()
        if not url:
            return False
        
        # 启动爬虫任务
        return self.launch_crawler_task(url)
    
    def launch_multiple_tasks(self, count=1):
        """启动多个随机URL任务"""
        success_count = 0
        for i in range(count):
            print(f"\n[任务 {i+1}/{count}]")
            if self.launch_single_task():
                success_count += 1
        
        print(f"\n总共完成 {count} 个任务，成功 {success_count} 个")
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
    parser = argparse.ArgumentParser(description='随机URL启动器（从数据库中读取随机URL启动任务）')
    parser.add_argument('--count', '-c', type=int, default=1,
                       help='启动任务数量（默认1）')
    parser.add_argument('--depth', '-d', type=int, default=3,
                       help='最大抓取深度（默认3）')
    parser.add_argument('--workers', '-w', type=int, default=1,
                       help='并发工作线程数（默认1）')
    parser.add_argument('--output', '-o', default='webpages',
                       help='输出目录（默认webpages）')
    parser.add_argument('--project-dir', '-p', type=str,
                       help='项目根目录路径')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='只显示统计信息，不启动任务')
    
    args = parser.parse_args()
    
    # 创建启动器
    launcher = RandomUrlLauncher(
        project_dir=args.project_dir,
        max_depth=args.depth,
        workers=args.workers,
        output_dir=args.output
    )
    
    if args.stats:
        # 只显示统计信息
        launcher.print_database_stats()
        return
    
    # 启动任务
    if args.count == 1:
        success = launcher.launch_single_task()
    else:
        success = launcher.launch_multiple_tasks(args.count)
    
    # 显示最终统计
    launcher.print_database_stats()
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
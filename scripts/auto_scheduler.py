#!/usr/bin/env python3
"""
自动爬虫调度器
基于run_crawler.py实现抓取后自动再随机启动一批任务
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase
from webspider.config import DatabaseConfig


class AutoSpiderScheduler:
    """自动爬虫调度器"""
    
    def __init__(self, project_dir=None, batch_size=2, max_depth=3, workers=2, 
                 output_dir='webpages', delay_between_batches=10):
        """
        初始化调度器
        
        Args:
            project_dir: 项目根目录
            batch_size: 每批处理的URL数量
            max_depth: 最大抓取深度
            workers: 每批并发worker数
            output_dir: 输出目录
            delay_between_batches: 批次间延迟（秒）
        """
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent.parent
        self.batch_size = batch_size
        self.max_depth = max_depth
        self.workers = workers
        self.output_dir = output_dir
        self.delay_between_batches = delay_between_batches
        self.db = UrlDatabase()
        self.running = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"自动爬虫调度器初始化完成")
        print(f"项目目录: {self.project_dir}")
        print(f"每批URL数: {self.batch_size}")
        print(f"最大深度: {self.max_depth}")
        print(f"Worker数: {self.workers}")
        print(f"输出目录: {self.output_dir}")
        print(f"批次延迟: {self.delay_between_batches}秒")
    
    def signal_handler(self, signum, frame):
        """信号处理器，用于优雅退出"""
        print(f"\n接收到信号 {signum}，正在停止调度器...")
        self.running = False
    
    def get_random_pending_urls(self, count):
        """获取多个随机待抓取的URL"""
        try:
            urls = []
            for _ in range(count):
                result = self.db.get_random_pending_url()
                if result:
                    urls.append(result[0])  # 只需要URL字符串
                else:
                    break
            return urls
        except Exception as e:
            print(f"获取随机URL失败: {e}")
            return []
    
    def run_crawler_batch(self, urls):
        """运行一批爬虫任务"""
        if not urls:
            print("没有URL需要抓取")
            return False
        
        try:
            # 构建命令
            cmd = [
                sys.executable,
                str(self.project_dir / 'run_crawler.py'),
                '--depth', str(self.max_depth),
                '--workers', str(self.workers),
                '--output', self.output_dir,
            ]
            
            # 添加URL参数
            for url in urls:
                cmd.extend(['--url', url])
            
            print(f"执行命令: {' '.join(cmd)}")
            
            # 运行爬虫
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                print("爬虫批次执行成功")
                if result.stdout:
                    print("输出:")
                    print(result.stdout)
                return True
            else:
                print(f"爬虫批次执行失败 (返回码: {result.returncode})")
                if result.stderr:
                    print("错误:")
                    print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("爬虫批次执行超时")
            return False
        except Exception as e:
            print(f"运行爬虫批次失败: {e}")
            return False
    
    def print_stats(self):
        """打印统计信息"""
        try:
            stats = self.db.get_stats()
            print("\n[STATS] 数据库统计信息:")
            print(f"  总URL数: {stats['total']}")
            print(f"  已完成: {stats['success'] + stats['failed']}")
            print(f"  待抓取: {stats['pending']}")
            print(f"  抓取中: {stats['crawling']}")
            print(f"  失败: {stats['failed']}")
        except Exception as e:
            print(f"获取统计信息失败: {e}")
    
    def start(self):
        """开始调度"""
        print(f"\n[START] 启动自动爬虫调度器")
        print("按 Ctrl+C 可以随时停止")
        
        self.running = True
        
        try:
            batch_count = 0
            
            while self.running:
                # 获取统计信息
                stats = self.db.get_stats()
                
                # 检查是否还有待抓取的URL
                if stats['pending'] == 0:
                    print("[DONE] 没有待抓取的URL")
                    break
                
                # 获取随机URL批次
                urls = self.get_random_pending_urls(self.batch_size)
                
                if not urls:
                    print("[DONE] 无法获取更多待抓取的URL")
                    break
                
                print(f"\n[BATCH-{batch_count+1}] 开始处理 {len(urls)} 个URL:")
                for i, url in enumerate(urls, 1):
                    print(f"  {i}. {url}")
                
                # 运行爬虫批次
                success = self.run_crawler_batch(urls)
                
                if success:
                    print(f"[BATCH-{batch_count+1}] 完成")
                else:
                    print(f"[BATCH-{batch_count+1}] 失败")
                
                batch_count += 1
                
                # 打印统计信息
                self.print_stats()
                
                # 检查是否继续运行
                if not self.running:
                    break
                
                # 批次间延迟
                if self.delay_between_batches > 0:
                    print(f"等待 {self.delay_between_batches} 秒后开始下一批...")
                    time.sleep(self.delay_between_batches)
            
        except KeyboardInterrupt:
            print("\n[STOP] 用户中断调度")
        except Exception as e:
            print(f"\n[ERROR] 调度异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            print(f"\n[BYE] 调度器已停止，共处理了 {batch_count} 个批次")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自动爬虫调度器')
    parser.add_argument('--batch-size', '-b', type=int, default=2,
                       help='每批处理的URL数量（默认2）')
    parser.add_argument('--depth', '-d', type=int, default=3,
                       help='最大抓取深度（默认3）')
    parser.add_argument('--workers', '-w', type=int, default=2,
                       help='每批并发worker数量（默认2）')
    parser.add_argument('--output', '-o', default='webpages',
                       help='输出目录（默认webpages）')
    parser.add_argument('--delay', type=int, default=10,
                       help='批次间延迟秒数（默认10）')
    parser.add_argument('--project-dir', '-p', type=str,
                       help='项目根目录路径')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='只显示统计信息，不启动调度')
    
    args = parser.parse_args()
    
    # 创建调度器
    scheduler = AutoSpiderScheduler(
        project_dir=args.project_dir,
        batch_size=args.batch_size,
        max_depth=args.depth,
        workers=args.workers,
        output_dir=args.output,
        delay_between_batches=args.delay
    )
    
    if args.stats:
        # 只显示统计信息
        scheduler.print_stats()
    else:
        # 启动调度器
        scheduler.start()


if __name__ == '__main__':
    main()
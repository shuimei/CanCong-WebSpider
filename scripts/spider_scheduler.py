#!/usr/bin/env python3
"""
智能爬虫调度脚本
循环随机选择未抓取的URL，启动爬虫任务，直到所有URL都被抓取完成
"""

import os
import sys
import time
import signal
import random
import sqlite3
import subprocess
import threading
import queue
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class SpiderScheduler:
    """爬虫调度器"""
    
    def __init__(self, project_dir=None, max_concurrent=2, delay_between_tasks=10):
        """
        初始化调度器
        
        Args:
            project_dir: 项目根目录
            max_concurrent: 最大并发进程数（默认2）
            delay_between_tasks: 任务之间的延迟（秒）
        """
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent.parent
        self.db_path = self.project_dir / 'spider_urls.db'
        self.max_concurrent = max_concurrent
        self.delay_between_tasks = delay_between_tasks
        self.running = False
        self.active_processes = {}  # 存储活跃进程 {thread_id: (process, url, start_time)}
        self.process_lock = threading.Lock()  # 线程安全锁
        self.url_queue = queue.Queue()  # URL队列
        
        # 统计信息
        self.stats = {
            'total_urls': 0,
            'completed_urls': 0,
            'failed_urls': 0,
            'pending_urls': 0,
            'current_tasks': {},  # {thread_id: url}
            'start_time': None,
            'tasks_completed': 0,
            'active_workers': 0
        }
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"爬虫调度器初始化完成")
        print(f"项目目录: {self.project_dir}")
        print(f"数据库路径: {self.db_path}")
        print(f"最大并发数: {self.max_concurrent}")
        print(f"任务间延迟: {self.delay_between_tasks}秒")
    
    def signal_handler(self, signum, frame):
        """信号处理器，用于优雅退出"""
        print(f"\n接收到信号 {signum}，正在停止调度器...")
        self.stop()
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        if not self.db_path.exists():
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总URL数量
            cursor.execute("SELECT COUNT(*) FROM urls")
            total = cursor.fetchone()[0]
            
            # 已完成数量
            cursor.execute("SELECT COUNT(*) FROM urls WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            # 失败数量
            cursor.execute("SELECT COUNT(*) FROM urls WHERE status = 'failed'")
            failed = cursor.fetchone()[0]
            
            # 待抓取数量
            cursor.execute("SELECT COUNT(*) FROM urls WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            # 正在处理数量
            cursor.execute("SELECT COUNT(*) FROM urls WHERE status = 'crawling'")
            crawling = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'crawling': crawling
            }
            
        except Exception as e:
            print(f"获取数据库统计失败: {e}")
            return None
    
    def get_multiple_random_pending_urls(self, count):
        """获取多个随机待抓取的URL"""
        if not self.db_path.exists():
            print("数据库文件不存在")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 随机获取多个待抓取的URL
            cursor.execute("""
                SELECT url FROM urls 
                WHERE status = 'pending' 
                ORDER BY RANDOM() 
                LIMIT ?
            """, (count,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [result[0] for result in results]
            
        except Exception as e:
            print(f"获取随机URL失败: {e}")
            return []

    def get_random_pending_url(self):
        """随机获取一个待抓取的URL"""
        if not self.db_path.exists():
            print("数据库文件不存在")
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 随机获取一个待抓取的URL
            cursor.execute("""
                SELECT url FROM urls 
                WHERE status = 'pending' 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"获取随机URL失败: {e}")
            return None
    
    def mark_url_crawling(self, url):
        """标记URL为正在抓取状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表结构，看是否有last_crawl_time列
            cursor.execute("PRAGMA table_info(urls)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'last_crawl_time' in columns:
                # 如果有last_crawl_time列，更新时间
                cursor.execute("""
                    UPDATE urls 
                    SET status = 'crawling', last_crawl_time = ? 
                    WHERE url = ?
                """, (datetime.now().isoformat(), url))
            else:
                # 如果没有last_crawl_time列，只更新状态
                cursor.execute("""
                    UPDATE urls 
                    SET status = 'crawling' 
                    WHERE url = ?
                """, (url,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"标记URL状态失败: {e}")
    
    def run_spider_for_url(self, url, worker_id=None):
        """为指定URL运行爬虫"""
        worker_info = f"[Worker-{worker_id}]" if worker_id else ""
        try:
            print(f"\n{'='*60}")
            print(f"{worker_info} 开始抓取: {url}")
            print(f"{worker_info} 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 标记URL为正在抓取
            self.mark_url_crawling(url)
            
            # 更新当前任务统计
            with self.process_lock:
                if worker_id:
                    self.stats['current_tasks'][worker_id] = url
                    self.stats['active_workers'] = len(self.stats['current_tasks'])
            
            # 构建爬虫命令
            spider_script = self.project_dir / 'spider.py'
            if not spider_script.exists():
                raise FileNotFoundError(f"爬虫脚本不存在: {spider_script}")
            
            # 运行爬虫命令
            cmd = [
                sys.executable,
                str(spider_script),
                url,
                '--depth', '2'  # 默认深度为2
            ]
            
            print(f"{worker_info} 执行命令: {' '.join(cmd)}")
            
            # 启动子进程
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 记录活跃进程
            with self.process_lock:
                if worker_id:
                    self.active_processes[worker_id] = (process, url, datetime.now())
            
            # 实时输出爬虫日志（但不阻塞其他worker）
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = f"{worker_info} {output.strip()}"
                    print(line)
                    output_lines.append(line)
            
            # 等待进程完成
            return_code = process.wait()
            
            # 清除活跃进程记录
            with self.process_lock:
                if worker_id and worker_id in self.active_processes:
                    del self.active_processes[worker_id]
                if worker_id and worker_id in self.stats['current_tasks']:
                    del self.stats['current_tasks'][worker_id]
                self.stats['active_workers'] = len(self.stats['current_tasks'])
            
            if return_code == 0:
                print(f"\n✅ {worker_info} 抓取完成: {url}")
                with self.process_lock:
                    self.stats['tasks_completed'] += 1
                return True
            else:
                print(f"\n❌ {worker_info} 抓取失败: {url} (返回码: {return_code})")
                return False
                
        except KeyboardInterrupt:
            print(f"\n⏸️  {worker_info} 用户中断抓取: {url}")
            if 'process' in locals():
                process.terminate()
                process.wait()
            return False
            
        except Exception as e:
            print(f"\n💥 {worker_info} 抓取异常: {url} - {e}")
            return False
        finally:
            # 确保清除统计信息
            with self.process_lock:
                if worker_id and worker_id in self.active_processes:
                    del self.active_processes[worker_id]
                if worker_id and worker_id in self.stats['current_tasks']:
                    del self.stats['current_tasks'][worker_id]
                self.stats['active_workers'] = len(self.stats['current_tasks'])
    
    def clean_stale_crawling_status(self):
        """清理长时间处于crawling状态的URL（可能是异常退出留下的）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表结构，看是否有last_crawl_time列
            cursor.execute("PRAGMA table_info(urls)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'last_crawl_time' in columns:
                # 如果有last_crawl_time列，使用时间条件
                cursor.execute("""
                    UPDATE urls 
                    SET status = 'pending' 
                    WHERE status = 'crawling' 
                    AND datetime(last_crawl_time) < datetime('now', '-1 hour')
                """)
            else:
                # 如果没有last_crawl_time列，只按状态清理
                cursor.execute("""
                    UPDATE urls 
                    SET status = 'pending' 
                    WHERE status = 'crawling'
                """)
            
            affected = cursor.rowcount
            if affected > 0:
                print(f"重置了 {affected} 个长时间未完成的抓取任务")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"清理异常状态失败: {e}")
    
    def print_progress(self):
        """打印当前进度"""
        stats = self.get_database_stats()
        if stats:
            self.stats.update(stats)
            
            total = stats['total']
            completed = stats['completed']
            failed = stats['failed']
            pending = stats['pending']
            crawling = stats['crawling']
            
            if total > 0:
                progress = (completed / total) * 100
                print(f"\n📊 当前进度:")
                print(f"  总URL数: {total}")
                print(f"  已完成: {completed} ({progress:.1f}%)")
                print(f"  待抓取: {pending}")
                print(f"  抓取中: {crawling}")
                print(f"  失败: {failed}")
                print(f"  当前活跃Worker: {self.stats['active_workers']}")
                print(f"  本次任务数: {self.stats['tasks_completed']}")
                
                # 显示活跃任务
                with self.process_lock:
                    if self.stats['current_tasks']:
                        print(f"  活跃任务:")
                        for worker_id, url in self.stats['current_tasks'].items():
                            print(f"    Worker-{worker_id}: {url[:50]}...")
                
                if self.stats['start_time']:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    if elapsed > 0:
                        speed = self.stats['tasks_completed'] / (elapsed / 3600)  # 任务/小时
                        print(f"  运行时间: {elapsed/60:.1f}分钟")
                        print(f"  平均速度: {speed:.1f}任务/小时")
    
    def start(self):
        """开始调度"""
        print(f"\n🚀 启动爬虫调度器 (最大并发: {self.max_concurrent})")
        print("按 Ctrl+C 可以随时停止")
        
        # 检查数据库
        if not self.db_path.exists():
            print("❌ 数据库文件不存在，请先运行爬虫添加一些URL")
            return
        
        # 清理异常状态
        self.clean_stale_crawling_status()
        
        # 获取初始统计
        initial_stats = self.get_database_stats()
        if not initial_stats or initial_stats['total'] == 0:
            print("❌ 数据库中没有URL，请先运行爬虫添加一些URL")
            return
        
        if initial_stats['pending'] == 0:
            print("✅ 所有URL都已处理完成！")
            return
        
        print(f"📋 找到 {initial_stats['pending']} 个待抓取URL，开始调度...")
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        try:
            # 使用线程池管理多个worker
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                active_futures = {}
                
                while self.running:
                    try:
                        # 获取当前统计
                        stats = self.get_database_stats()
                        if not stats:
                            print("❌ 无法获取数据库统计，停止调度")
                            break
                        
                        # 检查是否还有待抓取的URL
                        if stats['pending'] == 0 and len(active_futures) == 0:
                            print("\n🎉 所有URL都已抓取完成！")
                            break
                        
                        # 检查已完成的任务
                        completed_futures = []
                        try:
                            # 使用非阻塞方式检查已完成的任务
                            for future in list(active_futures.keys()):
                                if future.done():
                                    try:
                                        worker_id = active_futures[future]
                                        result = future.result(timeout=0.1)  # 很短的超时，只是为了获取结果
                                        completed_futures.append(future)
                                        print(f"\n🏁 Worker-{worker_id} 任务完成")
                                    except Exception as e:
                                        worker_id = active_futures[future]
                                        print(f"\n⚠️ Worker-{worker_id} 任务异常: {e}")
                                        completed_futures.append(future)
                        except Exception as e:
                            print(f"检查任务状态时出错: {e}")
                        
                        # 清理已完成的future
                        for future in completed_futures:
                            if future in active_futures:
                                del active_futures[future]
                        
                        # 启动新的worker任务
                        available_slots = self.max_concurrent - len(active_futures)
                        if available_slots > 0 and stats['pending'] > 0:
                            # 获取多个待抓取URL
                            urls = self.get_multiple_random_pending_urls(available_slots)
                            
                            for i, url in enumerate(urls):
                                if not self.running:
                                    break
                                    
                                worker_id = len(active_futures) + i + 1
                                future = executor.submit(self.run_spider_for_url, url, worker_id)
                                active_futures[future] = worker_id
                                print(f"\n🚀 启动 Worker-{worker_id}: {url}")
                        
                        # 等待策略
                        if len(active_futures) > 0:
                            time.sleep(2)  # 等待一下再检查
                        else:
                            # 没有活跃任务时，等待一下再查找新URL
                            if stats['pending'] > 0:
                                time.sleep(self.delay_between_tasks)
                        
                        # 定期显示进度
                        if hasattr(self, '_last_progress_time'):
                            if (datetime.now() - self._last_progress_time).total_seconds() > 30:
                                self.print_progress()
                                self._last_progress_time = datetime.now()
                        else:
                            self.print_progress()
                            self._last_progress_time = datetime.now()
                            
                    except Exception as e:
                        print(f"调度循环中发生异常: {e}")
                        import traceback
                        traceback.print_exc()
                        # 等待一下再继续
                        time.sleep(2)
                
                # 等待所有活跃任务完成
                if active_futures:
                    print(f"\n⏳ 等待 {len(active_futures)} 个活跃任务完成...")
                    # 使用更安全的方式等待任务完成
                    remaining_futures = list(active_futures.keys())
                    while remaining_futures:
                        completed_in_batch = []
                        for future in remaining_futures:
                            if future.done():
                                try:
                                    worker_id = active_futures[future]
                                    result = future.result()
                                    print(f"Worker-{worker_id} 最终完成")
                                except Exception as e:
                                    worker_id = active_futures[future]
                                    print(f"Worker-{worker_id} 最终异常: {e}")
                                completed_in_batch.append(future)
                        
                        # 移除已完成的任务
                        for future in completed_in_batch:
                            remaining_futures.remove(future)
                        
                        # 如果还有未完成的任务，等待一下
                        if remaining_futures:
                            time.sleep(1)
                            
        except KeyboardInterrupt:
            print("\n⏸️ 用户中断调度")
        except Exception as e:
            print(f"\n💥 调度异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            
            # 最终统计
            final_stats = self.get_database_stats()
            if final_stats:
                print(f"\n📊 最终统计:")
                print(f"  总URL数: {final_stats['total']}")
                print(f"  已完成: {final_stats['completed']}")
                print(f"  待抓取: {final_stats['pending']}")
                print(f"  失败: {final_stats['failed']}")
                print(f"  本次完成任务数: {self.stats['tasks_completed']}")
                
                if self.stats['start_time']:
                    total_time = (datetime.now() - self.stats['start_time']).total_seconds()
                    print(f"  总运行时间: {total_time/60:.1f}分钟")
                    if total_time > 0:
                        speed = self.stats['tasks_completed'] / (total_time / 3600)
                        print(f"  平均速度: {speed:.1f}任务/小时")
            
            print("\n👋 调度器已停止")
    
    def stop(self):
        """停止调度"""
        self.running = False
        
        # 终止所有活跃进程
        with self.process_lock:
            if self.active_processes:
                print(f"正在终止 {len(self.active_processes)} 个活跃爬虫进程...")
                
                for worker_id, (process, url, start_time) in self.active_processes.items():
                    try:
                        print(f"终止 Worker-{worker_id}: {url}")
                        process.terminate()
                    except Exception as e:
                        print(f"终止 Worker-{worker_id} 失败: {e}")
                
                # 等待进程终止
                for worker_id, (process, url, start_time) in self.active_processes.items():
                    try:
                        process.wait(timeout=10)
                        print(f"Worker-{worker_id} 已终止")
                    except subprocess.TimeoutExpired:
                        print(f"强制终止 Worker-{worker_id}...")
                        process.kill()
                        process.wait()
                    except Exception as e:
                        print(f"Worker-{worker_id} 终止异常: {e}")
                
                self.active_processes.clear()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='爬虫智能调度器')
    parser.add_argument('--delay', '-d', type=int, default=10,
                       help='任务之间的延迟时间（秒，默认10秒）')
    parser.add_argument('--workers', '-w', type=int, default=2,
                       help='最大并发worker数量（默认2）')
    parser.add_argument('--project-dir', '-p', type=str,
                       help='项目根目录路径（默认为脚本所在目录的上级）')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='只显示统计信息，不启动调度')
    
    args = parser.parse_args()
    
    # 创建调度器
    scheduler = SpiderScheduler(
        project_dir=args.project_dir,
        max_concurrent=args.workers,
        delay_between_tasks=args.delay
    )
    
    if args.stats:
        # 只显示统计信息
        print("\n📊 数据库统计信息:")
        stats = scheduler.get_database_stats()
        if stats:
            print(f"  总URL数: {stats['total']}")
            print(f"  已完成: {stats['completed']}")
            print(f"  待抓取: {stats['pending']}")
            print(f"  抓取中: {stats['crawling']}")
            print(f"  失败: {stats['failed']}")
        else:
            print("  无法获取统计信息")
    else:
        # 启动调度器
        scheduler.start()


if __name__ == '__main__':
    main()
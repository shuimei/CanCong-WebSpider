#!/usr/bin/env python3
"""检查URL抓取状态"""

from webspider.database import UrlDatabase
import psycopg2
from webspider.config import DatabaseConfig

def main():
    db = UrlDatabase()
    stats = db.get_stats()
    
    print("=" * 50)
    print("URL 抓取统计")
    print("=" * 50)
    print(f"总URL数:    {stats['total']}")
    print(f"待抓取:     {stats['pending']}")
    print(f"抓取成功:   {stats['success']}")
    print(f"抓取失败:   {stats['failed']}")
    print(f"正在抓取:   {stats['crawling']}")
    
    print("\n" + "=" * 50)
    print("最近失败的URL (前10个)")
    print("=" * 50)
    
    try:
        config = DatabaseConfig.get_postgres_params()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        cur.execute('''
            SELECT url, error_message 
            FROM urls 
            WHERE status = %s 
            ORDER BY created_time DESC 
            LIMIT 10
        ''', ('failed',))
        
        for i, (url, error_msg) in enumerate(cur.fetchall(), 1):
            print(f"{i:2d}. {url}")
            print(f"    错误: {error_msg}")
            print()
        
        print("=" * 50)
        print("最近成功的URL (前10个)")
        print("=" * 50)
        
        cur.execute('''
            SELECT url, title, html_file_path
            FROM urls 
            WHERE status = %s 
            ORDER BY created_time DESC 
            LIMIT 10
        ''', ('success',))
        
        for i, (url, title, html_file) in enumerate(cur.fetchall(), 1):
            print(f"{i:2d}. {url}")
            if title:
                print(f"    标题: {title}")
            if html_file:
                print(f"    文件: {html_file}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"查询数据库失败: {e}")

if __name__ == '__main__':
    main()
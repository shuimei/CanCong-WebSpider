#!/usr/bin/env python3
"""检查数据库表结构"""

import psycopg2
from webspider.config import DatabaseConfig

def main():
    try:
        config = DatabaseConfig.get_postgres_params()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        print("检查 urls 表的列结构:")
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'urls'")
        columns = cur.fetchall()
        
        for column_name, data_type in columns:
            print(f"  {column_name}: {data_type}")
        
        print("\n检查最近的记录:")
        cur.execute("SELECT url, status, error_message FROM urls LIMIT 5")
        records = cur.fetchall()
        
        for i, (url, status, error_msg) in enumerate(records, 1):
            print(f"{i}. {url}")
            print(f"   状态: {status}")
            if error_msg:
                print(f"   错误: {error_msg}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"数据库操作失败: {e}")

if __name__ == '__main__':
    main()
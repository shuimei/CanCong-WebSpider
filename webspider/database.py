import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import threading
from datetime import datetime
from urllib.parse import urlparse, urljoin
import os
from webspider.config import DatabaseConfig


class UrlDatabase:
    """URL数据库管理类 - PostgreSQL版本"""
    
    # 类变量，用于存储连接池
    _connection_pool = None
    _pool_lock = threading.Lock()
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.lock = threading.Lock()
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """初始化连接池"""
        with UrlDatabase._pool_lock:
            if UrlDatabase._connection_pool is None:
                try:
                    # 创建连接池，最大连接数设置为20
                    UrlDatabase._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=20,
                        host=self.config.PG_HOST,
                        port=self.config.PG_PORT,
                        database=self.config.PG_DATABASE,
                        user=self.config.PG_USERNAME,
                        password=self.config.PG_PASSWORD
                    )
                    print("数据库连接池初始化成功")
                except Exception as e:
                    print(f"初始化连接池失败: {e}")
                    raise
    
    def _get_connection(self):
        """从连接池获取数据库连接"""
        try:
            with UrlDatabase._pool_lock:
                if UrlDatabase._connection_pool is None:
                    self._init_connection_pool()
                return UrlDatabase._connection_pool.getconn()
        except Exception as e:
            print(f"获取数据库连接失败: {e}")
            raise
    
    def _return_connection(self, conn):
        """将连接返回到连接池"""
        try:
            with UrlDatabase._pool_lock:
                if UrlDatabase._connection_pool is not None:
                    UrlDatabase._connection_pool.putconn(conn)
        except Exception as e:
            print(f"返回数据库连接失败: {e}")
            # 如果返回连接池失败，直接关闭连接
            try:
                conn.close()
            except:
                pass
    
    def _init_database(self):
        """初始化数据库表 - 由setup_postgresql.py处理"""
        pass
    
    def add_url(self, url, source_url=None, depth=0):
        """添加URL到待抓取队列"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO urls (url, source_url, depth, status) 
                VALUES (%s, %s, %s, 'pending')
                ON CONFLICT (url) DO NOTHING
            ''', (url, source_url, depth))
            conn.commit()
            rowcount = cursor.rowcount
            cursor.close()
            self._return_connection(conn)
            return rowcount > 0
        except psycopg2.Error as e:
            print(f"添加URL失败: {e}")
            if conn:
                self._return_connection(conn)
            return False
        except Exception as e:
            print(f"添加URL失败: {e}")
            if conn:
                self._return_connection(conn)
            return False
    
    def is_crawled(self, url):
        """检查URL是否已经抓取成功过（只检查success状态）"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM urls WHERE url = %s', (url,))
            result = cursor.fetchone()
            cursor.close()
            self._return_connection(conn)
            if result:
                # 只有success状态才认为已抓取，避免重复处理crawling状态的URL
                return result[0] == 'success'
            return False
        except psycopg2.Error as e:
            print(f"检查URL状态失败: {e}")
            if conn:
                self._return_connection(conn)
            return False
        except Exception as e:
            print(f"检查URL状态失败: {e}")
            if conn:
                self._return_connection(conn)
            return False
    
    def mark_crawling(self, url):
        """标记URL为正在抓取"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urls SET status = 'crawling' WHERE url = %s
            ''', (url,))
            conn.commit()
            cursor.close()
            self._return_connection(conn)
        except psycopg2.Error as e:
            print(f"标记URL正在抓取失败: {e}")
            if conn:
                self._return_connection(conn)
        except Exception as e:
            print(f"标记URL正在抓取失败: {e}")
            if conn:
                self._return_connection(conn)
    
    def mark_success(self, url, title=None, html_file_path=None):
        """标记URL抓取成功"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urls SET 
                    status = 'success',
                    title = %s,
                    html_file_path = %s,
                    crawled_time = CURRENT_TIMESTAMP
                WHERE url = %s
            ''', (title, html_file_path, url))
            conn.commit()
            cursor.close()
            self._return_connection(conn)
        except psycopg2.Error as e:
            print(f"标记URL成功失败: {e}")
            if conn:
                self._return_connection(conn)
        except Exception as e:
            print(f"标记URL成功失败: {e}")
            if conn:
                self._return_connection(conn)
    
    def mark_failed(self, url, error_message=None):
        """标记URL抓取失败"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urls SET 
                    status = 'failed',
                    error_message = %s,
                    crawled_time = CURRENT_TIMESTAMP
                WHERE url = %s
            ''', (error_message, url))
            conn.commit()
            cursor.close()
            self._return_connection(conn)
        except psycopg2.Error as e:
            print(f"标记URL失败失败: {e}")
            if conn:
                self._return_connection(conn)
        except Exception as e:
            print(f"标记URL失败失败: {e}")
            if conn:
                self._return_connection(conn)
    
    def get_random_pending_url(self):
        """随机获取一个待抓取的URL"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url, source_url, depth FROM urls 
                WHERE status = 'pending' 
                ORDER BY RANDOM() 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            cursor.close()
            self._return_connection(conn)
            return result if result else None
        except psycopg2.Error as e:
            print(f"获取随机URL失败: {e}")
            if conn:
                self._return_connection(conn)
            return None
        except Exception as e:
            print(f"获取随机URL失败: {e}")
            if conn:
                self._return_connection(conn)
            return None
    
    def get_pending_urls(self, limit=100):
        """获取待抓取的URL列表"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url, source_url, depth FROM urls 
                WHERE status = 'pending' 
                ORDER BY depth, created_time 
                LIMIT %s
            ''', (limit,))
            result = cursor.fetchall()
            cursor.close()
            self._return_connection(conn)
            return result
        except psycopg2.Error as e:
            print(f"获取待抓取URL列表失败: {e}")
            if conn:
                self._return_connection(conn)
            return []
        except Exception as e:
            print(f"获取待抓取URL列表失败: {e}")
            if conn:
                self._return_connection(conn)
            return []
    
    def get_stats(self):
        """获取抓取统计信息"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, COUNT(*) FROM urls GROUP BY status
            ''')
            stats = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM urls')
            total = cursor.fetchone()[0]
            
            cursor.close()
            self._return_connection(conn)
            
            return {
                'total': total,
                'pending': stats.get('pending', 0),
                'success': stats.get('success', 0),
                'failed': stats.get('failed', 0),
                'crawling': stats.get('crawling', 0)
            }
        except psycopg2.Error as e:
            print(f"获取统计信息失败: {e}")
            if conn:
                self._return_connection(conn)
            return {
                'total': 0, 'pending': 0, 'success': 0, 
                'failed': 0, 'crawling': 0
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            if conn:
                self._return_connection(conn)
            return {
                'total': 0, 'pending': 0, 'success': 0, 
                'failed': 0, 'crawling': 0
            }
    
    def cleanup_stale_crawling(self):
        """清理长时间处于crawling状态的URL"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urls SET status = 'pending' 
                WHERE status = 'crawling' 
                AND created_time < (CURRENT_TIMESTAMP - INTERVAL '1 hour')
            ''')
            conn.commit()
            rowcount = cursor.rowcount
            cursor.close()
            self._return_connection(conn)
            return rowcount
        except psycopg2.Error as e:
            print(f"清理停滞抓取任务失败: {e}")
            if conn:
                self._return_connection(conn)
            return 0
        except Exception as e:
            print(f"清理停滞抓取任务失败: {e}")
            if conn:
                self._return_connection(conn)
            return 0


def normalize_url(url, base_url=None):
    """标准化URL"""
    if base_url:
        url = urljoin(base_url, url)
    
    # 移除fragment
    parsed = urlparse(url)
    normalized = parsed._replace(fragment='').geturl()
    
    return normalized


def is_valid_url(url):
    """检查URL是否有效"""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.scheme in ('http', 'https')
    except:
        return False
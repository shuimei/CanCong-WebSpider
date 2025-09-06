import sqlite3
import threading
from datetime import datetime
from urllib.parse import urlparse, urljoin
import os


class UrlDatabase:
    """URL数据库管理类"""
    
    def __init__(self, db_path='spider_urls.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建URL状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    source_url TEXT,
                    status TEXT DEFAULT 'pending',
                    depth INTEGER DEFAULT 0,
                    title TEXT,
                    html_file_path TEXT,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    crawled_time TIMESTAMP,
                    error_message TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON urls(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON urls(status)')
            
            conn.commit()
    
    def add_url(self, url, source_url=None, depth=0):
        """添加URL到待抓取队列"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO urls (url, source_url, depth, status) 
                        VALUES (?, ?, ?, 'pending')
                    ''', (url, source_url, depth))
                    conn.commit()
                    return cursor.rowcount > 0
            except sqlite3.Error as e:
                print(f"添加URL失败: {e}")
                return False
    
    def is_crawled(self, url):
        """检查URL是否已经抓取过"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM urls WHERE url = ?', (url,))
            result = cursor.fetchone()
            if result:
                return result[0] in ['success', 'crawling']
            return False
    
    def mark_crawling(self, url):
        """标记URL为正在抓取"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE urls SET status = 'crawling' WHERE url = ?
                ''', (url,))
                conn.commit()
    
    def mark_success(self, url, title=None, html_file_path=None):
        """标记URL抓取成功"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE urls SET 
                        status = 'success',
                        title = ?,
                        html_file_path = ?,
                        crawled_time = CURRENT_TIMESTAMP
                    WHERE url = ?
                ''', (title, html_file_path, url))
                conn.commit()
    
    def mark_failed(self, url, error_message=None):
        """标记URL抓取失败"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE urls SET 
                        status = 'failed',
                        error_message = ?,
                        crawled_time = CURRENT_TIMESTAMP
                    WHERE url = ?
                ''', (error_message, url))
                conn.commit()
    
    def get_random_pending_url(self):
        """随机获取一个待抓取的URL"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url, source_url, depth FROM urls 
                WHERE status = 'pending' 
                ORDER BY RANDOM() 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            return result if result else None
    
    def get_pending_urls(self, limit=100):
        """获取待抓取的URL列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url, source_url, depth FROM urls 
                WHERE status = 'pending' 
                ORDER BY depth, created_time 
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    
    def get_stats(self):
        """获取抓取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, COUNT(*) FROM urls GROUP BY status
            ''')
            stats = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM urls')
            total = cursor.fetchone()[0]
            
            return {
                'total': total,
                'pending': stats.get('pending', 0),
                'success': stats.get('success', 0),
                'failed': stats.get('failed', 0),
                'crawling': stats.get('crawling', 0)
            }
    
    def cleanup_stale_crawling(self):
        """清理长时间处于crawling状态的URL"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE urls SET status = 'pending' 
                    WHERE status = 'crawling' 
                    AND datetime(created_time, '+1 hour') < datetime('now')
                ''')
                conn.commit()
                return cursor.rowcount


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
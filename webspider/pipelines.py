import os
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from webspider.items import UrlItem, PageItem
from webspider.database import UrlDatabase
from webspider.config import AppConfig


class UrlFilterPipeline:
    """URL过滤管道"""
    
    def __init__(self):
        self.db = UrlDatabase()
    
    def process_item(self, item, spider):
        """处理URL数据项"""
        if isinstance(item, UrlItem):
            url = item['url']
            
            # 过滤无效URL
            if not self._is_valid_url(url):
                spider.logger.info(f"过滤无效URL: {url}")
                return None
            
            # 过滤不需要的文件类型
            if self._is_unwanted_file(url):
                spider.logger.info(f"过滤不需要的文件: {url}")
                return None
            
            # 过滤外部域名（可选）
            if hasattr(spider, 'allowed_domains') and spider.allowed_domains:
                if not self._is_allowed_domain(url, spider.allowed_domains):
                    spider.logger.info(f"过滤外部域名: {url}")
                    return None
        
        return item
    
    def _is_valid_url(self, url):
        """检查URL是否有效"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ('http', 'https')
        except:
            return False
    
    def _is_unwanted_file(self, url):
        """检查是否为不需要的文件类型"""
        unwanted_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv',
            '.exe', '.msi', '.dmg', '.app'
        ]
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        return any(path.endswith(ext) for ext in unwanted_extensions)
    
    def _is_allowed_domain(self, url, allowed_domains):
        """检查域名是否允许"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for allowed_domain in allowed_domains:
                if domain == allowed_domain.lower() or domain.endswith('.' + allowed_domain.lower()):
                    return True
            
            return False
        except:
            return False


class HtmlSavePipeline:
    """HTML保存管道"""
    
    def __init__(self, webpages_dir='webpages'):
        self.webpages_dir = webpages_dir
        self.db = UrlDatabase()
        self._ensure_directory()
    
    @classmethod
    def from_crawler(cls, crawler):
        webpages_dir = crawler.settings.get('WEBPAGES_DIR', 'webpages')
        return cls(webpages_dir)
    
    def _ensure_directory(self):
        """确保目录存在"""
        if not os.path.exists(self.webpages_dir):
            os.makedirs(self.webpages_dir)
    
    def process_item(self, item, spider):
        """处理页面数据项"""
        if isinstance(item, PageItem):
            url = item['url']
            html_content = item['html_content']
            title = item.get('title', '')
            
            # 生成文件名
            filename = self._generate_filename(url)
            file_path = os.path.join(self.webpages_dir, filename)
            
            try:
                # 保存HTML文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 更新数据库记录
                self.db.mark_success(url, title=title, html_file_path=file_path)
                
                spider.logger.info(f"保存页面: {url} -> {file_path}")
                
                # 保存元数据文件
                self._save_metadata(item, file_path)
                
            except Exception as e:
                spider.logger.error(f"保存页面失败 {url}: {e}")
                self.db.mark_failed(url, str(e))
        
        return item
    
    def _generate_filename(self, url):
        """生成文件名"""
        # 使用URL的MD5哈希作为文件名
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        # 尝试从URL路径提取有意义的名称
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split('/') if part]
        
        if path_parts:
            # 使用路径的最后一部分
            base_name = path_parts[-1]
            # 移除扩展名，添加哈希前缀
            if '.' in base_name:
                base_name = base_name.rsplit('.', 1)[0]
            filename = f"{url_hash[:8]}_{base_name}.html"
        else:
            # 使用域名
            domain = parsed.netloc.replace(':', '_').replace('.', '_')
            filename = f"{url_hash[:8]}_{domain}.html"
        
        # 清理文件名中的非法字符
        filename = self._clean_filename(filename)
        
        return filename
    
    def _clean_filename(self, filename):
        """清理文件名中的非法字符"""
        import re
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename
    
    def _save_metadata(self, item, html_file_path):
        """保存页面元数据"""
        metadata = {
            'url': item['url'],
            'title': item.get('title', ''),
            'crawl_time': datetime.now().isoformat(),
            'extracted_urls_count': len(item.get('extracted_urls', [])),
            'html_file_path': html_file_path
        }
        
        # 保存元数据到JSON文件
        import json
        metadata_path = html_file_path.replace('.html', '_metadata.json')
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存元数据失败: {e}")


class StatisticsPipeline:
    """统计信息管道"""
    
    def __init__(self):
        self.db = UrlDatabase()
        self.processed_count = 0
        self.start_time = datetime.now()
    
    def process_item(self, item, spider):
        """处理数据项并统计"""
        if isinstance(item, PageItem):
            self.processed_count += 1
            
            # 每处理10个页面输出一次统计
            if self.processed_count % 10 == 0:
                self._print_statistics(spider)
        
        return item
    
    def _print_statistics(self, spider):
        """打印统计信息"""
        stats = self.db.get_stats()
        elapsed_time = datetime.now() - self.start_time
        
        spider.logger.info(f"""
        ==========统计信息==========
        运行时间: {elapsed_time}
        已处理页面: {self.processed_count}
        总URL数: {stats['total']}
        待抓取: {stats['pending']}
        抓取成功: {stats['success']}
        抓取失败: {stats['failed']}
        正在抓取: {stats['crawling']}
        ===========================
        """)
    
    def close_spider(self, spider):
        """爬虫关闭时输出最终统计"""
        self._print_statistics(spider)
        spider.logger.info("爬虫已完成！")
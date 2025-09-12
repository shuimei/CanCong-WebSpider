#!/usr/bin/env python3
"""
URL收集器脚本
只抓取URL并将其存储到数据库中，不下载网页内容
"""

import os
import sys
import time
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import re

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from webspider.database import UrlDatabase
from webspider.config import DatabaseConfig


class UrlCollector:
    """URL收集器"""
    
    def __init__(self, start_urls=None, max_depth=3, output_dir='url_collections', workers=5, 
                 enable_keyword_filter=True, blacklist_file=None):
        """
        初始化URL收集器
        
        Args:
            start_urls: 起始URL列表
            max_depth: 最大抓取深度
            output_dir: 输出目录（用于保存日志等）
            workers: 并发请求数
            enable_keyword_filter: 是否启用关键词过滤
            blacklist_file: 屏蔽URL列表文件路径
        """
        self.start_urls = start_urls or []
        self.max_depth = max_depth
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.enable_keyword_filter = enable_keyword_filter
        self.blacklist_file = blacklist_file
        self.blacklist_patterns = set()
        self.db = UrlDatabase()
        
        # 加载屏蔽列表
        if self.blacklist_file and os.path.exists(self.blacklist_file):
            self._load_blacklist()
        
        # 矿山、自然资源、地质相关关键词（扩展了应急管理相关词汇）
        self.target_keywords = {
            '矿', '地球化学', '地调', '岩土',
            # 矿山相关
            '矿山', '矿业', '矿产', '采矿', '矿井', '矿物', '矿藏', '开采', '矿工', '矿权',
            '煤矿', '金矿', '铁矿', '铜矿', '铝矿', '锌矿', '石油', '天然气', '页岩气',
            '露天开采', '地下开采', '选矿', '冶炼', '矿物加工', '矿山安全', '矿山环保',
            
            # 自然资源相关
            '自然资源', '国土资源', '资源管理', '资源开发', '资源保护', '资源配置',
            '土地资源', '水资源', '森林资源', '海洋资源', '生态资源', '能源',
            '可再生能源', '不可再生资源', '资源勘探', '资源评估', '资源规划',
            
            # 地质相关
            '地质', '地质勘探', '地质调查', '地质环境', '地质灾害', '地质工程',
            '水文地质', '工程地质', '环境地质', '海洋地质', '构造地质', '沉积地质',
            '岩石', '岩层', '地层', '断层', '褶皱', '地壳', '地幔', '板块构造',
            '地震', '火山', '滑坡', '泥石流', '地面沉降', '岩溶', '喀斯特',
            '钻探', '物探', '化探', '遥感', '测绘', '地形测量', 'GIS', '遥感影像',
            
            # 应急管理相关（新增）
            '应急管理', '应急', '安全', '安全生产', '安全监管', '安全监察',
            '事故', '灾害', '救援', '应急预案', '应急响应', '应急处置',
            '风险评估', '隐患排查', '安全检查', '安全培训', '安全教育',
            '监管', '监察', '执法', '违规', '整改', '处罚',
            
            # 相关机构和术语
            '国土资源部', '自然资源部', '地质调查局', '矿产资源', '地质公园',
            '地质博物馆', '勘察设计', '地质勘察', '岩土工程', '地基基础',
            '环境影响评价', '水土保持', '生态修复', '绿色矿山', '智慧矿山',
            '应急管理部', '煤矿安全监察', '安全生产监督管理',
            
            # 英文关键词
            'mine', 'mining', 'geology', 'resource', 'natural',
            'mineral', 'coal', 'oil', 'gas', 'exploration',
            'geological', 'survey', 'earthquake', 'volcano',
            'emergency', 'safety', 'accident', 'disaster', 'rescue',
            'regulation', 'supervision', 'inspection'
        }
        
        # 将关键词转换为小写以便不区分大小写匹配
        self.target_keywords_lower = {kw.lower() for kw in self.target_keywords}
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 已访问的URL集合，用于避免重复抓取（在内存中）
        self.visited_urls = set()
        
        print(f"URL收集器初始化完成:")
        print(f"  起始URL数: {len(self.start_urls)}")
        print(f"  最大深度: {self.max_depth}")
        print(f"  输出目录: {self.output_dir}")
        print(f"  并发数: {self.workers}")
        print(f"  关键词过滤: {'启用' if self.enable_keyword_filter else '禁用'}")
        print(f"  屏蔽列表: {len(self.blacklist_patterns)} 个模式")
        print(f"  关键词库大小: {len(self.target_keywords)} 个关键词")
    
    def _load_blacklist(self):
        """加载屏蔽URL列表"""
        try:
            with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.blacklist_patterns.add(line.lower())
            print(f"加载了 {len(self.blacklist_patterns)} 个屏蔽规则")
        except Exception as e:
            print(f"加载屏蔽列表失败: {e}")
    
    def is_blacklisted(self, url):
        """检查URL是否在屏蔽列表中"""
        url_lower = url.lower()
        for pattern in self.blacklist_patterns:
            if pattern in url_lower:
                return True
        return False
    
    def is_valid_url(self, url):
        """检查URL是否有效"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ('http', 'https')
        except:
            return False
    
    def normalize_url(self, url, base_url=None):
        """标准化URL"""
        if base_url:
            url = urljoin(base_url, url)
        
        # 移除fragment
        parsed = urlparse(url)
        normalized = parsed._replace(fragment='').geturl()
        
        return normalized
    
    def should_crawl_url(self, url):
        """判断URL是否应该抓取"""
        try:
            # 检查是否在屏蔽列表中
            if self.is_blacklisted(url):
                return False
            
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # 过滤不需要的文件类型
            unwanted_extensions = [
                # 图片文件
                '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico',
                # 样式和脚本文件
                '.css', '.js', '.map',
                # 文档文件
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                # 压缩文件
                '.zip', '.rar', '.7z', '.tar', '.gz',
                # 音频视频文件
                '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
                # 其他文件
                '.exe', '.msi', '.dmg', '.app'
            ]
            
            if any(path.endswith(ext) for ext in unwanted_extensions):
                return False
            
            # 过滤常见的API和非页面URL
            unwanted_patterns = [
                '/api/', '/ajax/', '/json/', '/xml/', '/rss/',
                '?download=', '&download=', 'download.php', 'download.asp'
            ]
            
            url_lower = url.lower()
            if any(pattern in url_lower for pattern in unwanted_patterns):
                return False
            
            # 关键词预过滤：检查URL中是否包含相关关键词（如果启用了过滤）
            if self.enable_keyword_filter and not self.is_url_potentially_relevant(url):
                return False
            
            return True
            
        except Exception as e:
            print(f"检查URL失败: {url} - {e}")
            return False
    
    def is_url_potentially_relevant(self, url):
        """检查URL是否可能相关（初步过滤）"""
        url_lower = url.lower()
        
        # 简化的关键词列表，用于URL过滤
        url_keywords = [
            '矿', '地质', '资源', '国土', '自然', '应急', '安全', 'mem',
            'mine', 'mining', 'geology', 'resource', 'natural',
            'mineral', 'coal', 'oil', 'gas', 'exploration', 'emergency', 'safety'
        ]
        
        # 检查URL路径和查询参数中是否包含相关关键词
        for keyword in url_keywords:
            if keyword in url_lower:
                return True
        
        # 如果URL中没有相关关键词，但是是政府或机构网站，也可能相关
        if any(domain in url_lower for domain in ['.gov.', '.org.', '.edu.']):
            return True
        
        # 对于没有明显关键词的URL，默认为可能相关（放宽限制）
        return True
    
    def is_content_relevant(self, html_content, url):
        """检查页面内容是否与矿山、自然资源、地质相关"""
        try:
            # 检查是否在屏蔽列表中
            if self.is_blacklisted(url):
                return False
                
            # 提取文本内容
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取页面文本内容
            page_text = soup.get_text().lower()
            
            # 获取标题和关键词标签
            title_text = ''
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text().lower()
            
            # 获取meta关键词和description
            meta_text = ''
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                meta_text += meta_keywords['content'].lower() + ' '
            
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description and meta_description.get('content'):
                meta_text += meta_description['content'].lower() + ' '
            
            # 获取主要标题内容
            heading_text = ''
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text += heading.get_text().lower() + ' '
            
            # 组合所有文本内容，按重要性加权
            # 标题和meta信息权重最高，然后是标题标签，最后是页面内容
            weighted_content = (
                title_text * 5 +  # 标题权重5倍
                meta_text * 3 +   # meta信息权重3倍
                heading_text * 2 + # 标题标签权重2倍
                page_text         # 页面内容权重1倍
            )
            
            # 统计匹配的关键词数量
            matched_keywords = []
            keyword_count = 0
            
            for keyword in self.target_keywords_lower:
                if keyword in weighted_content:
                    matched_keywords.append(keyword)
                    # 计算关键词出现次数（按权重计算）
                    count_in_title = title_text.count(keyword) * 5
                    count_in_meta = meta_text.count(keyword) * 3
                    count_in_heading = heading_text.count(keyword) * 2
                    count_in_content = page_text.count(keyword)
                    
                    keyword_count += count_in_title + count_in_meta + count_in_heading + count_in_content
            
            # 改进的判断标准：
            # 1. 至少匹配3个关键词，或者
            # 2. 关键词总权重超过5分（考虑重复和权重），或者
            # 3. 标题中包含至少2个高权重关键词（如"安全"、"应急"、"矿山"等）
            title_high_priority_keywords = ['安全', '应急', '矿山', '矿', '地质', '资源', '管理']
            title_matches = [kw for kw in title_high_priority_keywords if kw in title_text]
            
            is_relevant = (
                len(matched_keywords) >= 3 or 
                keyword_count >= 5 or
                len(title_matches) >= 2
            )
            
            if is_relevant:
                print(f"相关页面: {url}")
                print(f"  匹配关键词: {matched_keywords[:10]}...")  # 只显示前10个
                print(f"  关键词权重分: {keyword_count}")
                if title_matches:
                    print(f"  标题匹配关键词: {title_matches}")
            else:
                print(f"不相关页面: {url}")
                print(f"  匹配关键词: {matched_keywords}")
                print(f"  关键词权重分: {keyword_count}")
            
            return is_relevant
            
        except Exception as e:
            print(f"检查内容相关性失败: {url} - {e}")
            # 如果检查失败，默认为相关（避免过度过滤）
            return True
    
    def extract_urls(self, html_content, base_url):
        """从HTML内容中提取所有URL"""
        urls = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取a标签的href
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = self.normalize_url(href, base_url)
                if self.is_valid_url(full_url) and self.should_crawl_url(full_url):
                    urls.add(full_url)
            
            # 提取iframe的src
            for iframe in soup.find_all('iframe', src=True):
                src = iframe['src']
                full_url = self.normalize_url(src, base_url)
                if self.is_valid_url(full_url) and self.should_crawl_url(full_url):
                    urls.add(full_url)
            
        except Exception as e:
            print(f"提取URL失败: {e}")
        
        return list(urls)
    
    def fetch_page_urls(self, url, depth=0):
        """获取页面中的URL（只抓取URL，不下载内容）"""
        # 检查深度限制
        if depth > self.max_depth:
            return []
        
        # 检查是否已访问
        if url in self.visited_urls:
            return []
        
        # 检查是否在屏蔽列表中
        if self.is_blacklisted(url):
            print(f"[Depth-{depth}] URL在屏蔽列表中，跳过: {url}")
            return []
        
        # 添加到已访问集合
        self.visited_urls.add(url)
        
        try:
            print(f"[Depth-{depth}] 处理URL: {url}")
            
            # 发送HTTP请求获取页面内容
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=30,
                allow_redirects=True
            )
            
            # 改进的中文编码处理逻辑
            original_encoding = response.encoding
            print(f"[Depth-{depth}] 原始编码: {original_encoding}")
            
            # 检查是否需要调整编码
            if response.status_code == 200:
                # 尝试多种常见中文编码
                encodings_to_try = ['utf-8', 'gb2312', 'gbk', 'gb18030']
                content_decoded = False
                
                # 首先检查Content-Type头中的编码信息
                content_type = response.headers.get('content-type', '').lower()
                if 'charset=' in content_type:
                    # 从Content-Type头中提取编码
                    charset_start = content_type.find('charset=') + 8
                    charset_end = content_type.find(';', charset_start)
                    if charset_end == -1:
                        charset_end = len(content_type)
                    header_encoding = content_type[charset_start:charset_end].strip()
                    if header_encoding:
                        encodings_to_try.insert(0, header_encoding)  # 优先尝试头中的编码
                
                # 尝试各种编码
                for encoding in encodings_to_try:
                    try:
                        response.encoding = encoding
                        # 检查解码后的内容是否包含中文字符
                        sample_text = response.text[:1000]  # 取前1000个字符检查
                        chinese_chars = [char for char in sample_text if '\u4e00' <= char <= '\u9fff']
                        if len(chinese_chars) > 10:  # 如果包含足够多的中文字符
                            print(f"[Depth-{depth}] 检测到中文内容，使用编码: {encoding}")
                            content_decoded = True
                            break
                    except Exception as e:
                        continue
                
                # 如果所有编码都失败，回退到原始编码
                if not content_decoded:
                    response.encoding = original_encoding
                    print(f"[Depth-{depth}] 无法检测合适编码，回退到原始编码: {original_encoding}")
            
            # 检查响应状态
            if response.status_code == 200:
                # 检查内容类型是否为HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    print(f"[Depth-{depth}] 跳过非HTML内容: {url} (Content-Type: {content_type})")
                    return []
                
                # 如果启用了关键词过滤，检查页面内容是否相关
                if self.enable_keyword_filter and not self.is_content_relevant(response.text, url):
                    print(f"[Depth-{depth}] 页面内容不相关，跳过: {url}")
                    self.db.mark_failed(url, "页面内容与目标主题不相关")
                    return []
                
                # 提取URL
                extracted_urls = self.extract_urls(response.text, url)
                print(f"[Depth-{depth}] 从 {url} 提取了 {len(extracted_urls)} 个URL")
                
                # 将提取的URL添加到数据库
                added_count = 0
                for extracted_url in extracted_urls:
                    # 检查提取的URL是否在屏蔽列表中
                    if self.is_blacklisted(extracted_url):
                        print(f"[Depth-{depth}] 提取的URL在屏蔽列表中，跳过: {extracted_url}")
                        continue
                        
                    if self.db.add_url(extracted_url, source_url=url, depth=depth+1):
                        added_count += 1
                
                print(f"[Depth-{depth}] 成功添加 {added_count} 个新URL到数据库")
                # 标记当前URL为成功处理
                self.db.mark_success(url, title="URL Collected")
                return extracted_urls
            else:
                print(f"[Depth-{depth}] HTTP错误 {response.status_code}: {url}")
                self.db.mark_failed(url, f"HTTP {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"[Depth-{depth}] 请求异常: {url} - {e}")
            self.db.mark_failed(url, f"Request Exception: {str(e)}")
            return []
        except Exception as e:
            print(f"[Depth-{depth}] 未知错误: {url} - {e}")
            self.db.mark_failed(url, f"Unknown Error: {str(e)}")
            return []
    
    def collect_urls(self):
        """收集URL"""
        if not self.start_urls:
            print("没有提供起始URL")
            return 0
        
        print(f"开始收集URL，共 {len(self.start_urls)} 个起始URL")
        print("-" * 60)
        
        # 将起始URL添加到数据库
        for url in self.start_urls:
            if self.is_valid_url(url) and not self.is_blacklisted(url):
                self.db.add_url(url, depth=0)
        
        # 按深度逐层抓取
        current_urls = self.start_urls[:]
        total_collected = 0
        
        for depth in range(self.max_depth + 1):
            if not current_urls:
                break
            
            print(f"\n[第{depth}层] 处始处理 {len(current_urls)} 个URL")
            
            next_urls = []
            for url in current_urls:
                if url in self.visited_urls:
                    continue
                    
                # 获取页面中的URL
                extracted_urls = self.fetch_page_urls(url, depth)
                next_urls.extend(extracted_urls)
                total_collected += len(extracted_urls)
            
            current_urls = next_urls
        
        # 显示统计信息
        print("\n" + "=" * 60)
        print("URL收集完成统计")
        print("=" * 60)
        print(f"起始URL数: {len(self.start_urls)}")
        print(f"总收集URL数: {total_collected}")
        print(f"访问URL数: {len(self.visited_urls)}")
        
        # 显示数据库统计
        self.print_database_stats()
        
        return total_collected
    
    def collect_urls_from_database(self, limit=10):
        """从数据库中获取待抓取的URL并收集"""
        try:
            # 如果limit为1，则获取随机URL；否则获取按顺序排列的URL列表
            if limit == 1:
                random_url = self.db.get_random_pending_url()
                if random_url:
                    url = random_url[0]  # 只需要URL字符串
                    # 过滤屏蔽URL
                    if not self.is_blacklisted(url):
                        print(f"从数据库随机获取了1个待抓取URL")
                        self.start_urls.append(url)
                    else:
                        print("随机获取的URL在屏蔽列表中，跳过")
                else:
                    print("数据库中没有待抓取的URL")
            else:
                pending_urls = self.db.get_pending_urls(limit)
                urls = [url_info[0] for url_info in pending_urls]  # 只需要URL字符串
                
                # 过滤屏蔽URL
                filtered_urls = [url for url in urls if not self.is_blacklisted(url)]
                print(f"从数据库获取了 {len(filtered_urls)} 个待抓取URL (过滤了 {len(urls) - len(filtered_urls)} 个屏蔽URL)")
                self.start_urls.extend(filtered_urls)
            
        except Exception as e:
            print(f"从数据库获取URL失败: {e}")
            return 0
    
    def collect_urls_from_file(self, urls_file):
        """从文件中读取URL并收集"""
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#') and self.is_valid_url(line.strip())]
            
            # 过滤屏蔽URL
            filtered_urls = [url for url in file_urls if not self.is_blacklisted(url)]
            print(f"从文件 {urls_file} 读取了 {len(filtered_urls)} 个有效URL (过滤了 {len(file_urls) - len(filtered_urls)} 个屏蔽URL)")
            self.start_urls.extend(filtered_urls)
            
        except FileNotFoundError:
            print(f"错误: 找不到URL文件: {urls_file}")
            return 0
        except Exception as e:
            print(f"错误: 读取URL文件失败: {e}")
            return 0
    
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
    parser = argparse.ArgumentParser(description='URL收集器（只抓取URL，不下载网页内容）')
    parser.add_argument('--url', action='append', help='起始URL地址（可多次使用）')
    parser.add_argument('--urls-file', help='包含URL列表的文件路径')
    parser.add_argument('--from-database', action='store_true', help='从数据库中获取待抓取的URL')
    parser.add_argument('--limit', type=int, default=10, help='从数据库获取URL的数量限制（默认10）')
    parser.add_argument('--depth', '-d', type=int, default=3, help='最大抓取深度 (默认: 3)')
    parser.add_argument('--workers', '-w', type=int, default=5, help='并发请求数 (默认: 5)')
    parser.add_argument('--output', '-o', default='url_collections', help='输出目录 (默认: url_collections)')
    parser.add_argument('--no-filter', action='store_true', help='禁用关键词过滤，抓取所有页面')
    parser.add_argument('--blacklist', '-b', help='屏蔽URL列表文件路径')
    parser.add_argument('--stats', action='store_true', help='显示统计信息后退出')
    
    args = parser.parse_args()
    
    # 判断是否启用关键词过滤
    enable_keyword_filter = not args.no_filter
    
    # 创建URL收集器
    collector = UrlCollector(
        start_urls=args.url or [],
        max_depth=args.depth,
        output_dir=args.output,
        workers=args.workers,
        enable_keyword_filter=enable_keyword_filter,
        blacklist_file=args.blacklist
    )
    
    if args.stats:
        # 只显示统计信息
        collector.print_database_stats()
        return
    
    # 从数据库获取URL
    if args.from_database:
        collector.collect_urls_from_database(args.limit)
    
    # 从文件读取URL
    if args.urls_file:
        collector.collect_urls_from_file(args.urls_file)
    
    # 收集URL
    collector.collect_urls()


if __name__ == '__main__':
    main()
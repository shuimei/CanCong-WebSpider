import scrapy
from scrapy import Request
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from webspider.items import UrlItem, PageItem
from webspider.database import UrlDatabase, normalize_url, is_valid_url


class WebSpider(scrapy.Spider):
    """通用网页爬虫，支持JavaScript渲染"""
    
    name = 'webspider'
    
    def __init__(self, start_url=None, max_depth=2, enable_keyword_filter=True, *args, **kwargs):
        super(WebSpider, self).__init__(*args, **kwargs)
        
        if not start_url:
            raise ValueError("必须提供start_url参数")
        
        self.start_urls = [start_url]
        self.max_depth = int(max_depth)
        self.db = UrlDatabase()
        
        # 关键词过滤开关
        self.enable_keyword_filter = enable_keyword_filter
        
        # 矿山、自然资源、地质相关关键词
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
            
            # 相关机构和术语
            '国土资源部', '自然资源部', '地质调查局', '矿产资源', '地质公园',
            '地质博物馆', '勘察设计', '地质勘察', '岩土工程', '地基基础',
            '环境影响评价', '水土保持', '生态修复', '绿色矿山', '智慧矿山'
        }
        
        # 将关键词转换为小写以便不区分大小写匹配
        self.target_keywords_lower = {kw.lower() for kw in self.target_keywords}
        
        # 初始化起始URL到数据库
        self.db.add_url(start_url, depth=0)
    
    def start_requests(self):
        """生成初始请求"""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta={
                    'depth': 0,
                    'source_url': None,
                    'render_js': True  # 标记需要JS渲染
                }
            )
    
    def parse(self, response):
        """解析页面并提取URL"""
        url = response.url
        depth = response.meta.get('depth', 0)
        source_url = response.meta.get('source_url')
        
        # 检查响应类型，只处理HTML内容
        content_type = response.headers.get('content-type', b'').decode('utf-8', errors='ignore').lower()
        
        if not self.is_html_content(content_type, url):
            self.logger.info(f"跳过非HTML内容: {url} (Content-Type: {content_type})")
            self.db.mark_failed(url, f"非HTML内容类型: {content_type}")
            return
        
        # 检查响应内容是否为文本
        try:
            html_content = response.text
        except AttributeError:
            self.logger.error(f"无法获取文本内容: {url}")
            self.db.mark_failed(url, "响应内容不是文本格式")
            return
        except Exception as e:
            self.logger.error(f"获取响应内容失败: {url} - {e}")
            self.db.mark_failed(url, str(e))
            return
        
        # 检查HTML内容的有效性
        if not html_content or len(html_content.strip()) < 10:
            self.logger.warning(f"HTML内容过短或为空: {url}")
            self.db.mark_failed(url, "HTML内容为空或过短")
            return
        
        # 关键词过滤：检查页面内容是否与目标主题相关
        if self.enable_keyword_filter and not self.is_content_relevant(html_content, url):
            self.logger.info(f"页面内容不相关，跳过: {url}")
            self.db.mark_failed(url, "页面内容与目标主题不相关")
            return
        
        # 标记当前URL为抓取成功
        self.db.mark_success(url)
        
        # 创建页面数据项
        page_item = PageItem()
        page_item['url'] = url
        page_item['html_content'] = html_content
        page_item['title'] = self.extract_title(html_content)
        page_item['crawl_time'] = response.headers.get('Date', b'').decode('utf-8', errors='ignore')
        
        # 提取页面中的所有URL
        extracted_urls = self.extract_urls(html_content, url)
        page_item['extracted_urls'] = extracted_urls
        
        # 输出页面数据项
        yield page_item
        
        # 如果没有超过最大深度，继续抓取提取的URL
        if depth < self.max_depth:
            for extracted_url in extracted_urls:
                # 过滤不需要的URL
                if not self.should_crawl_url(extracted_url):
                    continue
                    
                # 检查URL是否已经抓取过
                if not self.db.is_crawled(extracted_url):
                    # 添加到数据库
                    if self.db.add_url(extracted_url, source_url=url, depth=depth + 1):
                        # 创建 URL数据项
                        url_item = UrlItem()
                        url_item['url'] = extracted_url
                        url_item['source_url'] = url
                        url_item['depth'] = depth + 1
                        url_item['status'] = 'pending'
                        
                        yield url_item
                        
                        # 生成新的请求
                        yield Request(
                            url=extracted_url,
                            callback=self.parse,
                            meta={
                                'depth': depth + 1,
                                'source_url': url,
                                'render_js': self.needs_js_rendering(extracted_url)
                            },
                            errback=self.handle_error
                        )
    
    def is_content_relevant(self, html_content, url):
        """检查页面内容是否与矿山、自然资源、地质相关"""
        try:
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
            
            # 判断标准：
            # 1. 至少匹配2个关键词，或者
            # 2. 关键词总权重超过5分（考虑重复和权重）
            is_relevant = len(matched_keywords) >= 2 or keyword_count >= 5
            
            if is_relevant:
                self.logger.info(f"相关页面: {url}")
                self.logger.info(f"  匹配关键词: {matched_keywords[:10]}...")  # 只显示前10个
                self.logger.info(f"  关键词权重分: {keyword_count}")
            else:
                self.logger.debug(f"不相关页面: {url}")
                self.logger.debug(f"  匹配关键词: {matched_keywords}")
                self.logger.debug(f"  关键词权重分: {keyword_count}")
            
            return is_relevant
            
        except Exception as e:
            self.logger.error(f"检查内容相关性失败: {url} - {e}")
            # 如果检查失败，默认为相关（避免过度过滤）
            return True
    
    def is_html_content(self, content_type, url):
        """检查内容类型是否为HTML"""
        # 常见的HTML内容类型
        html_types = [
            'text/html',
            'application/xhtml+xml',
            'application/xml',
            'text/xml'
        ]
        
        # 检查Content-Type
        for html_type in html_types:
            if html_type in content_type:
                return True
        
        # 如果没有Content-Type或者为空，根据URL判断
        if not content_type or content_type.strip() == '':
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # 如果没有扩展名或者是HTML扩展名，则假设为HTML
            if not path or path.endswith('/') or path.endswith('.html') or path.endswith('.htm'):
                return True
            
            # 非明显HTML扩展名的静态资源
            static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.rar', '.doc', '.docx']
            if any(path.endswith(ext) for ext in static_extensions):
                return False
        
        return False
    
    def should_crawl_url(self, url):
        """判断URL是否应该抓取"""
        try:
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
            
            # 关键词预过滤：检查URL中是否包含相关关键词
            if self.enable_keyword_filter and not self.is_url_potentially_relevant(url):
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"检查URL失败: {url} - {e}")
            return False
    
    def is_url_potentially_relevant(self, url):
        """检查URL是否可能相关（初步过滤）"""
        url_lower = url.lower()
        
        # 简化的关键词列表，用于URL过滤
        url_keywords = [
            '矿', '地质', '资源', '国土', '自然',
            'mine', 'mining', 'geology', 'resource', 'natural',
            'mineral', 'coal', 'oil', 'gas', 'exploration'
        ]
        
        # 检查URL路径和查询参数中是否包含相关关键词
        for keyword in url_keywords:
            if keyword in url_lower:
                return True
        
        # 如果URL中没有相关关键词，但是是政府或机构网站，也可能相关
        if any(domain in url_lower for domain in ['.gov.', '.org.', '.edu.']):
            return True
        
        # 对于没有明显关键词的URL，默认为不相关
        return False
    
    def extract_title(self, html_content):
        """提取页面标题"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
        except Exception as e:
            self.logger.warning(f"提取标题失败: {e}")
        return None
    
    def extract_urls(self, html_content, base_url):
        """从HTML内容中提取所有URL"""
        urls = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 只提取a标签的href作为可抓取的页面
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = normalize_url(href, base_url)
                if is_valid_url(full_url) and self.should_crawl_url(full_url):
                    urls.add(full_url)
            
            # 可选：也提取iframe的src（可能包含其他页面）
            for iframe in soup.find_all('iframe', src=True):
                src = iframe['src']
                full_url = normalize_url(src, base_url)
                if is_valid_url(full_url) and self.should_crawl_url(full_url):
                    urls.add(full_url)
            
            # 不再提取图片、样式表、脚本等静态资源
            
        except Exception as e:
            self.logger.error(f"提取URL失败: {e}")
        
        return list(urls)
    
    def extract_js_urls(self, html_content, base_url):
        """从JavaScript代码中提取URL（现在主要用于页面URL）"""
        urls = set()
        
        # 匹配JavaScript中的页面URL模式
        patterns = [
            r'["\']https?://[^"\']*\.html?["\']',  # HTML页面URL
            r'["\']https?://[^"\']*/$',            # 目录URL
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                # 移除引号
                url = match.strip('"\'')
                full_url = normalize_url(url, base_url)
                if is_valid_url(full_url) and self.should_crawl_url(full_url):
                    urls.add(full_url)
        
        return urls
    
    def needs_js_rendering(self, url):
        """判断URL是否需要JavaScript渲染"""
        # 根据URL模式判断
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # 静态资源不需要JS渲染
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip']
        if any(path.endswith(ext) for ext in static_extensions):
            return False
        
        return True
    
    def handle_error(self, failure):
        """处理请求错误"""
        request = failure.request
        url = request.url
        error_msg = str(failure.value)
        
        self.logger.error(f"抓取失败 {url}: {error_msg}")
        self.db.mark_failed(url, error_msg)
    
    def closed(self, reason):
        """爬虫关闭时的清理工作"""
        stats = self.db.get_stats()
        self.logger.info(f"爬虫结束，统计信息: {stats}")
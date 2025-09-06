#!/usr/bin/env python3
"""
HTML文件清洗和内容提取脚本
使用流行的HTML转Markdown工具提取网页核心内容
"""

import os
import re
import html2text
import markdownify
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging


class HTMLCleaner:
    """HTML内容清洗器"""
    
    def __init__(self, webpages_dir="webpages", output_dir="mdpages", min_content_length=200, skip_existing=True):
        """
        初始化清洗器
        
        Args:
            webpages_dir: 输入HTML文件目录
            output_dir: 输出Markdown文件目录
            min_content_length: 最小内容长度限制（字符数）
            skip_existing: 是否跳过已存在的转换文件
        """
        self.project_root = Path(__file__).parent.parent
        self.webpages_dir = self.project_root / webpages_dir
        self.output_dir = self.project_root / output_dir
        self.min_content_length = min_content_length
        self.skip_existing = skip_existing
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建错误日志目录
        self.error_log_dir = self.output_dir / 'error_logs'
        self.error_log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 设置文件日志处理器
        log_file = self.error_log_dir / 'html_cleaner.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 配置html2text
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = True  # 忽略链接
        self.h2t.ignore_images = True  # 忽略图片
        self.h2t.ignore_tables = False  # 保留表格
        self.h2t.body_width = 0  # 不限制行宽
        self.h2t.single_line_break = True  # 单行换行
        
        # 需要移除的HTML标签（框架、导航、广告等）
        self.unwanted_tags = [
            'nav', 'header', 'footer', 'aside', 'menu',
            'script', 'style', 'noscript', 'iframe',
            'form', 'input', 'button', 'select', 'textarea',
            'advertisement', 'sidebar', 'banner', 'navigation'
        ]
        
        # 需要移除的CSS类名关键词
        self.unwanted_classes = [
            'nav', 'navigation', 'menu', 'header', 'footer',
            'sidebar', 'aside', 'banner', 'ad', 'advertisement',
            'social', 'share', 'comment', 'pagination',
            'breadcrumb', 'widget', 'toolbar', 'popup',
            'top-menu', 'main-menu', 'sub-menu', 'left-menu',
            'right-menu', 'bottom-menu', 'site-nav', 'page-nav',
            'crumb', 'crumbs', 'bread-crumb', 'path-nav'
        ]
        
        # 需要移除的ID关键词
        self.unwanted_ids = [
            'nav', 'navigation', 'menu', 'header', 'footer',
            'sidebar', 'aside', 'banner', 'ad', 'advertisement',
            'top-nav', 'main-nav', 'sub-nav', 'left-nav',
            'right-nav', 'bottom-nav', 'site-header', 'site-footer'
        ]
        
        # 导航和菜单相关的文本模式
        self.nav_menu_patterns = [
            r'首页[\s|>]*',
            r'主页[\s|>]*', 
            r'网站首页[\s|>]*',
            r'当前位置[\s:：]*',
            r'您当前的位置[\s:：]*',
            r'您现在的位置[\s:：]*',
            r'位置[\s:：]*首页',
            r'导航[\s:：]*',
            r'栏目导航[\s:：]*',
            r'网站导航[\s:：]*',
            r'面包屑[\s:：]*',
            r'>>\s*',
            r'>\s*>\s*',
            r'\|\s*\|',
            r'---+',
            r'更多[>>]*',
            r'查看更多',
            r'返回[上级|首页]*',
            r'打印本页',
            r'关闭窗口',
            r'收藏本页',
            r'分享到',
            r'扫一扫'
        ]
    
    def clean_html(self, html_content):
        """
        清洗HTML内容，移除无关元素
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            清洗后的HTML内容
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. 移除不需要的标签
            for tag_name in self.unwanted_tags:
                for tag in soup.find_all(tag_name):
                    tag.decompose()
            
            # 2. 移除包含特定类名的元素
            for class_keyword in self.unwanted_classes:
                for tag in soup.find_all(class_=re.compile(class_keyword, re.I)):
                    tag.decompose()
            
            # 3. 移除包含特定ID的元素
            for id_keyword in self.unwanted_ids:
                for tag in soup.find_all(id=re.compile(id_keyword, re.I)):
                    tag.decompose()
            
            # 4. 移除所有链接的href属性（保留文本）
            for link in soup.find_all('a'):
                if link.get('href'):
                    del link['href']
            
            # 5. 移除所有图片标签
            for img in soup.find_all('img'):
                img.decompose()
            
            # 6. 移除空的div和span
            for tag in soup.find_all(['div', 'span']):
                if not tag.get_text(strip=True):
                    tag.decompose()
            
            # 7. 提取主要内容区域
            main_content = self.extract_main_content(soup)
            
            return str(main_content) if main_content else str(soup)
            
        except Exception as e:
            self.logger.error(f"HTML清洗失败: {e}")
            return html_content
    
    def filter_navigation_content(self, text):
        """
        过滤导航和菜单内容
        
        Args:
            text: 输入文本
            
        Returns:
            过滤后的文本
        """
        if not text:
            return text
            
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否匹配导航菜单模式
            is_nav_content = False
            for pattern in self.nav_menu_patterns:
                if re.search(pattern, line):
                    is_nav_content = True
                    break
            
            # 检查是否是单独的导航关键词
            nav_keywords = ['首页', '上一页', '下一页', '更多', '返回', '打印', '关闭', '分享']
            if line in nav_keywords:
                is_nav_content = True
            
            # 检查是否只包含特殊字符和空格
            if re.match(r'^[\s|>\-─│├┤┴┬┼—–]*$', line):
                is_nav_content = True
            
            # 检查是否是简短的导航文本（小于5个字符）
            if len(line) <= 5 and any(keyword in line for keyword in ['首页', '导航', '菜单', '更多']):
                is_nav_content = True
            
            if not is_nav_content:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def assess_content_quality(self, text):
        """
        评估内容质量
        
        Args:
            text: 输入文本
            
        Returns:
            质量评分（0-100）和详细信息
        """
        if not text or not text.strip():
            return 0, "内容为空"
        
        text = text.strip()
        
        # 1. 长度得分（20分）
        length_score = min(20, len(text) / 50)  # 每50个字符得1分，最多20分
        
        # 2. 结构完整性得分（20分）
        structure_score = 0
        if '。' in text or '.' in text:  # 包含句号
            structure_score += 5
        if '\n' in text:  # 包含换行
            structure_score += 5
        if len(text.split()) > 10:  # 词汇丰富
            structure_score += 5
        if any(char in text for char in '：，；、'):  # 包含标点符号
            structure_score += 5
            
        # 3. 实质内容比例得分（30分）
        total_chars = len(text)
        
        # 统计实质内容字符（中文、英文、数字）
        substantial_chars = len(re.findall(r'[\u4e00-\u9fffa-zA-Z0-9]', text))
        
        if total_chars > 0:
            substantial_ratio = substantial_chars / total_chars
            content_score = substantial_ratio * 30
        else:
            content_score = 0
            
        # 4. 导航/菜单内容过滤得分（20分）
        nav_score = 20
        for pattern in self.nav_menu_patterns:
            if re.search(pattern, text):
                nav_score -= 5
                if nav_score < 0:
                    nav_score = 0
                    break
        
        # 5. 领域相关性得分（10分）
        domain_score = 0
        
        # 检查是否包含矿山地质领域关键词
        domain_keywords = ['矿', '地质', '自然资源', '地理', '勘探', '地调',
                          '矿物', '地壳', '岩石', '地层', '水文', '环境',
                          '测绘', '规划', '管理', '保护', '开发', '利用']
        
        keyword_count = sum(1 for keyword in domain_keywords if keyword in text)
        domain_score = min(10, keyword_count * 2)
        
        total_score = length_score + structure_score + content_score + nav_score + domain_score
        
        details = {
            'length_score': length_score,
            'structure_score': structure_score, 
            'content_score': content_score,
            'nav_score': nav_score,
            'domain_score': domain_score,
            'text_length': len(text),
            'substantial_ratio': substantial_chars / total_chars if total_chars > 0 else 0,
            'keyword_count': keyword_count
        }
        
        return total_score, details
    
    def extract_main_content(self, soup):
        """
        提取页面主要内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            主要内容的BeautifulSoup对象
        """
        # 常见的主要内容容器标签和属性
        main_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '.main-content', '.article-content',
            '.post-content', '.entry-content', '.page-content',
            '#content', '#main-content', '#article-content'
        ]
        
        # 尝试找到主要内容容器
        for selector in main_selectors:
            try:
                main_element = soup.select_one(selector)
                if main_element and main_element.get_text(strip=True):
                    self.logger.debug(f"找到主要内容: {selector}")
                    return main_element
            except Exception:
                continue
        
        # 如果没找到特定容器，尝试找到最大的文本块
        text_containers = soup.find_all(['div', 'section', 'article'])
        if text_containers:
            # 按文本长度排序
            text_containers.sort(key=lambda x: len(x.get_text()), reverse=True)
            
            # 返回文本最多的容器
            for container in text_containers[:3]:  # 检查前3个
                text_content = container.get_text(strip=True)
                if len(text_content) > 500:  # 至少500字符
                    self.logger.debug(f"使用最大文本容器: {len(text_content)}字符")
                    return container
        
        # 如果都没找到，返回body内容
        body = soup.find('body')
        return body if body else soup
    
    def html_to_markdown(self, html_content, method='html2text'):
        """
        将HTML转换为Markdown
        
        Args:
            html_content: HTML内容
            method: 转换方法 ('html2text' 或 'markdownify')
            
        Returns:
            Markdown内容
        """
        try:
            if method == 'html2text':
                return self.h2t.handle(html_content)
            elif method == 'markdownify':
                return markdownify.markdownify(
                    html_content,
                    heading_style="ATX",  # 使用 # 风格的标题
                    bullets="-",  # 使用 - 作为列表符号
                    strip=['a', 'img'],  # 移除链接和图片
                    convert=['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                            'ul', 'ol', 'li', 'strong', 'em', 'blockquote']
                )
            else:
                self.logger.error(f"不支持的转换方法: {method}")
                return self.h2t.handle(html_content)
                
        except Exception as e:
            self.logger.error(f"Markdown转换失败: {e}")
            return f"# 转换失败\n\n内容转换时出现错误: {e}"
    
    def clean_markdown(self, markdown_content):
        """
        清理Markdown内容
        
        Args:
            markdown_content: 原始Markdown内容
            
        Returns:
            清理后的Markdown内容
        """
        if not markdown_content:
            return ""
            
        # 先过滤导航内容
        filtered_content = self.filter_navigation_content(markdown_content)
        
        # 移除多余的空行
        filtered_content = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_content)
        
        # 移除行首行尾空白
        lines = []
        for line in filtered_content.split('\n'):
            cleaned_line = line.strip()
            lines.append(cleaned_line)
        
        # 重新组合，保持适当的空行
        result = []
        prev_empty = False
        for line in lines:
            if line:
                result.append(line)
                prev_empty = False
            elif not prev_empty:
                result.append('')
                prev_empty = True
        
        final_content = '\n'.join(result).strip()
        
        # 检查内容长度
        if len(final_content) < self.min_content_length:
            raise ValueError(f"内容长度不足：{len(final_content)}字符 < {self.min_content_length}字符")
            
        # 评估内容质量
        quality_score, quality_details = self.assess_content_quality(final_content)
        
        if quality_score < 40:  # 质量阈值
            raise ValueError(f"内容质量不达标：{quality_score:.1f}分 < 40分. 详情: {quality_details}")
        
        return final_content
    
    def generate_filename(self, original_filename, url=None):
        """
        生成输出文件名
        
        Args:
            original_filename: 原始文件名
            url: 原始URL（如果有）
            
        Returns:
            输出文件名
        """
        # 从文件名中提取基础名称
        base_name = Path(original_filename).stem
        
        # 如果有URL，尝试从URL中提取更好的名称
        if url:
            try:
                parsed_url = urlparse(url)
                path_parts = [part for part in parsed_url.path.split('/') if part]
                if path_parts:
                    # 使用URL路径的最后一部分
                    url_name = path_parts[-1]
                    if url_name and url_name != 'index':
                        base_name = url_name
                else:
                    # 使用域名
                    domain_parts = parsed_url.netloc.split('.')
                    if len(domain_parts) >= 2:
                        base_name = domain_parts[-2]  # 主域名
            except Exception:
                pass
        
        # 清理文件名
        base_name = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', base_name)
        base_name = re.sub(r'_+', '_', base_name).strip('_')
        
        if not base_name:
            base_name = "page"
        
        return f"{base_name}.md"
    
    def process_file(self, html_file_path):
        """
        处理单个HTML文件
        
        Args:
            html_file_path: HTML文件路径
            
        Returns:
            处理结果 (success, output_file, message)
        """
        try:
            # 生成输出文件名
            output_filename = self.generate_filename(html_file_path.name)
            output_file_path = self.output_dir / output_filename
            
            # 检查是否跳过已存在的文件
            if self.skip_existing and output_file_path.exists():
                file_size = output_file_path.stat().st_size
                self.logger.info(f"跳过已存在文件: {output_file_path} ({file_size}字节)")
                return True, output_file_path, f"跳过已存在文件 ({file_size}字节)"
            
            self.logger.info(f"处理文件: {html_file_path}")
            
            # 读取HTML文件
            with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            if not html_content.strip():
                raise ValueError("HTML文件为空")
            
            # 清洗HTML
            try:
                cleaned_html = self.clean_html(html_content)
            except Exception as e:
                raise ValueError(f"HTML清洗失败: {e}")
            
            # 转换为Markdown
            try:
                markdown_content = self.html_to_markdown(cleaned_html)
            except Exception as e:
                raise ValueError(f"Markdown转换失败: {e}")
            
            # 清理Markdown并评估质量
            try:
                final_markdown = self.clean_markdown(markdown_content)
            except ValueError as e:
                # 内容质量不达标，记录并跳过
                self.logger.warning(f"跳过低质量文件 {html_file_path.name}: {e}")
                return False, None, str(e)
            except Exception as e:
                raise ValueError(f"Markdown清理失败: {e}")
            
            # 如果文件不存在，则保存；如果存在且不跳过，则创建唯一文件名
            if not self.skip_existing and output_file_path.exists():
                # 确保文件名唯一
                counter = 1
                base_name = output_file_path.stem
                while output_file_path.exists():
                    output_filename = f"{base_name}_{counter}.md"
                    output_file_path = self.output_dir / output_filename
                    counter += 1
            
            # 保存Markdown文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown)
            
            file_size = len(final_markdown)
            self.logger.info(f"处理完成: {output_file_path} ({file_size}字符)")
            
            return True, output_file_path, f"成功提取 {file_size} 字符"
            
        except Exception as e:
            error_msg = f"处理失败: {e}"
            self.logger.error(f"{html_file_path.name} - {error_msg}")
            
            # 将错误信息写入错误日志文件
            error_log_file = self.error_log_dir / f"{html_file_path.stem}_error.log"
            try:
                with open(error_log_file, 'w', encoding='utf-8') as f:
                    f.write(f"文件: {html_file_path}\n")
                    f.write(f"错误: {error_msg}\n")
                    f.write(f"时间: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n")
            except Exception:
                pass  # 忽略日志文件写入错误
            
            return False, None, error_msg
    
    def process_all_files(self):
        """
        处理所有HTML文件
        
        Returns:
            处理结果统计
        """
        if not self.webpages_dir.exists():
            self.logger.error(f"输入目录不存在: {self.webpages_dir}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'results': []
            }
        
        # 找到所有HTML文件
        html_files = list(self.webpages_dir.glob('*.html'))
        
        if not html_files:
            self.logger.warning(f"在 {self.webpages_dir} 中没有找到HTML文件")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'results': []
            }
        
        self.logger.info(f"找到 {len(html_files)} 个HTML文件")
        
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0  # 质量过滤跳过数量
        existing_count = 0  # 已存在文件跳过数量
        
        for html_file in html_files:
            success, output_file, message = self.process_file(html_file)
            
            result = {
                'input_file': str(html_file),
                'output_file': str(output_file) if output_file else None,
                'success': success,
                'message': message
            }
            results.append(result)
            
            if success:
                if '跳过已存在文件' in message:
                    existing_count += 1
                else:
                    success_count += 1
            elif '质量不达标' in message or '内容长度不足' in message:
                skipped_count += 1
            else:
                failed_count += 1
        
        return {
            'total': len(html_files),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'existing': existing_count,  # 新增返回值
            'results': results
        }


def main():
    """主函数"""
    import argparse
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='HTML内容清洗和提取工具')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='强制重新处理所有文件，不跳过已存在的文件')
    parser.add_argument('--min-length', '-l', type=int, default=200,
                       help='最小内容长度限制（默认200字符）')
    
    args = parser.parse_args()
    
    print("HTML内容清洗和提取工具")
    print("=" * 50)
    
    # 创建清洗器
    skip_existing = not args.force  # --force 参数反转为 skip_existing
    cleaner = HTMLCleaner(
        min_content_length=args.min_length,
        skip_existing=skip_existing
    )
    
    print(f"输入目录: {cleaner.webpages_dir}")
    print(f"输出目录: {cleaner.output_dir}")
    if skip_existing:
        print(f"模式: 跳过已存在文件")
    else:
        print(f"模式: 强制重新处理所有文件")
    print(f"最小内容长度: {cleaner.min_content_length} 字符")
    print()
    
    # 处理所有文件
    results = cleaner.process_all_files()
    
    # 显示结果
    print("处理结果:")
    print(f"  总计文件: {results['total']}")
    print(f"  新处理: {results['success']}")
    print(f"  跳过已存在: {results['existing']}")
    print(f"  质量过滤: {results['skipped']}")
    print(f"  处理失败: {results['failed']}")
    
    if results['failed'] > 0:
        print("\n处理失败文件:")
        for result in results['results']:
            if not result['success'] and not ('质量不达标' in result['message'] or '内容长度不足' in result['message']):
                print(f"  - {Path(result['input_file']).name}: {result['message']}")
    
    if results['skipped'] > 0:
        print("\n质量过滤文件:")
        for result in results['results']:
            if not result['success'] and ('质量不达标' in result['message'] or '内容长度不足' in result['message']):
                print(f"  - {Path(result['input_file']).name}: {result['message']}")
    
    total_processed = results['success'] + results['existing']
    if total_processed > 0:
        print(f"\n成功提取 {total_processed} 个高质量文件到 {cleaner.output_dir}")
        if results['success'] > 0:
            print(f"  - 本次新处理: {results['success']} 个")
        if results['existing'] > 0:
            print(f"  - 跳过已存在: {results['existing']} 个")
        print(f"\n质量标准:")
        print(f"  - 最小内容长度: {cleaner.min_content_length} 字符")
        print(f"  - 内容质量阈值: 40分")
        print(f"  - 已过滤导航菜单内容")
        print("\n处理完成！您现在可以在 mdpages 目录中查看提取的高质量Markdown内容。")
        print(f"\n错误日志保存在: {cleaner.error_log_dir}")
    else:
        print("\n没有成功处理任何文件")
        
    # 显示使用提示
    if skip_existing:
        print("\n提示: 使用 --force 或 -f 参数可以强制重新处理所有文件")


if __name__ == '__main__':
    main()
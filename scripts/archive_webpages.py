#!/usr/bin/env python3
"""
网页文件打包归档脚本
将webpages目录中的HTML文件打包为ZIP文件，并可选择删除原文件
"""

import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import argparse


class WebpageArchiver:
    """网页文件归档器"""
    
    def __init__(self, webpages_dir="webpages", output_dir="archives"):
        """
        初始化归档器
        
        Args:
            webpages_dir: 网页文件目录
            output_dir: 归档输出目录
        """
        self.project_root = Path(__file__).parent.parent
        self.webpages_dir = self.project_root / webpages_dir
        self.output_dir = self.project_root / output_dir
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"网页文件归档器初始化完成")
        print(f"源目录: {self.webpages_dir}")
        print(f"输出目录: {self.output_dir}")
    
    def get_html_files(self):
        """获取所有HTML文件列表"""
        if not self.webpages_dir.exists():
            print(f"警告: 源目录不存在: {self.webpages_dir}")
            return []
        
        html_files = list(self.webpages_dir.glob('*.html'))
        print(f"找到 {len(html_files)} 个HTML文件")
        return html_files
    
    def create_archive_filename(self):
        """生成归档文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"webpages_archive_{timestamp}.zip"
    
    def create_zip_archive(self, html_files, archive_path, compression_level=6):
        """
        创建ZIP归档文件
        
        Args:
            html_files: HTML文件列表
            archive_path: 归档文件路径
            compression_level: 压缩级别 (0-9)
        
        Returns:
            成功创建的文件数量
        """
        success_count = 0
        total_size = 0
        
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                for html_file in html_files:
                    try:
                        # 获取文件信息
                        file_size = html_file.stat().st_size
                        total_size += file_size
                        
                        # 添加到ZIP文件，使用相对路径
                        arcname = html_file.name
                        zipf.write(html_file, arcname)
                        success_count += 1
                        
                        if success_count % 100 == 0:
                            print(f"已处理 {success_count} 个文件...")
                            
                    except Exception as e:
                        print(f"添加文件失败 {html_file.name}: {e}")
                        continue
            
            # 获取压缩后文件大小
            compressed_size = archive_path.stat().st_size
            compression_ratio = (1 - compressed_size / total_size) * 100 if total_size > 0 else 0
            
            print(f"\n📦 归档创建完成:")
            print(f"  归档文件: {archive_path}")
            print(f"  包含文件: {success_count} 个")
            print(f"  原始大小: {self.format_size(total_size)}")
            print(f"  压缩大小: {self.format_size(compressed_size)}")
            print(f"  压缩率: {compression_ratio:.1f}%")
            
            return success_count
            
        except Exception as e:
            print(f"创建归档文件失败: {e}")
            return 0
    
    def format_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def delete_original_files(self, html_files, confirmed=False):
        """
        删除原始HTML文件
        
        Args:
            html_files: 要删除的HTML文件列表
            confirmed: 是否已确认删除
        
        Returns:
            成功删除的文件数量
        """
        if not confirmed:
            response = input(f"\n⚠️  确认删除 {len(html_files)} 个原始HTML文件? (yes/no): ")
            if response.lower() not in ['yes', 'y', '是']:
                print("取消删除操作")
                return 0
        
        deleted_count = 0
        
        for html_file in html_files:
            try:
                html_file.unlink()
                deleted_count += 1
                
                if deleted_count % 100 == 0:
                    print(f"已删除 {deleted_count} 个文件...")
                    
            except Exception as e:
                print(f"删除文件失败 {html_file.name}: {e}")
                continue
        
        print(f"\n🗑️  删除完成: {deleted_count} 个文件")
        return deleted_count
    
    def archive_and_cleanup(self, delete_originals=False, auto_confirm=False, compression_level=6):
        """
        执行归档和清理操作
        
        Args:
            delete_originals: 是否删除原文件
            auto_confirm: 是否自动确认删除
            compression_level: 压缩级别
        
        Returns:
            操作结果字典
        """
        # 获取HTML文件列表
        html_files = self.get_html_files()
        
        if not html_files:
            print("没有找到HTML文件，操作取消")
            return {'success': False, 'message': '没有文件需要归档'}
        
        # 创建归档文件名
        archive_filename = self.create_archive_filename()
        archive_path = self.output_dir / archive_filename
        
        print(f"\n开始创建归档文件: {archive_filename}")
        
        # 创建ZIP归档
        success_count = self.create_zip_archive(html_files, archive_path, compression_level)
        
        if success_count == 0:
            print("归档创建失败")
            return {'success': False, 'message': '归档创建失败'}
        
        # 验证归档文件
        if not self.verify_archive(archive_path, len(html_files)):
            print("⚠️  归档文件验证失败，建议检查文件完整性")
        
        result = {
            'success': True,
            'archive_path': str(archive_path),
            'archived_files': success_count,
            'deleted_files': 0
        }
        
        # 可选删除原文件
        if delete_originals:
            deleted_count = self.delete_original_files(html_files, auto_confirm)
            result['deleted_files'] = deleted_count
            
            if deleted_count == success_count:
                print(f"\n✅ 归档和清理完成!")
            else:
                print(f"\n⚠️  归档完成，但删除了 {deleted_count}/{success_count} 个文件")
        else:
            print(f"\n✅ 归档完成! 原文件保留在 {self.webpages_dir}")
        
        return result
    
    def verify_archive(self, archive_path, expected_count):
        """验证归档文件完整性"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # 检查文件数量
                actual_count = len(zipf.namelist())
                if actual_count != expected_count:
                    print(f"文件数量不匹配: 期望 {expected_count}, 实际 {actual_count}")
                    return False
                
                # 测试所有文件
                bad_files = zipf.testzip()
                if bad_files:
                    print(f"发现损坏的文件: {bad_files}")
                    return False
                
                print(f"✅ 归档文件验证成功: {actual_count} 个文件")
                return True
                
        except Exception as e:
            print(f"验证归档文件时出错: {e}")
            return False
    
    def list_archives(self):
        """列出已有的归档文件"""
        archive_files = list(self.output_dir.glob('webpages_archive_*.zip'))
        
        if not archive_files:
            print("没有找到归档文件")
            return
        
        print(f"\n📁 已有归档文件 ({len(archive_files)} 个):")
        
        # 按时间排序
        archive_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for archive_file in archive_files:
            stat = archive_file.stat()
            size = self.format_size(stat.st_size)
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取ZIP文件中的文件数量
            try:
                with zipfile.ZipFile(archive_file, 'r') as zipf:
                    file_count = len(zipf.namelist())
                print(f"  {archive_file.name} - {size} - {file_count} 个文件 - {mtime}")
            except:
                print(f"  {archive_file.name} - {size} - 未知文件数 - {mtime}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网页文件归档工具')
    parser.add_argument('--delete', '-d', action='store_true',
                       help='归档后删除原始文件')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='自动确认删除操作，不提示用户')
    parser.add_argument('--compression', '-c', type=int, default=6, choices=range(0, 10),
                       help='压缩级别 (0-9, 默认6)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='列出已有的归档文件')
    parser.add_argument('--webpages-dir', type=str, default='webpages',
                       help='网页文件目录 (默认: webpages)')
    parser.add_argument('--output-dir', type=str, default='archives',
                       help='归档输出目录 (默认: archives)')
    
    args = parser.parse_args()
    
    # 创建归档器
    archiver = WebpageArchiver(
        webpages_dir=args.webpages_dir,
        output_dir=args.output_dir
    )
    
    if args.list:
        # 列出已有归档文件
        archiver.list_archives()
        return
    
    # 执行归档操作
    print(f"\n🗄️  网页文件归档工具")
    print("=" * 50)
    
    result = archiver.archive_and_cleanup(
        delete_originals=args.delete,
        auto_confirm=args.yes,
        compression_level=args.compression
    )
    
    if result['success']:
        print(f"\n📊 操作统计:")
        print(f"  归档文件: {Path(result['archive_path']).name}")
        print(f"  归档文件数: {result['archived_files']}")
        if result['deleted_files'] > 0:
            print(f"  删除文件数: {result['deleted_files']}")
        
        print(f"\n💡 提示:")
        print(f"  - 归档文件保存在: {archiver.output_dir}")
        print(f"  - 使用 --list 查看所有归档文件")
        if not args.delete:
            print(f"  - 使用 --delete 参数可在归档后删除原文件")
    else:
        print(f"\n❌ 操作失败: {result.get('message', '未知错误')}")


if __name__ == '__main__':
    main()
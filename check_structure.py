#!/usr/bin/env python3
"""
检查项目文件结构的完整性
"""

import os
from pathlib import Path


def check_project_structure():
    """检查项目结构是否完整"""
    
    project_root = Path(__file__).parent
    
    # 定义期望的文件结构
    expected_structure = {
        # 根目录文件
        'files': [
            'README.md',
            'requirements.txt', 
            'scrapy.cfg',
            'spider.py',
            'run_spider.py',
            'spider_urls.db'
        ],
        
        # 目录和其中的关键文件
        'directories': {
            'webspider': ['__init__.py', 'settings.py', 'items.py', 'database.py', 'middlewares.py', 'pipelines.py'],
            'webspider/spiders': ['__init__.py', 'webspider.py'],
            'frontend': ['main.py'],
            'frontend/templates': ['index.html'],
            'scripts': ['install.bat', 'start_monitor.bat', 'start_monitor.py'],
            'tests': ['test_spider.py', 'test_random.py', 'test_keyword_filter.py', 'test_chart.py', 'test_web_monitor.py'],
            'examples': ['keyword_filter_demo.py'],
            'docs': ['项目结构说明.md', '使用指南.md', '快速使用指南.md', '关键词过滤功能说明.md'],
            'webpages': []  # 可能为空，不检查具体文件
        }
    }
    
    print("🔍 检查项目文件结构...")
    print("=" * 50)
    
    missing_files = []
    missing_dirs = []
    
    # 检查根目录文件
    print("📄 检查根目录文件:")
    for file_name in expected_structure['files']:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name}")
            missing_files.append(file_name)
    
    print()
    
    # 检查目录结构
    print("📁 检查目录结构:")
    for dir_name, files in expected_structure['directories'].items():
        dir_path = project_root / dir_name
        
        if dir_path.exists() and dir_path.is_dir():
            print(f"  📁 {dir_name}/")
            
            # 检查目录中的文件（如果不是webpages目录）
            if dir_name != 'webpages':
                for file_name in files:
                    file_path = dir_path / file_name
                    if file_path.exists():
                        print(f"    ✅ {file_name}")
                    else:
                        print(f"    ❌ {file_name}")
                        missing_files.append(f"{dir_name}/{file_name}")
            else:
                file_count = len(list(dir_path.glob('*')))
                print(f"    📊 包含 {file_count} 个文件")
        else:
            print(f"  ❌ {dir_name}/ (目录不存在)")
            missing_dirs.append(dir_name)
    
    print()
    print("=" * 50)
    
    # 总结结果
    if not missing_files and not missing_dirs:
        print("🎉 项目结构完整！")
        print("✅ 所有必需的文件和目录都存在")
        return True
    else:
        print("⚠️ 项目结构不完整")
        
        if missing_dirs:
            print(f"\n❌ 缺失的目录 ({len(missing_dirs)}):")
            for dir_name in missing_dirs:
                print(f"  - {dir_name}/")
        
        if missing_files:
            print(f"\n❌ 缺失的文件 ({len(missing_files)}):")
            for file_name in missing_files:
                print(f"  - {file_name}")
        
        return False


def show_current_structure():
    """显示当前的项目结构"""
    
    project_root = Path(__file__).parent
    
    print("\n🗂️ 当前项目结构:")
    print("=" * 50)
    
    def print_tree(path, prefix="", max_depth=3, current_depth=0):
        """递归打印目录树"""
        if current_depth > max_depth:
            return
            
        items = []
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            
            if item.is_file():
                size = item.stat().st_size
                size_str = f" ({size:,} bytes)" if size < 1024*1024 else f" ({size/(1024*1024):.1f}MB)"
                print(f"{prefix}{current_prefix}{item.name}{size_str}")
            else:
                print(f"{prefix}{current_prefix}{item.name}/")
                
                # 递归打印子目录（除了__pycache__等）
                if item.name not in ['__pycache__', '.git', '.idea', 'node_modules'] and current_depth < max_depth:
                    extension = "    " if is_last else "│   "
                    print_tree(item, prefix + extension, max_depth, current_depth + 1)
    
    print_tree(project_root)


def main():
    """主函数"""
    print("🏗️ 项目结构检查工具")
    print("=" * 50)
    
    # 检查结构完整性
    is_complete = check_project_structure()
    
    # 显示当前结构
    show_current_structure()
    
    print("\n" + "=" * 50)
    if is_complete:
        print("✅ 项目结构检查完成 - 所有必需文件都存在")
        print("\n🚀 您可以开始使用爬虫:")
        print("  python spider.py https://mnr.gov.cn")
        print("  python scripts/start_monitor.py")
    else:
        print("⚠️ 项目结构不完整，某些功能可能无法正常工作")
        print("\n🔧 建议:")
        print("  1. 检查是否正确移动了所有文件")
        print("  2. 重新运行文件整理脚本")
        print("  3. 手动创建缺失的目录和文件")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
清理重复的Markdown文件（删除带_1后缀的重复文件）
"""

import os
from pathlib import Path

def clean_duplicate_files():
    """清理重复文件"""
    project_root = Path(__file__).parent.parent
    mdpages_dir = project_root / 'mdpages'
    
    if not mdpages_dir.exists():
        print("mdpages目录不存在")
        return
    
    # 找到所有带_1后缀的文件
    duplicate_files = list(mdpages_dir.glob('*_1.md'))
    
    print(f"找到 {len(duplicate_files)} 个重复文件")
    
    deleted_count = 0
    for file_path in duplicate_files:
        try:
            os.remove(file_path)
            deleted_count += 1
            print(f"删除: {file_path.name}")
        except Exception as e:
            print(f"删除失败 {file_path.name}: {e}")
    
    print(f"成功删除 {deleted_count} 个重复文件")
    
    # 统计剩余文件
    remaining_files = list(mdpages_dir.glob('*.md'))
    print(f"剩余文件: {len(remaining_files)} 个")

if __name__ == '__main__':
    clean_duplicate_files()

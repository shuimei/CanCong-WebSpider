#!/usr/bin/env python3
"""
自动调度器测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.auto_scheduler import AutoSpiderScheduler


def test_scheduler():
    """测试调度器功能"""
    print("测试自动调度器...")
    
    # 创建调度器实例
    scheduler = AutoSpiderScheduler(
        batch_size=1,
        max_depth=2,
        workers=1,
        delay_between_batches=2
    )
    
    # 显示统计信息
    scheduler.print_stats()
    
    print("测试完成")


if __name__ == '__main__':
    test_scheduler()
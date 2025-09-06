#!/usr/bin/env python3
"""
启动爬虫监控Web界面
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 获取当前脚本目录的父目录（项目根目录）
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / 'frontend'
    
    # 检查frontend目录和main.py是否存在
    main_py = frontend_dir / 'main.py'
    if not main_py.exists():
        print("错误: 找不到frontend/main.py文件")
        print(f"当前查找路径: {main_py}")
        return False
    
    # 切换到frontend目录
    os.chdir(str(frontend_dir))
    
    print("🚀 启动爬虫监控Web界面...")
    print(f"📁 工作目录: {frontend_dir}")
    print("🌐 访问地址: http://localhost:8000")
    print("📊 API文档: http://localhost:8000/docs")
    print("-" * 50)
    
    try:
        # 启动FastAPI应用
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 监控界面已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ 错误: 未找到uvicorn，请先安装FastAPI依赖:")
        print("   pip install fastapi uvicorn[standard]")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
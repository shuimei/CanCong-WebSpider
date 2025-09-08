@echo off
REM 自动爬虫调度器启动脚本

echo 启动自动爬虫调度器...
echo.

cd /d E:\projects\CanCong-WebSpider

REM 检查是否提供了参数
if "%1"=="" (
    echo 使用默认参数启动调度器...
    python scripts/auto_scheduler.py
) else (
    echo 使用自定义参数启动调度器...
    python scripts/auto_scheduler.py %*
)

echo.
echo 调度器已退出。
pause
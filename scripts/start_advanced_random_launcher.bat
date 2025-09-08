@echo off
REM 高级随机URL启动器启动脚本

cd /d "%~dp0"
cd ..

echo 启动高级随机URL启动器...
python scripts\advanced_random_launcher.py %*

pause
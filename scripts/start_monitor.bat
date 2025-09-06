@echo off
echo 启动爬虫监控Web界面...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo 正在安装Web界面依赖...
    pip install fastapi uvicorn[standard] python-multipart jinja2
)

echo.
echo 启动监控界面...
echo 访问地址: http://localhost:8000
echo 按 Ctrl+C 停止服务
echo.

python start_monitor.py

pause
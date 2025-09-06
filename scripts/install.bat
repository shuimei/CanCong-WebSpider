@echo off
echo 安装网页爬虫依赖...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo Python已安装
echo.

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 安装项目依赖...
pip install -r requirements.txt

REM 安装Chrome WebDriver管理器
echo 安装Chrome WebDriver管理器...
pip install webdriver-manager

echo.
echo 安装完成！
echo.
echo 使用方法：
echo   python spider.py https://example.com
echo   python spider.py  (交互式模式)
echo.
echo 更多信息请查看 README.md
echo.
pause
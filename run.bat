@echo off
chcp 65001 >nul
echo ======================================
echo         LOL 辅助工具启动器
echo ======================================
echo.
echo 正在启动程序...
echo.

python main_window.py

if errorlevel 1 (
    echo.
    echo 程序运行出错！
    echo 请检查：
    echo 1. 是否已安装Python 3.8+
    echo 2. 是否已安装依赖库
    echo    运行: pip install -r requirements.txt
    echo.
    pause
)

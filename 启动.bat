@echo off
chcp 65001 >nul
title 戏韵千秋 - 京剧数据可视分析系统

echo.
echo ╔══════════════════════════════════════╗
echo ║    戏韵千秋 · 京剧数据可视分析系统    ║
echo ║         ChinaVis 2026               ║
echo ╚══════════════════════════════════════╝
echo.
echo 正在启动本地服务器...

cd /d "%~dp0"

start "" http://localhost:8899/opera_dashboard.html

python -m http.server 8899

pause

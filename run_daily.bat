@echo off
chcp 65001 >nul
REM ============================================================
REM  盘前全球市场简报 · 每日数据更新
REM  用法：双击运行，或由 Windows 任务计划在每个交易日 07:35 调用
REM ============================================================
set PY=C:\Users\z\.workbuddy\binaries\python\versions\3.13.12\python.exe
set DIR=C:\Users\z\WorkBuddy\2026-11-14-05-42-06
cd /d "%DIR%"
"%PY%" tools\update_market_data.py
echo.
echo 数据已更新至 site\data.js，刷新页面即可查看最新简报。
timeout /t 3 >nul

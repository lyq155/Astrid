@echo off
chcp 65001 >nul
cd /d "C:\Users\z\WorkBuddy\2026-11-14-05-42-06"
echo ============================================
echo   正在推送代码到 GitHub: lyq155/Astrid
echo ============================================
echo.
git push -u origin main
echo.
echo ============================================
if %ERRORLEVEL%==0 (
   echo   推送成功！
) else (
   echo   推送失败，错误码 %ERRORLEVEL%
)
echo ============================================
echo.
echo 按任意键关闭窗口...
pause >nul

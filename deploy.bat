@echo off
chcp 65001 >nul
echo ========================================
echo   AI资讯自动推送系统 - 快速部署工具
echo ========================================
echo.

echo [1/5] 检查文件完整性...
if not exist "ai_news_collector.py" (
    echo ❌ 缺少核心脚本文件！
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo ❌ 缺少依赖配置文件！
    pause
    exit /b 1
)
if not exist ".github\workflows\ai-news-daily.yml" (
    echo ❌ 缺少GitHub Actions配置！
    pause
    exit /b 1
)
echo ✅ 文件检查完成

echo.
echo [2/5] 初始化Git仓库...
if not exist ".git" (
    git init
    echo ✅ Git仓库初始化完成
) else (
    echo ℹ️ Git仓库已存在
)

echo.
echo [3/5] 添加文件到Git...
git add .
git status
echo ✅ 文件已添加

echo.
echo [4/5] 提交代码...
git commit -m "Add AI news auto-push system - Initial commit"
echo ✅ 代码已提交

echo.
echo [5/5] 推送到GitHub...
echo.
echo ⚠️ 请手动执行以下命令完成推送：
echo.
echo    git remote add origin https://github.com/paranoiawang0818/ai-news-collector.git
echo    git branch -M main
echo    git push -u origin main
echo.

echo ========================================
echo   📋 下一步操作清单
echo ========================================
echo.
echo 1. 在GitHub创建新仓库（如果还没有）
echo    仓库名建议：ai-news-collector
echo.
echo 2. 执行上面的推送命令
echo.
echo 3. 配置GitHub Secrets（必须！）
echo    - SENDER_EMAIL: 你的QQ邮箱
echo    - SENDER_PASSWORD: QQ邮箱授权码
echo    - RECEIVER_EMAIL: paranoiawang0818@qq.com
echo.
echo 4. 启用GitHub Actions
echo.
echo 5. 手动触发测试运行
echo.
echo ========================================
echo   详细文档请查看 README.md
echo ========================================
echo.
pause

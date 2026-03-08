#!/bin/bash
# 一键安装所有依赖（Python 包 + Chromium 浏览器）

set -e

echo "📦 安装 Python 依赖..."
pip install -r requirements.txt

echo ""
echo "🌐 安装 Chrome 浏览器依赖..."
playwright install chrome

echo ""
echo "✅ 全部安装完成！"
echo "   下一步：运行 python main.py"
echo "   （首次运行会自动引导你登录各平台）"

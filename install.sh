#!/bin/bash
# 一键安装所有依赖（Python 包 + Chromium 浏览器）

set -e

echo "📦 安装 Python 依赖..."
pip install -r requirements.txt

echo ""
echo "🌐 安装 Chromium 浏览器..."
playwright install chromium

echo ""
echo "✅ 全部安装完成！"
echo "   下一步："
echo "   1. 首次使用请运行: python setup_login.py"
echo "   2. 正式运行: python main.py"

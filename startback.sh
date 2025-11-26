#!/bin/bash
# MLX DeepSeek-OCR 启动脚本

echo "🚀 启动 MLX DeepSeek-OCR 应用..."
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python3 --version

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 发现虚拟环境，正在激活..."
    source venv/bin/activate
else
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 检查依赖
echo ""
echo "📦 检查依赖..."
if ! python3 -c "import flask" 2>/dev/null || ! python3 -c "import mlx_vlm" 2>/dev/null || ! python3 -c "from PIL import Image" 2>/dev/null; then
    echo "⚠️  缺少依赖，正在安装..."
    echo "⏳ 这可能需要几分钟时间..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ 依赖安装完成"
    else
        echo "❌ 依赖安装失败，请检查错误信息"
        exit 1
    fi
else
    echo "✅ 依赖已安装"
fi

# 启动应用
echo ""
echo "🎯 启动 Flask 应用..."
echo "📍 访问地址: http://localhost:5000"
echo "🛑 按 Ctrl+C 停止应用"
echo ""

python3 app.py


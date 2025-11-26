#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MLX DeepSeek-OCR.
# Copyright (C) 2025 MLX DeepSeek-OCR contributors
# Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
# See the LICENSE file in the project root for full license text:
# https://www.gnu.org/licenses/agpl-3.0.en.html

# MLX DeepSeek-OCR 終極啟動腳本（強制殺港 + 直傳 port + 永不衝突）

echo "啟動 MLX DeepSeek-OCR 應用..."
echo ""

cd "$(dirname "$0")"

echo "檢查 Python 版本..."
python3 --version

# 虛擬環境
if [ -d "venv" ]; then
    echo "發現虛擬環境，正在激活..."
    source venv/bin/activate
else
    echo "創建虛擬環境..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 檢查依賴
echo ""
echo "檢查依賴..."
MISSING=false
python3 -c "import flask" 2>/dev/null || MISSING=true
python3 -c "import mlx_vlm" 2>/dev/null || MISSING=true
python3 -c "from PIL import Image" 2>/dev/null || MISSING=true
python3 -c "import fitz" 2>/dev/null || MISSING=true  # PDF 解析必備

if [ "$MISSING" = true ]; then
    echo "缺少依賴，正在安裝..."
    pip install -r requirements.txt
    [ $? -eq 0 ] && echo "依賴安裝完成" || { echo "安裝失敗"; exit 1; }
else
    echo "依賴已安裝"
fi

# 自動尋找可用端口 + 強制殺掉殭屍進程
PORT=5000
MAX_PORT=5010
echo ""
echo "尋找可用端口並清理殭屍進程..."

while [ $PORT -le $MAX_PORT ]; do
    if lsof -i:$PORT >/dev/null 2>&1; then
        echo "端口 $PORT 被佔用，嘗試殺掉進程..."
        lsof -i:$PORT | grep python | awk '{print $2}' | xargs kill -9 2>/dev/null || true
        if lsof -i:$PORT >/dev/null 2>&1; then
            echo "無法釋放端口 $PORT，嘗試下一個..."
            ((PORT++))
        else
            echo "成功釋放並使用端口: $PORT"
            break
        fi
    else
        echo "找到可用端口: $PORT"
        break
    fi
done

if [ $PORT -gt $MAX_PORT ]; then
    echo "錯誤：無法找到可用端口（5000-5010）"
    exit 1
fi

echo ""
echo "強制啟動 Flask 應用（直傳 port，無視 app.py 硬編碼）"
echo "訪問地址: http://localhost:$PORT"
echo "按 Ctrl+C 安全停止"
echo ""

# 強制監聽所有介面 + 關閉 reload（避免雙進程）
PORT=$PORT python3 app.py

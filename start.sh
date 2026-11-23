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

# 自動更新到最新版（失敗不影響啟動）
if [ -d .git ] && [ -z "$MLX_OCR_UPDATED" ]; then
  echo "檢查更新..."
  OLD=$(git rev-parse HEAD)
  if git pull --ff-only -q 2>/dev/null; then
    if [ "$OLD" != "$(git rev-parse HEAD)" ]; then
      echo "已更新到最新版，重新啟動..."
      MLX_OCR_UPDATED=1 exec "$0" "$@"
    fi
    echo "已是最新版"
  else
    echo "⚠️ 無法自動更新（離線或有本機修改），用目前版本繼續"
  fi
fi

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

# 檢查依賴：版本不對的自動換掉，缺的自動補
echo ""
echo "檢查依賴版本..."
pip install -q -r requirements.txt || { echo "安裝失敗"; exit 1; }
echo "依賴版本正確"

# 檢查 OCR 模型（鎖定 2025-10-27 版，第一次會下載約 3.9 GB）
echo ""
echo "檢查 OCR 模型（第一次會下載約 3.9 GB）..."
HF_HOME="$HOME/hf_cache" python3 -c "from huggingface_hub import snapshot_download as d; import os; r='mlx-community/DeepSeek-OCR-8bit'; v='148305747fad0be1d6f417d3c7cb477216c63a90'
try: p=d(r, revision=v)
except Exception: p=d(r, revision=v, local_files_only=True)
assert os.path.exists(os.path.join(p,'model.safetensors')), '模型不完整'" || { echo "模型下載失敗或不完整，請檢查網路後重新執行 ./start.sh"; exit 1; }

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

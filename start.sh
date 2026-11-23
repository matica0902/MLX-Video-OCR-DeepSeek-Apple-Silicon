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
# 優先用 3.11，其次 3.12 / 3.13，都沒有才用 python3
PY=""
for p in python3.11 python3.12 python3.13 python3; do
    if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
        PY="$p"; break
    fi
done
# 沒有 3.11 以上：下載獨立版 Python 3.11.18 到專案資料夾（不動系統，刪資料夾即移除）
if [ -z "$PY" ] && [ -x ".python/bin/python3.11" ]; then
    PY=".python/bin/python3.11"
fi
if [ -z "$PY" ]; then
    if [ "$(uname -m)" != "arm64" ]; then
        echo "❌ 需要 Apple Silicon (M1/M2/M3/M4) Mac"; exit 1
    fi
    echo ""
    echo "找不到 Python 3.11 以上（目前: $(python3 --version 2>&1)）"
    echo "本專案需要 Python 3.11+。可以下載專案專用的 Python 3.11.18（約 27 MB）："
    echo "  • 只放在本專案的 .python/ 資料夾，不會修改系統的 Python"
    echo "  • 來源 python-build-standalone，下載後會驗證 SHA256"
    echo "  • 刪除本專案資料夾即完全移除"
    if [ -t 0 ]; then
        read -r -p "要下載嗎？[Y/n] " ans
    else
        ans="n"
    fi
    case "$ans" in
        ""|y|Y|yes|YES) ;;
        *) echo "已取消。也可以自行安裝：brew install python@3.11，再重新執行 ./start.sh"; exit 1 ;;
    esac
    echo "下載中..."
    PBS_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20261110/cpython-3.11.18%2B20261110-aarch64-apple-darwin-install_only.tar.gz"
    PBS_SHA="73f1ed14486aa278d331e95f7d6d452f5cfb69d90b418e26e62fd4846d53557d"
    curl -fL --retry 3 -o .python.tgz "$PBS_URL" || { echo "❌ Python 下載失敗，請檢查網路後重新執行 ./start.sh"; rm -f .python.tgz; exit 1; }
    echo "$PBS_SHA  .python.tgz" | shasum -a 256 -c - >/dev/null || { echo "❌ Python 檔案驗證失敗，已刪除"; rm -f .python.tgz; exit 1; }
    rm -rf .python && mkdir .python && tar -xzf .python.tgz -C .python --strip-components 1 && rm -f .python.tgz
    PY=".python/bin/python3.11"
fi
"$PY" --version

# 虛擬環境：版本太舊的 venv 自動重建
if [ -d "venv" ] && ! venv/bin/python -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    echo "虛擬環境的 Python 版本太舊，重新建立..."
    rm -rf venv
fi
if [ -d "venv" ]; then
    echo "發現虛擬環境，正在激活..."
    source venv/bin/activate
else
    echo "創建虛擬環境（$PY）..."
    "$PY" -m venv venv
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

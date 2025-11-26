# MLX DeepSeek-OCR

專為 macOS Apple Silicon (M1/M2/M3/M4) 優化的高效能 OCR 解決方案，基於 MLX 框架和 DeepSeek-OCR 模型。

## ✨ 特色

- **高效能**：利用 MLX 框架和 Metal GPU 加速
- **多功能**：支援文件、表格、公式識別，以及 Markdown 格式輸出
- **新功能**：支援照片前處理（去背、增強）和影片截圖
- **隱私安全**：完全本地運行，無需上傳數據

## 📚 文件導覽

詳細說明請參考 `docs/` 目錄下的文件：

- **🚀 快速開始**：
  - [快速啟動指南](docs/快速启动.md) - 最簡單的啟動方式
  - [詳細啟動指南](docs/START_GUIDE.md) - 包含故障排除

- **📖 使用指南**：
  - [完整運行指南](docs/MLX%20DeepSeek-OCR%20本地运行指南) - 功能詳解與進階用法

- **🛠️ 部署與維護**：
  - [部署指南](docs/DEPLOYMENT_GUIDE.md) - Docker 與服務器部署方案
  - [GPU 驗證指南](docs/GPU_VERIFICATION_GUIDE.md)

## 🛠️ 安裝與啟動

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 啟動應用

```bash
# 使用啟動腳本 (推薦)
./start.sh

# 或手動啟動
python app.py
```

訪問 **http://localhost:5000** (或 5001) 開始使用。

## ⚠️ 系統要求

- **OS**: macOS 13.0+
- **Hardware**: Apple Silicon (M1/M2/M3/M4)
- **Python**: 3.11+
- **RAM**: 16GB+ (推薦)

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
See the `LICENSE` file in the project root for details, or visit:

https://www.gnu.org/licenses/agpl-3.0.en.html

SPDX-License-Identifier: AGPL-3.0-or-later

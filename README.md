# MLX DeepSeek-OCR

<div align="center">

**🚀 專為 Apple Silicon 優化的全功能 OCR 解決方案**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MLX](https://img.shields.io/badge/MLX-0.20.0+-orange.svg)](https://github.com/ml-explore/mlx)
[![DeepSeek-OCR](https://img.shields.io/badge/Model-DeepSeek--OCR-purple.svg)](https://huggingface.co/mlx-community/DeepSeek-OCR-8bit)

*完全本地運行 • 隱私保護 • Metal GPU 加速 • 零配置部署*

[快速開始](#-快速開始) • [功能特色](#-功能特色) • [架構設計](#-系統架構) • [文檔](#-文檔)

</div>

---

## ✨ 功能特色

### 🎯 **核心 OCR 能力**

#### **多場景智能識別**
- **📄 文檔處理**：學術論文、商業文件、一般內容、表格、手寫文字、複雜版面
- **🌆 場景識別**：街景文字、照片文字、物品標籤、驗證碼
- **🎚️ 5 級精度控制**：Tiny → Small → Medium → Large → Gundam
  - 動態調整圖像尺寸（512px - 1280px）
  - 智能 Token 分配（256 - 8192 tokens）

#### **專業格式輸出**
- ✅ **Markdown** 格式轉換（保留結構）
- ✅ **LaTeX** 數學公式提取
- ✅ **表格** Markdown 格式化
- ✅ **繁體中文** 優先處理

### 📑 **PDF 批次處理**

#### **雙模式處理**
- **批次模式**：自動處理整份 PDF（1/3/5/10/自訂頁數）
- **單頁模式**：精確選擇特定頁面處理

#### **智能特性**
- 🖼️ **即時縮圖預覽**（可縮放、可選擇）
- ⏸️ **批次控制**：暫停/繼續/停止
- 📊 **進度追蹤**：實時顯示處理狀態
- 💾 **結果管理**：分頁下載、批次導出

### 🎨 **照片前處理**

#### **4 種預設模式**
1. **掃描優化**：自動旋轉 + 增強 + 去陰影 + 二值化
2. **照片優化**：自動旋轉 + 增強 + 去陰影
3. **模糊增強**：對比度增強 + 銳化
4. **去背景**：智能背景移除

#### **批次處理能力**
- 📤 **多圖上傳**：拖放或選擇多張圖片
- 🔄 **批次前處理**：一鍵處理所有圖片
- 📥 **批次下載**：ZIP 打包下載
- 🔗 **無縫銜接**：直接傳送至 OCR 處理

### 🎬 **影片截圖提取**

#### **智能截圖**
- 🎞️ **支援格式**：MP4, AVI, MOV, MKV, WebM
- ⚡ **快速提取**：自動均勻採樣關鍵幀
- 🖼️ **預覽管理**：網格顯示、批次下載
- 🔄 **OCR 整合**：截圖可直接進行 OCR

---

## 🏗️ 系統架構

### **技術棧**

```
┌─────────────────────────────────────────────────────────┐
│                    前端層 (UI)                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tailwind CSS + Vanilla JS (3033 行)             │  │
│  │  • 響應式設計 • 拖放上傳 • 實時預覽              │  │
│  │  • 進度追蹤 • 批次控制 • 結果管理                │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                 後端層 (Flask API)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Flask 3.0 + Python 3.11+ (1770 行)              │  │
│  │  • 18 個 REST API 端點                           │  │
│  │  • 多進程 OCR 處理                               │  │
│  │  • 任務狀態管理                                  │  │
│  │  • 文件流式處理                                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               AI 推理層 (MLX Framework)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  MLX 0.20+ • mlx-vlm 0.3.5                       │  │
│  │  • Metal GPU 加速                                │  │
│  │  • DeepSeek-OCR-8bit 模型                        │  │
│  │  • 自動模型下載與緩存                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              圖像處理層 (OpenCV + PIL)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  OpenCV 4.10+ • Pillow 10.3+ • PyMuPDF           │  │
│  │  • PDF 渲染 • 影片解碼 • 圖像增強                │  │
│  │  • 自動旋轉 • 去陰影 • 背景移除                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### **API 架構**

#### **核心端點**
```
GET  /                          # 主頁面
GET  /api/status               # 系統狀態
GET  /api/health               # 健康檢查

POST /api/ocr                  # 單圖 OCR
POST /api/pdf/init             # PDF 初始化
POST /api/pdf/extract-pages    # PDF 頁面提取
POST /api/pdf/process-batch    # PDF 批次處理
POST /api/pdf/preview-page     # PDF 頁面預覽
POST /api/pdf/cancel           # 取消處理

POST /api/preprocess/upload    # 照片上傳
POST /api/preprocess/process   # 照片前處理
POST /api/preprocess/download  # 下載處理結果
POST /api/preprocess/to-ocr    # 傳送至 OCR

POST /api/video/upload         # 影片上傳
POST /api/video/extract        # 截圖提取
POST /api/video/download       # 下載截圖
POST /api/video/process-batch  # 批次 OCR

GET  /api/files/<path>         # 文件服務
```

### **數據流**

```
用戶上傳
    ↓
┌──────────────┐
│ 文件驗證     │ → 格式檢查 (PNG/JPG/PDF/MP4...)
│ 大小限制     │ → 最大 512MB
└──────────────┘
    ↓
┌──────────────┐
│ 前處理       │ → 圖像增強、去陰影、旋轉
│ (可選)       │ → 影片截圖提取
└──────────────┘
    ↓
┌──────────────┐
│ 任務創建     │ → UUID 生成
│ 狀態初始化   │ → pending → processing → completed
└──────────────┘
    ↓
┌──────────────┐
│ MLX 推理     │ → 多進程處理
│ GPU 加速     │ → Metal 優化
└──────────────┘
    ↓
┌──────────────┐
│ 結果處理     │ → Markdown 格式化
│ 文件清理     │ → 自動清理臨時文件
└──────────────┘
    ↓
返回結果 (JSON)
```

---

## 🎨 UI 設計特色

### **現代化界面**

#### **🎯 三大功能分頁**
```
┌─────────────────────────────────────────────────┐
│  📄 OCR 識別  │  🎨 照片前處理  │  🎬 影片截圖  │
└─────────────────────────────────────────────────┘
```

#### **🎨 設計亮點**

1. **漸層紫色主題**
   - 主色：`#8b5cf6` → `#a78bfa`
   - 陰影效果：`rgba(139, 92, 246, 0.4)`
   - 一致的視覺語言

2. **拖放上傳區**
   - 虛線邊框設計
   - Hover 動畫效果
   - 拖入時高亮顯示

3. **智能配置面板**
   - 動態顯示/隱藏
   - 滑桿式精度控制
   - 實時配置預覽

4. **進度追蹤**
   - 旋轉載入動畫
   - 百分比進度條
   - 狀態文字提示

5. **結果展示**
   - Markdown 渲染
   - 一鍵複製
   - 批次下載

### **響應式設計**

```css
/* 桌面 (1024px+) */
- 三欄佈局
- 側邊縮圖預覽
- 完整功能面板

/* 平板 (768px - 1024px) */
- 兩欄佈局
- 摺疊式縮圖
- 簡化控制面板

/* 手機 (< 768px) */
- 單欄佈局
- 全屏預覽
- 底部操作欄
```

### **互動體驗**

- ✨ **平滑過渡**：所有狀態變化 0.3s 動畫
- 🎯 **視覺反饋**：Hover、Active、Selected 狀態
- ⚡ **即時響應**：無刷新頁面更新
- 🔔 **友好提示**：錯誤、成功、警告訊息

---

## 🚀 快速開始

### **系統要求**

| 項目 | 需求 |
|------|------|
| **作業系統** | macOS 13.0+ |
| **硬體** | Apple Silicon (M1/M2/M3/M4) |
| **Python** | 3.11+ |
| **記憶體** | 16GB+ (推薦) |
| **磁碟空間** | 5GB+ (含模型) |

### **一鍵安裝**

```bash
# 1. 克隆專案
git clone https://github.com/matica0902/Video-PDF-IMG-DeepOCR-Omni.git
cd Video-PDF-IMG-DeepOCR-Omni

# 2. 執行啟動腳本（自動安裝依賴）
./start.sh
```

**start.sh 會自動：**
- ✅ 檢查 Python 版本
- ✅ 創建虛擬環境
- ✅ 安裝所有依賴
- ✅ 尋找可用端口（5000-5010）
- ✅ 清理殭屍進程
- ✅ 啟動應用

### **首次使用**

1. **訪問應用**：http://localhost:5000
2. **首次 OCR**：自動下載模型（~800MB，需 5-15 分鐘）
3. **模型位置**：`~/hf_cache/hub/models--mlx-community--DeepSeek-OCR-8bit/`
4. **後續使用**：模型已緩存，啟動即用

### **手動安裝**

```bash
# 1. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 啟動應用
python3 app.py
```

---

## 📚 文檔

詳細說明請參考 `docs/` 目錄：

### **快速指南**
- [快速啟動](docs/快速启动.md) - 最簡單的啟動方式
- [詳細啟動指南](docs/START_GUIDE.md) - 包含故障排除

### **完整文檔**
- [完整運行指南](docs/MLX%20DeepSeek-OCR%20本地运行指南) - 功能詳解與進階用法

---

## 🔒 隱私與安全

### **完全本地運行**
- ✅ 所有處理在本地完成
- ✅ 無需上傳數據到雲端
- ✅ 無網絡連接要求（模型下載後）
- ✅ 臨時文件自動清理

### **數據處理**
- 上傳文件：存儲在系統臨時目錄
- 處理結果：僅保存在瀏覽器會話
- 自動清理：處理完成後刪除臨時文件

---

## ⚡ 性能優化

### **Metal GPU 加速**
```python
# 自動檢測並使用 Metal GPU
if mx.metal.is_available():
    # 使用 GPU 加速（默認）
    print("🔧 Metal GPU 已啟用")
else:
    # 降級到 CPU
    mx.set_default_device(mx.cpu)
```

### **多進程處理**
- PDF 批次：並行處理多頁
- 照片前處理：批次處理多圖
- 影片截圖：異步提取幀

### **記憶體管理**
- 延遲載入：首次請求時才載入模型
- 手動釋放：`POST /api/unload-model`
- 自動清理：處理完成後釋放資源

---

## 🛠️ 開發資訊

### **專案結構**

```
FLASKAPP/
├── app.py                 # Flask 後端 (1770 行)
├── start.sh              # 啟動腳本
├── requirements.txt      # Python 依賴
├── static/
│   └── app.js           # 前端邏輯 (3033 行)
├── templates/
│   └── index.html       # 主頁面 (849 行)
├── docs/                # 文檔目錄
├── uploads/             # 臨時上傳目錄
└── venv/                # 虛擬環境
```

### **核心依賴**

```python
Flask==3.0.0              # Web 框架
mlx-vlm==0.3.5           # MLX 視覺語言模型
mlx>=0.20.0              # Apple MLX 框架
Pillow>=10.3.0           # 圖像處理
opencv-python>=4.10.0    # 電腦視覺
PyMuPDF                  # PDF 處理
Werkzeug==3.0.1          # WSGI 工具
```

### **代碼統計**

| 文件 | 行數 | 說明 |
|------|------|------|
| `app.py` | 1,770 | 後端邏輯、API、OCR 處理 |
| `static/app.js` | 3,033 | 前端邏輯、UI 互動 |
| `templates/index.html` | 849 | HTML 結構、樣式 |
| **總計** | **5,652** | 完整功能實現 |

---

## 📖 使用範例

### **1. 基礎 OCR**
```bash
# 上傳圖片 → 選擇模式 → 點擊「開始識別」
# 結果自動顯示，可複製或下載
```

### **2. PDF 批次處理**
```bash
# 上傳 PDF → 選擇批次模式 → 設定每批頁數
# 自動處理 → 查看進度 → 下載結果
```

### **3. 照片前處理**
```bash
# 切換到「照片前處理」分頁
# 上傳照片 → 選擇預設模式 → 處理
# 下載結果 或 直接傳送至 OCR
```

### **4. 影片截圖**
```bash
# 切換到「影片截圖」分頁
# 上傳影片 → 設定截圖數量 → 提取
# 預覽截圖 → 下載 或 批次 OCR
```

---

## 🤝 貢獻

歡迎貢獻！請遵循以下步驟：

1. Fork 本專案
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 📄 授權

本專案採用 **GNU Affero General Public License v3.0 (AGPL-3.0)** 授權。

- 📖 [完整授權條款](LICENSE)
- 🔗 [AGPL-3.0 官方說明](https://www.gnu.org/licenses/agpl-3.0.en.html)

**SPDX-License-Identifier**: AGPL-3.0-or-later

### **簡要說明**

✅ **您可以：**
- 自由使用、修改、分發本軟體
- 用於商業用途

⚠️ **您必須：**
- 保留原始授權聲明和版權信息
- 開源您的修改版本（使用相同授權）
- 如果通過網絡提供服務，必須提供源代碼

---

## 🙏 致謝

- **[MLX](https://github.com/ml-explore/mlx)** - Apple 的機器學習框架
- **[DeepSeek-OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR)** - 強大的 OCR 模型
- **[mlx-vlm](https://github.com/Blaizzy/mlx-vlm)** - MLX 視覺語言模型實現
- **[Flask](https://flask.palletsprojects.com/)** - 輕量級 Web 框架

---

## 📞 聯繫方式

- **GitHub**: [matica0902/MLX-Video-OCR-DeepSeek-Apple-Silicon](https://github.com/matica0902/MLX-Video-OCR-DeepSeek-Apple-Silicon)
- **Issues**: [提交問題](https://github.com/matica0902/MLX-Video-OCR-DeepSeek-Apple-Silicon/issues)

---

<div align="center">

**⭐ 如果這個專案對您有幫助，請給個星星！**

Made with ❤️ for Apple Silicon

</div>

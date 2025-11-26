# 部署架构指南：APP 与 API 部署方案

## 📋 部署方案对比

### 方案 1：Docker Compose 统一部署（推荐用于开发/测试）
- APP 和 API 在同一 Docker Compose 中
- 统一管理、一键启动
- 适合本地开发、测试环境

### 方案 2：完全分离部署（推荐用于生产）
- APP 和 API 独立部署
- 通过 HTTP/HTTPS 通信
- 适合生产环境、高可用场景

### 方案 3：混合部署
- API 用 Docker，APP 直接部署
- 灵活组合

---

## ⚠️ 重要限制：MLX 框架与 Docker

### MLX 框架限制
- **MLX 框架专为 macOS Apple Silicon 设计**
- **需要 Metal 后端支持**（macOS 专用）
- **Docker 在 macOS 上无法直接使用 Metal GPU**

### 部署建议

| 环境 | 推荐方案 | 说明 |
|------|---------|------|
| **macOS 本地开发** | 直接运行（不使用 Docker） | MLX 需要 Metal，Docker 不支持 |
| **macOS 服务器** | 直接运行（不使用 Docker） | 最佳性能，直接使用 Metal |
| **Linux 服务器** | ❌ 不支持 | MLX 不支持 Linux |
| **云服务（AWS/GCP）** | ❌ 不支持 | MLX 仅支持 macOS |

---

## 🐳 方案 1：Docker Compose 部署（开发/测试）

### 适用场景
- 本地开发环境
- 团队协作
- 快速部署测试

### 架构图

```
┌─────────────────────────────────────┐
│     Docker Compose Network          │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Node.js APP │  │ Flask API   │ │
│  │  (Port 3000) │  │ (Port 5000) │ │
│  └──────┬───────┘  └──────┬───────┘ │
│         │                 │         │
│         └────────┬────────┘         │
│                  │                  │
│         └────────┴────────┘         │
│         Internal Network            │
└─────────────────────────────────────┘
```

### 文件结构

```
project/
├── docker-compose.yml
├── flask-api/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── ...
└── node-app/
    ├── Dockerfile
    ├── package.json
    └── ...
```

---

## 🚀 方案 2：完全分离部署（生产推荐）

### 适用场景
- 生产环境
- 高可用需求
- 独立扩展需求

### 架构图

```
┌─────────────────┐         ┌─────────────────┐
│   Node.js APP   │  HTTP  │   Flask API      │
│   (Port 3000)   │ ──────>│   (Port 5000)    │
│                 │        │                 │
│  Load Balancer  │        │  Load Balancer   │
└─────────────────┘        └─────────────────┘
      │                           │
      └───────────┬───────────────┘
                  │
            Internet/Network
```

### 优势
- ✅ 独立扩展（APP 和 API 可分别扩展）
- ✅ 故障隔离（一个服务故障不影响另一个）
- ✅ 独立部署（可分别更新）
- ✅ 负载均衡（可分别配置）

---

## 📝 实施步骤

### 方案 1：Docker Compose（开发环境）

#### 1. 创建 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  flask-api:
    build: ./flask-api
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - PORT=5000
    volumes:
      - ./flask-api:/app
      - model_cache:/root/.cache/huggingface
    networks:
      - ocr-network
    # ⚠️ 注意：macOS 上无法使用 GPU，MLX 性能会受限
    # 建议在 macOS 上直接运行，不使用 Docker

  node-app:
    build: ./node-app
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://flask-api:5000
      - NODE_ENV=production
    depends_on:
      - flask-api
    networks:
      - ocr-network

volumes:
  model_cache:

networks:
  ocr-network:
    driver: bridge
```

#### 2. Flask API Dockerfile

```dockerfile
# flask-api/Dockerfile
FROM python:3.11-slim

# ⚠️ 注意：MLX 需要 macOS，此 Dockerfile 仅用于参考
# 在 macOS 上建议直接运行，不使用 Docker

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
```

#### 3. Node.js APP Dockerfile

```dockerfile
# node-app/Dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制依赖文件
COPY package*.json ./
RUN npm install --production

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["node", "server.js"]
```

#### 4. 启动命令

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

### 方案 2：完全分离部署（生产环境）

#### Flask API 部署（macOS 服务器）

```bash
# 1. 在 macOS 服务器上直接运行
cd /path/to/flask-api
source venv/bin/activate
python app.py

# 2. 或使用 systemd 服务
# /etc/systemd/system/flask-ocr-api.service
[Unit]
Description=Flask OCR API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/flask-api
Environment="PATH=/path/to/flask-api/venv/bin"
ExecStart=/path/to/flask-api/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target

# 启动服务
sudo systemctl enable flask-ocr-api
sudo systemctl start flask-ocr-api
```

#### Node.js APP 部署

```bash
# 1. 安装依赖
npm install

# 2. 配置环境变量
export API_URL=http://flask-api-server:5000

# 3. 启动应用
npm start

# 4. 或使用 PM2
pm2 start server.js --name node-app
```

#### 环境变量配置

```bash
# Node.js APP .env
API_URL=http://flask-api-server:5000
NODE_ENV=production
PORT=3000
```

---

## 🔧 方案 3：混合部署（灵活方案）

### 场景
- API 在 macOS 服务器直接运行（利用 Metal）
- APP 用 Docker 部署（Linux 服务器）

### 配置示例

```javascript
// Node.js APP 配置
const API_URL = process.env.API_URL || 'http://macos-server:5000';

// 调用 Flask API
const response = await axios.post(`${API_URL}/api/ocr`, formData);
```

---

## 📊 方案对比总结

| 特性 | Docker Compose | 完全分离 | 混合部署 |
|------|---------------|---------|---------|
| **部署复杂度** | ⭐⭐ 中等 | ⭐⭐⭐ 简单 | ⭐⭐ 中等 |
| **开发便利性** | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐ 良好 | ⭐⭐⭐ 良好 |
| **生产适用性** | ⭐⭐ 一般 | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐ 良好 |
| **扩展性** | ⭐⭐ 受限 | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐ 良好 |
| **MLX 性能** | ⚠️ 受限 | ✅ 最佳 | ✅ 最佳 |
| **资源占用** | ⚠️ 较高 | ✅ 较低 | ✅ 较低 |

---

## 🎯 推荐方案

### 开发环境
**推荐：直接运行（不使用 Docker）**
- macOS 本地：直接运行 Flask API 和 Node.js APP
- MLX 需要 Metal，Docker 无法使用 GPU

### 生产环境
**推荐：完全分离部署**
- Flask API：macOS 服务器直接运行（利用 Metal）
- Node.js APP：独立部署（Linux/Windows 都可以）
- 通过 HTTP/HTTPS 通信

### 部署步骤

1. **Flask API（macOS 服务器）**
   ```bash
   cd /path/to/flask-api
   ./start.sh  # 或使用 systemd
   ```

2. **Node.js APP（任意服务器）**
   ```bash
   cd /path/to/node-app
   npm install
   export API_URL=http://flask-api-server:5000
   npm start
   ```

3. **配置反向代理（可选）**
   ```nginx
   # Nginx 配置
   upstream flask-api {
       server flask-api-server:5000;
   }

   upstream node-app {
       server node-app-server:3000;
   }

   server {
       listen 80;
       server_name your-domain.com;

       location /api/ {
           proxy_pass http://flask-api;
       }

       location / {
           proxy_pass http://node-app;
       }
   }
   ```

---

## ⚠️ 重要提醒

1. **MLX 框架限制**
   - MLX 仅支持 macOS Apple Silicon
   - Docker 在 macOS 上无法使用 Metal GPU
   - **建议在 macOS 上直接运行 Flask API**

2. **性能考虑**
   - 直接运行：最佳性能（Metal GPU 加速）
   - Docker：性能受限（无法使用 GPU）

3. **部署建议**
   - 开发：macOS 本地直接运行
   - 生产：macOS 服务器直接运行 Flask API，Node.js APP 可部署到任意平台

---

## 📝 总结

| 环境 | Flask API 部署 | Node.js APP 部署 | 通信方式 |
|------|---------------|-----------------|---------|
| **开发** | macOS 直接运行 | macOS 直接运行 | localhost |
| **测试** | macOS 直接运行 | Docker（可选） | HTTP |
| **生产** | macOS 直接运行 | 任意平台 | HTTP/HTTPS |

**核心原则：Flask API 必须在 macOS 上直接运行以利用 MLX Metal 加速！**


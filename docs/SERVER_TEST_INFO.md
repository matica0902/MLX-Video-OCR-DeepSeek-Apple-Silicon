# 服务器测试信息总结

## 🔍 服务器环境信息

### 部署平台
- **平台**: Hugging Face Spaces
- **端口**: 7860 (Hugging Face Spaces 标准端口)
- **路径**: `/app/app.py` (Docker 容器路径)
- **环境**: Linux CPU (从日志 "You are running on Linux CPU" 可以看出)

### 访问信息
- **HF_TOKEN**: 已提供（用户说"我把 hugging face 的 token 都给你了"）
- **huggingface-cli**: 已安装 (`/Users/jianjunneng/1111TEST/FLASKAPP/venv/bin/huggingface-cli`)
- **当前状态**: CLI 未登录 (`Not logged in`)

## 🐛 错误信息

### 错误详情
```
AttributeError: 'NoneType' object has no attribute 'token'
File: /usr/local/lib/python3.10/site-packages/mlx_vlm/generate.py, line 572
```

### 错误原因
- `mlx-vlm` 0.3.5 的 bug
- `stream_generate()` 没有产生响应时，`last_response` 保持为 `None`
- 代码直接访问 `last_response.token` 导致错误

### 错误位置
- 服务器代码: `/app/app.py` 第 568 行（旧版本）
- 库代码: `mlx_vlm/generate.py` 第 572 行

## 📝 测试脚本

### 已创建的测试脚本
1. `test_server_final.py` - 最简测试
2. `test_server_minimal.py` - 最小化测试
3. `test_server_debug.py` - 调试测试（测试不同参数）
4. `test_find_minimal.py` - 找出最小可工作配置
5. `test_model_professional.py` - 专业测试套件
6. `test_fix_verification.py` - 验证修复

### 测试脚本位置
- 本地: `/Users/jianjunneng/1117test/FLASKAPP/test_*.py`
- 服务器: `/app/test_*.py` (需要部署)

## 🔧 修复方案

### 已实施的修复
1. **添加重试机制**: 3次重试，逐步减小 max_tokens (2048 → 512 → 256)
2. **捕获错误**: 捕获 `AttributeError: 'NoneType' object has no attribute 'token'`
3. **降级版本**: `requirements.txt` 设置为 `mlx-vlm==0.3.4`

### 代码修改位置
- 文件: `app.py`
- 函数: `_run_ocr_in_process()`
- 行数: 469-520 (当前版本)

## 🚀 如何测试服务器

### 方法 1: 通过 Hugging Face Spaces Web 界面
1. 登录 Hugging Face Spaces
2. 进入您的 Space
3. 查看日志 (Logs 标签)
4. 使用 Web 终端 (如果有)

### 方法 2: 通过 Hugging Face CLI
```bash
# 登录
huggingface-cli login
# 或
hf auth login

# 查看 Spaces
hf spaces list

# 查看 Space 日志
hf spaces logs <space-name>
```

### 方法 3: 通过 Docker (如果本地有镜像)
```bash
# 运行容器
docker run -it -e HF_TOKEN=your_token <image-name> /bin/bash

# 在容器内运行测试
python /app/test_server_final.py
```

### 方法 4: 通过 API 测试
```bash
# 测试 OCR API
curl -X POST https://your-space.hf.space/api/ocr \
  -F "file=@test_image.jpg" \
  -F "content_type=Document" \
  -F "subcategory=Academic" \
  -F "complexity=Medium"
```

## 📊 测试结果记录

### 本地测试结果
- ✅ 模型可以加载
- ⚠️ 本地 Mac 环境与服务器 Linux CPU 环境不同
- ❌ 无法完全复现服务器错误

### 服务器测试结果
- ❌ 错误持续存在: `'NoneType' object has no attribute 'token'`
- ⚠️ 服务器代码可能是旧版本（有 `Calling generate` 日志，当前代码没有）

## 🎯 下一步行动

1. **确认服务器代码版本**
   - 检查服务器上实际运行的代码
   - 确认是否是最新版本

2. **运行测试脚本**
   - 在服务器上运行 `test_server_final.py`
   - 查看实际错误和参数组合

3. **验证修复**
   - 重新部署修复后的代码
   - 测试是否解决问题

4. **如果仍有问题**
   - 尝试降级到 `mlx-vlm==0.3.3`
   - 或查找 mlx-vlm GitHub Issues
   - 或考虑使用其他 OCR 方案

## 📌 关键发现

1. **问题根源**: `mlx-vlm` 库的 bug，不是我们的代码问题
2. **环境差异**: 本地 Mac ≠ 服务器 Linux CPU
3. **版本问题**: `mlx-vlm==0.3.5` 可能有 bug，建议使用 0.3.4
4. **测试困难**: 无法直接在服务器环境测试，只能通过部署验证




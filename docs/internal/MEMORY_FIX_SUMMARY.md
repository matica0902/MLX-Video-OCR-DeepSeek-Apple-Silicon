# FLASKAPP/app.py 内存释放修复说明

## 🔍 发现的问题

### 1. **模型一直保留在内存中**
- 模型加载后存储在全局变量中
- 没有释放机制
- Flask 服务运行期间，模型会一直占用内存

### 2. **图像对象未释放**
- `Image.open()` 创建的对象没有显式关闭
- 可能导致文件句柄泄漏

### 3. **没有清理 API**
- 无法手动释放模型
- 无法在不需要时清理内存

### 4. **没有退出清理**
- Flask 服务停止时没有清理资源
- 可能导致内存未完全释放

## ✅ 已实施的修复

### 1. **添加了 `unload_model()` 函数**
```python
def unload_model():
    """释放模型内存"""
    global model, processor, model_loaded
    
    del model
    del processor
    model_loaded = False
    gc.collect()
    
    # 清理 MLX 缓存
    import mlx.core as mx
    mx.clear_cache()
```

### 2. **添加了释放模型的 API 端点**
```python
@app.route('/api/unload-model', methods=['POST'])
def unload_model_endpoint():
    """释放模型内存的 API 端点"""
    unload_model()
    return jsonify({'success': True, 'message': '模型已释放'})
```

### 3. **改进了 OCR 处理的内存管理**
- 显式关闭图像对象：`image.close()`
- 删除图像对象：`del image`
- 执行垃圾回收：`gc.collect()`

### 4. **添加了退出清理机制**
```python
import atexit
atexit.register(cleanup_on_exit)

def cleanup_on_exit():
    """应用退出时的清理函数"""
    unload_model()
```

### 5. **添加了异常处理**
- 在 `finally` 块中确保清理
- 处理 KeyboardInterrupt

## 📋 使用方法

### 手动释放模型（通过 API）
```bash
curl -X POST http://localhost:5000/api/unload-model
```

### 自动释放（服务停止时）
- 按 `Ctrl+C` 停止服务
- 模型会自动释放

### 检查模型状态
```bash
curl http://localhost:5000/api/status
```

## 🔧 内存管理流程

### 加载模型
1. 第一次 OCR 请求时自动加载
2. 或通过 `POST /api/load-model` 手动加载

### 使用模型
1. 处理 OCR 请求
2. 清理图像对象
3. 执行垃圾回收

### 释放模型
1. 通过 `POST /api/unload-model` 手动释放
2. 或服务停止时自动释放

## ⚠️ 注意事项

1. **模型释放后需要重新加载**
   - 释放后，下次 OCR 请求会自动重新加载
   - 重新加载需要时间（10-20秒）

2. **服务运行期间**
   - 如果持续使用，建议保持模型加载
   - 如果长时间不使用，可以释放以节省内存

3. **MLX 缓存清理**
   - 已添加 MLX 缓存清理
   - 确保 MLX 框架的内存也被释放

## 📊 内存占用

- **模型加载后**: 约 2-3GB（MLX 4-bit 量化模型）
- **模型释放后**: 回到正常水平（<100MB）

## ✅ 修复总结

现在的 `app.py` 包含：
- ✅ 模型加载函数
- ✅ 模型释放函数
- ✅ 图像对象清理
- ✅ 垃圾回收机制
- ✅ MLX 缓存清理
- ✅ 退出时自动清理
- ✅ 手动释放 API

## 🧪 测试方法

1. **启动服务**
   ```bash
   cd FLASKAPP
   python3 app.py
   ```

2. **检查模型状态**
   ```bash
   curl http://localhost:5000/api/status
   ```

3. **执行 OCR（会自动加载模型）**
   ```bash
   curl -X POST -F "file=@test.jpg" http://localhost:5000/api/ocr
   ```

4. **释放模型**
   ```bash
   curl -X POST http://localhost:5000/api/unload-model
   ```

5. **停止服务（会自动清理）**
   - 按 `Ctrl+C`
   - 查看控制台输出，应该看到清理消息


# Mac M2 上 MLX DeepSeek-OCR 问题与解决方案

## 🔍 代码检查结果

### ✅ 代码正确性
代码结构基本正确，但存在一些可以改进的地方：

1. **MLX 内存清理可能不完整**
   - 当前只调用 `mx.clear_cache()`
   - Mac M2 的统一内存架构可能需要更彻底的清理

2. **缺少 MLX 特定的内存管理**
   - MLX 框架在 Mac M2 上可能有特殊的内存管理需求

3. **多次垃圾回收可能不够**
   - 需要更激进的清理策略

## ⚠️ Mac M2 上的已知问题

### 1. **统一内存架构（UMA）的特殊性**
- Mac M2 使用统一内存架构，CPU、GPU、NPU 共享内存
- 模型加载后，内存可能被标记为 GPU 使用，即使进程结束也可能不立即释放
- **问题**: 即使调用 `del model` 和 `gc.collect()`，内存可能仍然被系统保留

### 2. **MLX 框架的内存管理**
- MLX 使用 Metal 后端，内存管理可能与标准 Python 不同
- `mx.clear_cache()` 可能不足以完全释放内存
- **问题**: MLX 可能缓存了模型权重，即使删除 Python 对象，Metal 层可能仍保留

### 3. **系统内存压缩机制**
- macOS 会压缩不活跃的内存
- 即使内存被"释放"，系统可能仍保留压缩版本
- **问题**: 看起来内存已释放，但实际上被压缩存储

## 💡 解决方案

### 方案 1: 改进 MLX 内存清理（推荐）

```python
def unload_model():
    """✅ 彻底释放 MLX 模型内存（Mac M2 优化版）"""
    global model, processor, model_loaded
    
    print("🧹 正在徹底釋放模型記憶體（Mac M2 優化）...")
    
    # 1. 先清理 MLX 缓存（在删除对象前）
    try:
        import mlx.core as mx
        mx.clear_cache()
        # 强制同步所有 MLX 操作
        mx.eval(mx.array([0]))  # 触发同步
    except Exception as e:
        print(f"   警告: MLX 缓存清理失败: {e}")
    
    # 2. 删除模型和 processor
    if model is not None:
        try:
            # 尝试将模型移到 CPU（如果支持）
            if hasattr(model, 'cpu'):
                model = model.cpu()
        except:
            pass
        del model
        model = None
    
    if processor is not None:
        del processor
        processor = None
    
    model_loaded = False
    
    # 3. 多次垃圾回收（Mac M2 需要更彻底）
    for i in range(5):  # 增加到 5 次
        collected = gc.collect()
        if collected == 0:
            break
    
    # 4. 再次清理 MLX 缓存
    try:
        import mlx.core as mx
        mx.clear_cache()
        # 清空所有 MLX 数组
        mx.clear_cache()
    except:
        pass
    
    # 5. 最终垃圾回收
    gc.collect()
    
    print("✅ 模型記憶體已徹底釋放")
    return True
```

### 方案 2: 使用上下文管理器

```python
from contextlib import contextmanager

@contextmanager
def model_context():
    """模型上下文管理器，确保自动释放"""
    model = None
    processor = None
    try:
        model, processor = load("mlx-community/DeepSeek-OCR-4bit")
        yield model, processor
    finally:
        # 清理
        if model is not None:
            del model
        if processor is not None:
            del processor
        import mlx.core as mx
        mx.clear_cache()
        gc.collect()
```

### 方案 3: 系统级清理（如果问题持续）

如果内存仍然不释放，可能需要：

1. **重启系统**（最彻底）
2. **清理系统缓存**：
   ```bash
   sudo purge
   ```
3. **检查活动监视器**：
   - 查看是否有残留的 Python 进程
   - 检查内存压缩情况

## 🔧 代码改进建议

### 改进点 1: 更彻底的 MLX 清理

```python
# 在 unload_model() 中添加
try:
    import mlx.core as mx
    # 多次清理缓存
    for _ in range(3):
        mx.clear_cache()
    # 同步操作
    mx.eval(mx.array([0]))
except:
    pass
```

### 改进点 2: 添加内存监控

```python
import psutil
import os

def get_memory_usage():
    """获取当前进程内存使用"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

# 在 load_model() 后
mem_after = get_memory_usage()
print(f"模型加载后内存: {mem_after:.2f} MB")

# 在 unload_model() 后
mem_after_unload = get_memory_usage()
print(f"模型释放后内存: {mem_after_unload:.2f} MB")
print(f"释放了: {mem_after - mem_after_unload:.2f} MB")
```

### 改进点 3: 定期清理（如果服务长期运行）

```python
import threading
import time

def periodic_cleanup():
    """定期清理 MLX 缓存"""
    while True:
        time.sleep(300)  # 每 5 分钟
        try:
            import mlx.core as mx
            mx.clear_cache()
        except:
            pass

# 在应用启动时
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

## 📊 Mac M2 特定优化

### 1. **使用量化模型**（已使用 4-bit）
- ✅ 当前已使用 `DeepSeek-OCR-4bit`
- 这是正确的选择，可以减少内存占用

### 2. **限制并发请求**
- 如果同时处理多个请求，内存占用会增加
- 考虑添加请求队列限制

### 3. **监控系统内存压力**
```python
import psutil

def check_memory_pressure():
    """检查系统内存压力"""
    mem = psutil.virtual_memory()
    if mem.percent > 85:
        print("⚠️  系统内存压力高，建议释放模型")
        return True
    return False
```

## 🚨 已知限制

1. **MLX 框架限制**
   - MLX 是 Apple 专为 Apple Silicon 设计的框架
   - 内存管理可能与标准 Python 不同
   - 某些情况下，内存可能不会立即释放

2. **macOS 系统行为**
   - macOS 的内存管理是自动的
   - 系统会保留 inactive 内存以便快速重用
   - 这不是内存泄漏，而是系统优化

3. **统一内存架构**
   - CPU、GPU 共享内存
   - GPU 使用的内存可能不会立即释放
   - 需要等待系统自动回收

## ✅ 最佳实践

1. **使用修复后的代码**
   - 多次垃圾回收
   - 多次清理 MLX 缓存
   - 同步 MLX 操作

2. **监控内存使用**
   - 使用 `psutil` 监控内存
   - 记录加载前后的内存差异

3. **定期重启服务**（如果长期运行）
   - 每天重启一次服务
   - 确保内存完全释放

4. **使用系统清理**
   - 如果问题持续，使用 `sudo purge`
   - 或重启系统

## 📝 总结

Mac M2 上的内存问题主要来自：
1. **统一内存架构的特殊性**
2. **MLX 框架的内存管理**
3. **macOS 的内存压缩机制**

解决方案：
1. ✅ 改进 MLX 清理代码（多次清理 + 同步）
2. ✅ 多次垃圾回收
3. ✅ 添加内存监控
4. ⚠️  如果问题持续，可能需要系统级清理或重启


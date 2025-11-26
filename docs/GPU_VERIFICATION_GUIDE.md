# GPU/Metal 验证指南

## 🔍 如何验证 Mac 是否使用 GPU（Metal）而不是 CPU

### 方法 1：使用验证脚本（推荐）

```bash
cd /Users/jianjunneng/1111TEST/FLASKAPP
source venv/bin/activate
python check_gpu.py
```

这个脚本会：
1. ✅ 检查 Metal 是否可用
2. ✅ 测试 GPU vs CPU 性能
3. ✅ 显示加速比
4. ✅ 检查系统信息

### 方法 2：在代码中检查

当前代码已经包含检查：

```python
# app.py 第 64 行和第 205 行
print(f"📊 Metal available: {mx.metal.is_available()}")

if not mx.metal.is_available():
    print("WARNING: Metal is not available, MLX might not perform well.")
```

### 方法 3：运行时查看日志

启动应用时，查看日志输出：

```bash
./start.sh
```

查找以下输出：
- `📊 Metal available: True` ✅ 使用 GPU
- `📊 Metal available: False` ❌ 仅使用 CPU
- `WARNING: Metal is not available` ⚠️ 警告

### 方法 4：使用 Activity Monitor（活动监视器）

1. 打开 **活动监视器** (Activity Monitor)
2. 查看 **GPU** 标签页
3. 运行 OCR 任务
4. 观察 GPU 使用率：
   - **有 GPU 活动** = ✅ 使用 GPU
   - **无 GPU 活动** = ❌ 仅使用 CPU

### 方法 5：性能对比测试

#### GPU 使用时的表现：
- ✅ OCR 处理速度快（15-30秒/页）
- ✅ GPU 使用率上升（Activity Monitor）
- ✅ 温度上升（Mac 风扇可能启动）

#### 仅 CPU 使用时的表现：
- ❌ OCR 处理速度慢（60-120秒/页）
- ❌ GPU 使用率为 0
- ⚠️ CPU 使用率高

---

## 📊 验证结果解读

### ✅ 正常情况（使用 GPU）

```
Metal 可用: ✅ 是
默认设备: gpu
GPU 时间: 0.1234 秒
CPU 时间: 0.5678 秒
加速比: 4.60x
✅ GPU 加速明显，正在使用 Metal
```

### ⚠️ 警告情况（部分使用）

```
Metal 可用: ✅ 是
默认设备: gpu
GPU 时间: 0.3000 秒
CPU 时间: 0.3500 秒
加速比: 1.17x
⚠️ GPU 加速不明显，可能部分使用 CPU
```

### ❌ 异常情况（仅 CPU）

```
Metal 可用: ❌ 否
默认设备: cpu
⚠️ 警告: Metal 不可用，MLX 将使用 CPU
```

---

## 🔧 故障排除

### 问题 1：Metal 不可用

**可能原因：**
1. 不是 Apple Silicon Mac（M1/M2/M3/M4）
2. macOS 版本过低（需要 macOS 13.0+）
3. MLX 安装问题

**解决方案：**
```bash
# 检查 Mac 型号
system_profiler SPHardwareDataType | grep "Chip"

# 检查 macOS 版本
sw_vers

# 重新安装 MLX
pip uninstall mlx mlx-vlm
pip install mlx mlx-vlm
```

### 问题 2：Metal 可用但加速不明显

**可能原因：**
1. 任务太小，GPU 优势不明显
2. 内存不足
3. 系统资源竞争

**解决方案：**
- 使用更大的图片测试
- 关闭其他应用释放资源
- 检查内存使用情况

### 问题 3：如何强制使用 GPU

MLX 默认会自动使用 Metal（如果可用），无需手动配置。

如果需要强制使用 CPU（测试用）：
```python
# 强制使用 CPU（不推荐，仅用于测试）
mx.set_default_device(mx.cpu)
```

---

## 📈 性能基准

### 使用 GPU (Metal) 的预期性能

| 任务类型 | 处理时间 | GPU 使用率 |
|---------|---------|-----------|
| 简单文档 OCR | 15-30秒 | 60-80% |
| 复杂表格 | 30-45秒 | 70-90% |
| 数学公式 | 20-40秒 | 65-85% |

### 仅使用 CPU 的预期性能

| 任务类型 | 处理时间 | CPU 使用率 |
|---------|---------|-----------|
| 简单文档 OCR | 60-120秒 | 80-100% |
| 复杂表格 | 120-180秒 | 90-100% |
| 数学公式 | 90-150秒 | 85-100% |

**性能差异：GPU 比 CPU 快 3-5 倍**

---

## 🎯 快速检查清单

- [ ] 运行 `python check_gpu.py` 验证脚本
- [ ] 检查日志中的 "Metal available" 信息
- [ ] 使用 Activity Monitor 查看 GPU 使用率
- [ ] 对比处理时间（应该 < 30秒/页）
- [ ] 检查 Mac 型号（应该是 M1/M2/M3/M4）

---

## 💡 最佳实践

1. **定期验证**：每次更新 MLX 后验证 GPU 使用
2. **监控性能**：记录处理时间，异常时检查
3. **系统要求**：确保 macOS 13.0+ 和 Apple Silicon
4. **资源管理**：确保有足够内存（推荐 16GB+）

---

## 📝 总结

### 如何确认使用 GPU：

1. ✅ 运行验证脚本：`python check_gpu.py`
2. ✅ 查看日志：`📊 Metal available: True`
3. ✅ Activity Monitor：GPU 使用率 > 0%
4. ✅ 性能测试：处理时间 < 30秒/页

### 如果未使用 GPU：

1. ❌ 检查 Mac 型号（必须是 Apple Silicon）
2. ❌ 检查 macOS 版本（需要 13.0+）
3. ❌ 重新安装 MLX：`pip install --upgrade mlx mlx-vlm`
4. ❌ 检查系统日志是否有错误


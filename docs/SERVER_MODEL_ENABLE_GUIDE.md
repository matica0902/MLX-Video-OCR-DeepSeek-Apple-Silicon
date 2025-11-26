# 🚀 服务器环境模型启用指南

## 📋 模型启用的完整流程

### 步骤 1: 环境设置（必须在所有 import 之前）

```python
import os
os.environ['MLX_USE_CPU'] = '1'  # CPU 模式
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'
```

**说明**: 
- 服务器是 Linux CPU 环境，必须设置 `MLX_USE_CPU=1`
- 这必须在导入任何 MLX 库之前设置

### 步骤 2: 设置 HF_HOME

```python
from pathlib import Path
os.environ["HF_HOME"] = str(Path.home() / "hf_cache")
```

**说明**: 
- 设置 Hugging Face 缓存目录
- 服务器上通常是 `/tmp/hf_cache` 或 `/root/.cache/huggingface`

### 步骤 3: 导入库

```python
from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate
```

**说明**: 
- `PIL`: 图像处理
- `mlx.core`: MLX 核心库
- `mlx_vlm`: MLX 视觉语言模型库

### 步骤 4: 设置设备

```python
mx.set_default_device(mx.cpu)
```

**说明**: 
- 明确设置使用 CPU 设备
- 服务器环境必须使用 CPU 模式

### 步骤 5: 检查 Token

```python
hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
if hf_token:
    os.environ['HF_TOKEN'] = hf_token
    os.environ['HUGGINGFACE_TOKEN'] = hf_token
```

**说明**: 
- 检查 Hugging Face Token 是否设置
- 在 Hugging Face Spaces: Settings → Secrets → 添加 `HF_TOKEN`

### 步骤 6: 加载模型（启用模型）

```python
model_path = "mlx-community/DeepSeek-OCR-8bit"
model, processor = load(model_path)
```

**说明**: 
- 这是**启用模型**的关键步骤
- `load()` 函数会：
  1. 下载模型文件（如果不存在）
  2. 加载模型权重
  3. 初始化处理器
  4. 返回可用的模型和处理器对象

**成功标志**:
```
✅ Model loaded successfully!
```

### 步骤 7: 准备图像

```python
img = Image.open(image_path)
if img.mode != 'RGB':
    img = img.convert('RGB')
```

**说明**: 
- 加载图像
- 确保图像是 RGB 模式

### 步骤 8: 使用模型进行 OCR（调用模型）

```python
res = generate(
    model=model,
    processor=processor,
    image=img,
    prompt="<image>\nExtract all text from the image.",
    max_tokens=512,
    temperature=0.0,
    use_cache=False
)
```

**说明**: 
- 这是**使用模型**的关键步骤
- `generate()` 函数会：
  1. 处理图像和提示词
  2. 调用模型进行推理
  3. 生成 OCR 结果
  4. 返回结果对象

**参数说明**:
- `model`: 已加载的模型对象
- `processor`: 已加载的处理器对象
- `image`: PIL Image 对象
- `prompt`: 提示词（必须包含 `<image>`）
- `max_tokens`: 最大生成 token 数
- `temperature`: 温度参数（0.0 = 确定性输出）
- `use_cache=False`: CPU 模式下推荐禁用缓存

### 步骤 9: 处理结果

```python
text = res.text if hasattr(res, 'text') else str(res)
text = text.strip()
```

**说明**: 
- 从结果对象中提取文本
- 清理格式标记

## 🔧 在 app.py 中的实际使用

### 模型加载（在子进程中）

```python
def _load_model_for_subprocess():
    global _model_instance, _processor_instance
    
    # 设置设备
    mx.set_default_device(mx.cpu)
    
    # 加载模型
    model_path = "mlx-community/DeepSeek-OCR-8bit"
    _model_instance, _processor_instance = load(model_path)
    
    return True
```

### 使用模型（在子进程中）

```python
def _run_ocr_in_process(image_bytes, prompt, max_tokens, output_queue):
    # 1. 加载模型（如果未加载）
    if not _load_model_for_subprocess():
        return
    
    # 2. 准备图像
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 3. 设置设备
    mx.set_default_device(mx.cpu)
    
    # 4. 使用模型进行 OCR（带重试机制）
    max_retries = 3
    retry_tokens = [min(max_tokens, 2048), min(max_tokens, 512), 256]
    
    for attempt in range(max_retries):
        try:
            res = generate(
                model=_model_instance,
                processor=_processor_instance,
                image=img,
                prompt=prompt,
                max_tokens=retry_tokens[attempt],
                temperature=0.0,
                use_cache=False
            )
            if res is not None:
                break
        except AttributeError as e:
            if "'NoneType' object has no attribute 'token'" in str(e):
                # mlx-vlm bug，重试
                continue
            else:
                raise
    
    # 5. 处理结果
    text = res.text if hasattr(res, 'text') else str(res)
    text = text.strip()
    
    # 6. 返回结果
    output_queue.put({'success': True, 'text': text})
```

## ✅ 模型启用成功的标志

1. **模型加载成功**:
   ```
   ✅ Model loaded successfully!
   ```

2. **generate() 调用成功**:
   ```
   ✅ OCR completed, text length: XXX
   ```

3. **返回有效结果**:
   - `res` 不为 `None`
   - `res.text` 包含 OCR 结果

## ❌ 常见错误及解决方案

### 错误 1: `'NoneType' object has no attribute 'token'`

**原因**: `mlx-vlm` 0.3.5 的 bug，`stream_generate()` 没有产生响应

**解决方案**:
1. 使用更小的 `max_tokens` 值（256-512）
2. 添加重试机制（代码已实现）
3. 降级到 `mlx-vlm==0.3.4`

### 错误 2: `401 Client Error: Unauthorized`

**原因**: HF_TOKEN 未设置或无效

**解决方案**:
1. 在 Hugging Face Spaces: Settings → Secrets → 添加 `HF_TOKEN`
2. 确保 token 有 Read 权限
3. 重新部署应用

### 错误 3: `Model load failed`

**原因**: 
- 网络问题
- 磁盘空间不足
- 模型仓库需要接受使用条款

**解决方案**:
1. 检查网络连接
2. 检查磁盘空间
3. 访问模型页面接受使用条款

## 🧪 测试模型启用

### 在服务器上运行测试

```bash
# 在服务器容器中运行
python /app/test_server_model_enable.py
```

### 测试脚本会验证:

1. ✅ 环境变量设置
2. ✅ 库导入
3. ✅ 设备设置
4. ✅ Token 检查
5. ✅ 模型加载（启用）
6. ✅ 图像准备
7. ✅ 模型使用（OCR）
8. ✅ 结果处理

## 📊 总结

**模型启用的关键步骤**:
1. 环境设置 (`MLX_USE_CPU=1`)
2. 设备设置 (`mx.set_default_device(mx.cpu)`)
3. 加载模型 (`load()`) ← **这是启用模型**
4. 调用 generate() ← **这是使用模型**

**在服务器环境**:
- 必须使用 CPU 模式
- 必须设置 HF_TOKEN
- 必须处理 `mlx-vlm` 的 bug（使用重试机制）
- 建议使用较小的 `max_tokens` 值




# DeepSeek-OCR 图片格式支持说明

## 📸 支持的图片格式

### ✅ 标准格式
- **PNG** (.png) - 推荐，支持透明背景
- **JPEG/JPG** (.jpg, .jpeg) - 推荐，文件较小
- **RGB 模式** - 所有图片会自动转换为 RGB

### 📋 当前代码设置
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
```

## 🔍 模型处理流程

### 1. 图片加载
- 使用 `PIL.Image.open()` 加载图片
- 自动转换为 RGB 模式
- 支持常见图片格式（PNG, JPEG, BMP, TIFF 等）

### 2. 图片预处理
- DeepSeek-OCR 会自动调整图片大小
- 支持动态预处理（dynamic_preprocess）
- 自动处理不同宽高比

### 3. 图片要求

#### ✅ 推荐设置
- **格式**: PNG 或 JPEG
- **大小**: 最大 16MB（当前设置）
- **分辨率**: 建议 300-1200 DPI
- **模式**: RGB（会自动转换）

#### ⚠️ 注意事项
- 低分辨率图片可能影响识别准确率
- 模糊、倾斜的图片效果较差
- 手写体识别准确率较低

## 🛠️ 输出清理

### 已实施的清理措施

1. **跳过特殊标记**
   ```python
   skip_special_tokens=True  # 移除 <｜begin▁of▁sentence｜> 等
   ```

2. **清理特殊标记**
   ```python
   re.sub(r'<\|[^|]+\|>', '', output_text)  # 移除 <|xxx|> 格式
   ```

3. **清理重复模式**
   ```python
   re.sub(r'(.{1,10})\1{10,}', r'\1', output_text)  # 移除重复内容
   ```

4. **清理格式**
   ```python
   re.sub(r'\n{3,}', '\n\n', output_text)  # 清理多余换行
   re.sub(r' {3,}', ' ', output_text)  # 清理多余空格
   ```

## 📊 常见问题

### Q1: 为什么输出有 `<｜begin▁of▁sentence｜>`？
**A:** 这是模型的特殊标记，已添加 `skip_special_tokens=True` 和正则清理来移除。

### Q2: 为什么有重复的 `2.2.2.2.2.2...`？
**A:** 可能是模型生成时的重复问题，已添加重复模式清理。

### Q3: 支持哪些图片格式？
**A:** 
- **当前限制**: PNG, JPG, JPEG（前端限制）
- **实际支持**: PNG, JPEG, BMP, TIFF 等（PIL 支持的格式）
- **推荐**: PNG（无损）或 JPEG（文件小）

### Q4: 如何支持更多格式？
**A:** 修改 `ALLOWED_EXTENSIONS`：
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}
```

## 🔧 优化建议

### 1. 图片预处理
- 上传前调整大小（如果太大）
- 确保图片清晰
- 避免过度压缩

### 2. 输出后处理
- 已添加清理逻辑
- 可以进一步自定义清理规则

### 3. 错误处理
- 检查图片是否损坏
- 验证图片格式
- 处理超大图片


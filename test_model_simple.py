#!/usr/bin/env python3
"""
快速测试 MLX DeepSeek-OCR 模型
最小化测试，快速定位问题
"""

import os
os.environ['MLX_USE_CPU'] = '1'
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("=" * 60)
print("🧪 快速测试 MLX DeepSeek-OCR")
print("=" * 60)

# 1. 设置设备
print("\n[1/4] 设置 CPU 设备...")
mx.set_default_device(mx.cpu)
print(f"✅ 设备: {mx.default_device()}")

# 2. 加载模型
print("\n[2/4] 加载模型...")
try:
    model, processor = load("mlx-community/DeepSeek-OCR-8bit")
    print("✅ 模型加载成功")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    exit(1)

# 3. 创建最小测试图像
print("\n[3/4] 创建测试图像...")
img = Image.new('RGB', (256, 256), color='white')
print(f"✅ 图像: {img.size}, {img.mode}")

# 4. 测试生成 - 最小参数
print("\n[4/4] 测试生成...")
print("参数: use_cache=False, max_tokens=100")

try:
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt="<image>\nExtract text.",
        max_tokens=100,
        temperature=0.0,
        use_cache=False
    )
    
    if res is None:
        print("❌ 返回 None")
        exit(1)
    
    text = res.text if hasattr(res, 'text') else str(res)
    print(f"✅ 生成成功!")
    print(f"结果长度: {len(text)} 字符")
    print(f"结果预览: {text[:100]}...")
    
except Exception as e:
    print(f"❌ 生成失败!")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    import traceback
    print("\n完整错误堆栈:")
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ 所有测试通过!")
print("=" * 60)

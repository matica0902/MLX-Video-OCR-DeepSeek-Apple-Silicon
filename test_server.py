#!/usr/bin/env python3
"""
服务器环境测试脚本
测试 MLX DeepSeek-OCR 在 CPU 模式下是否能正常工作
"""

import os
os.environ['MLX_USE_CPU'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("=" * 60)
print("服务器环境测试")
print("=" * 60)

# 1. 设置设备
mx.set_default_device(mx.cpu)
print(f"设备: {mx.default_device()}")

# 2. 加载模型
print("\n加载模型...")
model, processor = load("mlx-community/DeepSeek-OCR-8bit")
print("模型加载成功")

# 3. 创建测试图像
img = Image.new('RGB', (100, 100), color='white')
print(f"图像: {img.size}")

# 4. 测试 1: 不使用 use_cache 参数（默认）
print("\n测试 1: 默认参数（不指定 use_cache）...")
try:
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt="<image>\nText:",
        max_tokens=50,
        temperature=0.0
    )
    print(f"✅ 成功: {type(res)}")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试 2: 使用 use_cache=False
print("\n测试 2: use_cache=False...")
try:
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt="<image>\nText:",
        max_tokens=50,
        temperature=0.0,
        use_cache=False
    )
    print(f"✅ 成功: {type(res)}")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# 6. 测试 3: 使用 use_cache=True
print("\n测试 3: use_cache=True...")
try:
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt="<image>\nText:",
        max_tokens=50,
        temperature=0.0,
        use_cache=True
    )
    print(f"✅ 成功: {type(res)}")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)




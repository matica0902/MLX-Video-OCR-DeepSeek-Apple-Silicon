#!/usr/bin/env python3
"""
服务器调试脚本 - 找出能工作的参数组合
在服务器运行: python /app/test_server_debug.py
"""

import os
os.environ['MLX_USE_CPU'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("=" * 70)
print("服务器环境调试 - 找出能工作的参数组合")
print("=" * 70)

# 设置设备
mx.set_default_device(mx.cpu)
print(f"设备: {mx.default_device()}")

# 加载模型
print("\n加载模型...")
model, processor = load("mlx-community/DeepSeek-OCR-8bit")
print("✓ 模型加载成功")

# 创建图像
img = Image.new('RGB', (256, 256), color='white')
print(f"✓ 图像: {img.size}")

# 测试不同的调用方式
print("\n" + "=" * 70)
print("测试不同的 generate() 调用方式")
print("=" * 70)

# 方式 1: 最少参数
print("\n[1] 测试: 只有必需参数")
try:
    res = generate(model=model, processor=processor, image=img, prompt="<image>\nText:")
    print(f"  ✅ 成功! {type(res)}")
    if res:
        text = res.text if hasattr(res, 'text') else str(res)
        print(f"  结果: {text[:50]}")
except Exception as e:
    print(f"  ❌ 失败: {type(e).__name__}: {str(e)[:100]}")

# 方式 2: 添加 max_tokens
print("\n[2] 测试: 添加 max_tokens=50")
try:
    res = generate(model=model, processor=processor, image=img, prompt="<image>\nText:", max_tokens=50)
    print(f"  ✅ 成功! {type(res)}")
except Exception as e:
    print(f"  ❌ 失败: {type(e).__name__}: {str(e)[:100]}")

# 方式 3: 添加 temperature
print("\n[3] 测试: 添加 temperature=0.0")
try:
    res = generate(model=model, processor=processor, image=img, prompt="<image>\nText:", max_tokens=50, temperature=0.0)
    print(f"  ✅ 成功! {type(res)}")
except Exception as e:
    print(f"  ❌ 失败: {type(e).__name__}: {str(e)[:100]}")

# 方式 4: 尝试更小的 max_tokens
print("\n[4] 测试: max_tokens=10 (很小)")
try:
    res = generate(model=model, processor=processor, image=img, prompt="<image>\nText:", max_tokens=10, temperature=0.0)
    print(f"  ✅ 成功! {type(res)}")
except Exception as e:
    print(f"  ❌ 失败: {type(e).__name__}: {str(e)[:100]}")

# 方式 5: 尝试不同的 prompt 格式
print("\n[5] 测试: 不同的 prompt 格式")
try:
    res = generate(model=model, processor=processor, image=img, prompt="<image>", max_tokens=50, temperature=0.0)
    print(f"  ✅ 成功! {type(res)}")
except Exception as e:
    print(f"  ❌ 失败: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)




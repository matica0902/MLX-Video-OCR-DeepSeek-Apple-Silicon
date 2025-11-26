#!/usr/bin/env python3
"""最基础的测试 - 只测试 generate 函数调用"""

import os
os.environ['MLX_USE_CPU'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("测试开始...")

# 设置设备
mx.set_default_device(mx.cpu)
print("✓ 设备设置完成")

# 加载模型
print("加载模型...")
model, processor = load("mlx-community/DeepSeek-OCR-8bit")
print("✓ 模型加载完成")

# 创建图像
img = Image.new('RGB', (100, 100), color='white')
print("✓ 图像创建完成")

# 测试生成
print("测试 generate()...")
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
    print(f"✓ 生成成功: {type(res)}")
    if res:
        print(f"✓ 结果: {str(res)[:50]}")
    else:
        print("✗ 返回 None")
except Exception as e:
    print(f"✗ 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("测试完成")




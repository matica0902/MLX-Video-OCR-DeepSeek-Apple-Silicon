#!/usr/bin/env python3
"""最简测试 - 只测试模型能否启动和生成"""

import os
os.environ['MLX_USE_CPU'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

# 设置设备
mx.set_default_device(mx.cpu)

# 加载模型
print("加载模型...")
model, processor = load("mlx-community/DeepSeek-OCR-8bit")
print("✓ 模型加载成功")

# 创建图像
img = Image.new('RGB', (100, 100), color='white')
print("✓ 图像创建")

# 测试生成 - 最简参数
print("测试 generate()...")
res = generate(
    model=model,
    processor=processor,
    image=img,
    prompt="<image>\nText:",
    max_tokens=50,
    temperature=0.0
)

print(f"✓ 成功: {type(res)}")
if res:
    text = res.text if hasattr(res, 'text') else str(res)
    print(f"✓ 结果: {text[:50]}")

print("\n✅ 测试通过！模型可以正常工作")




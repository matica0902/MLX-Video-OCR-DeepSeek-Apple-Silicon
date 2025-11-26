#!/usr/bin/env python3
"""
服务器环境最简测试
在服务器上运行: python /app/test_server_minimal.py
"""

import os
os.environ['MLX_USE_CPU'] = '1'

print("=" * 60)
print("服务器环境测试 - MLX DeepSeek-OCR")
print("=" * 60)

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

# 1. 设置设备
mx.set_default_device(mx.cpu)
print(f"[1/4] 设备设置: {mx.default_device()}")

# 2. 加载模型
print("[2/4] 加载模型...")
try:
    model, processor = load("mlx-community/DeepSeek-OCR-8bit")
    print("[2/4] ✓ 模型加载成功")
except Exception as e:
    print(f"[2/4] ✗ 模型加载失败: {e}")
    exit(1)

# 3. 创建测试图像
print("[3/4] 创建测试图像...")
img = Image.new('RGB', (100, 100), color='white')
print(f"[3/4] ✓ 图像: {img.size}")

# 4. 测试 generate - 与 app.py 中完全相同的调用方式
print("[4/4] 测试 generate() - 使用与 app.py 相同的参数...")
print("      参数: model, processor, image, prompt, max_tokens, temperature")
print("      （不包含 use_cache）")

try:
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt="<image>\nExtract text.",
        max_tokens=50,
        temperature=0.0
    )
    
    if res is None:
        print("[4/4] ✗ generate() 返回 None")
        exit(1)
    
    text = res.text if hasattr(res, 'text') else str(res)
    print(f"[4/4] ✓ 生成成功!")
    print(f"      结果长度: {len(text)} 字符")
    print(f"      结果: {text[:100]}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！模型可以正常工作")
    print("=" * 60)
    
except Exception as e:
    print(f"[4/4] ✗ 生成失败!")
    print(f"      错误类型: {type(e).__name__}")
    print(f"      错误信息: {str(e)}")
    import traceback
    print("\n完整错误堆栈:")
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("❌ 测试失败 - 需要进一步调试")
    print("=" * 60)
    exit(1)




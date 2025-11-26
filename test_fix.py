#!/usr/bin/env python3
"""
测试修复后的代码逻辑
模拟 app.py 中的 _run_ocr_in_process 函数
"""

import os
os.environ['MLX_USE_CPU'] = '1'

import io
from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("=" * 60)
print("测试修复后的代码逻辑")
print("=" * 60)

# 1. 设置设备
mx.set_default_device(mx.cpu)
print(f"✅ 设备设置: {mx.default_device()}")

# 2. 加载模型
print("\n加载模型...")
model, processor = load("mlx-community/DeepSeek-OCR-8bit")
print("✅ 模型加载成功")

# 3. 模拟 app.py 中的图像处理流程
print("\n模拟图像处理...")
img = Image.new('RGB', (512, 512), color='white')
if img.mode != 'RGB':
    img = img.convert('RGB')
print(f"✅ 图像: {img.size}, mode: {img.mode}")

# 4. 测试修复后的 generate 调用（与 app.py 中一致）
print("\n测试修复后的 generate 调用...")
print("参数: model, processor, image, prompt, max_tokens, temperature")
print("（不包含 use_cache 参数）")

prompt = "<image>\nExtract all text from the image."
max_tokens = 512

try:
    # 这是修复后的调用方式（与 app.py 第 472-479 行一致）
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.0
    )
    
    # 检查结果
    if res is None:
        print("❌ generate() 返回 None")
        exit(1)
    
    text = res.text if hasattr(res, 'text') else str(res)
    print(f"✅ 生成成功!")
    print(f"结果长度: {len(text)} 字符")
    print(f"结果预览: {text[:100]}...")
    
    print("\n" + "=" * 60)
    print("✅ 测试通过！修复后的代码可以正常工作")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 测试失败!")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    import traceback
    print("\n完整错误堆栈:")
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("❌ 修复后的代码仍有问题，需要进一步调试")
    print("=" * 60)
    exit(1)




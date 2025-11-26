#!/usr/bin/env python3
"""
验证修复后的代码是否能正常工作
测试 mlx-vlm generate() 函数在不同参数下的行为
"""

import os
os.environ['MLX_USE_CPU'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("=" * 70)
print("验证修复 - 测试不同 max_tokens 值")
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

# 测试不同的 max_tokens 值
test_cases = [
    {"max_tokens": 50, "name": "小值 (50)"},
    {"max_tokens": 512, "name": "中等值 (512)"},
    {"max_tokens": 2048, "name": "大值 (2048)"},
    {"max_tokens": 4096, "name": "很大值 (4096)"},
]

print("\n" + "=" * 70)
print("测试不同 max_tokens 值")
print("=" * 70)

success_count = 0
fail_count = 0

for i, test_case in enumerate(test_cases, 1):
    max_tokens = test_case["max_tokens"]
    name = test_case["name"]
    
    print(f"\n[测试 {i}] {name} - max_tokens={max_tokens}")
    
    try:
        res = generate(
            model=model,
            processor=processor,
            image=img,
            prompt="<image>\nExtract text.",
            max_tokens=max_tokens,
            temperature=0.0,
            use_cache=False
        )
        
        if res is None:
            print(f"  ✗ 返回 None")
            fail_count += 1
            continue
        
        text = res.text if hasattr(res, 'text') else str(res)
        if text:
            print(f"  ✓ 成功! 结果长度: {len(text)} 字符")
            print(f"  结果预览: {text[:50]}...")
            success_count += 1
        else:
            print(f"  ⚠️  成功但结果为空")
            success_count += 1
            
    except AttributeError as e:
        if "'NoneType' object has no attribute 'token'" in str(e):
            print(f"  ✗ 检测到 mlx-vlm bug: last_response 为 None")
            print(f"  这说明 stream_generate() 没有产生任何响应")
            fail_count += 1
        else:
            print(f"  ✗ AttributeError: {e}")
            fail_count += 1
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {e}")
        fail_count += 1

print("\n" + "=" * 70)
print(f"测试结果: 成功 {success_count}/{len(test_cases)}, 失败 {fail_count}/{len(test_cases)}")
print("=" * 70)

if success_count > 0:
    print("\n✅ 至少有一个测试通过，说明修复可能有效")
else:
    print("\n❌ 所有测试都失败，需要进一步调试")




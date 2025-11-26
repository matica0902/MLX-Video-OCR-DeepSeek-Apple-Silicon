#!/usr/bin/env python3
"""
找出启动模型的最基本方式
尝试不同的参数组合，找出最小可工作的配置
"""

import os
os.environ['MLX_USE_CPU'] = '1'
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

print("=" * 70)
print("🔍 寻找模型启动的最基本方式")
print("=" * 70)

# 1. 设置设备
print("\n[步骤 1] 设置 CPU 设备...")
mx.set_default_device(mx.cpu)
print(f"✅ 设备: {mx.default_device()}")

# 2. 加载模型
print("\n[步骤 2] 加载模型...")
try:
    model, processor = load("mlx-community/DeepSeek-OCR-8bit")
    print("✅ 模型加载成功")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    exit(1)

# 3. 创建测试图像
print("\n[步骤 3] 创建测试图像...")
img = Image.new('RGB', (256, 256), color='white')
print(f"✅ 图像: {img.size}, {img.mode}")

# 4. 尝试不同的调用方式
print("\n" + "=" * 70)
print("🧪 尝试不同的 generate() 调用方式")
print("=" * 70)

test_cases = [
    {
        "name": "方式 1: 最少参数（只有必需参数）",
        "params": {
            "model": model,
            "processor": processor,
            "image": img,
            "prompt": "<image>\nText:"
        }
    },
    {
        "name": "方式 2: 添加 max_tokens",
        "params": {
            "model": model,
            "processor": processor,
            "image": img,
            "prompt": "<image>\nText:",
            "max_tokens": 50
        }
    },
    {
        "name": "方式 3: 添加 temperature=0.0",
        "params": {
            "model": model,
            "processor": processor,
            "image": img,
            "prompt": "<image>\nText:",
            "max_tokens": 50,
            "temperature": 0.0
        }
    },
    {
        "name": "方式 4: 添加 verbose=False",
        "params": {
            "model": model,
            "processor": processor,
            "image": img,
            "prompt": "<image>\nText:",
            "max_tokens": 50,
            "temperature": 0.0,
            "verbose": False
        }
    },
    {
        "name": "方式 5: 添加 use_cache=True",
        "params": {
            "model": model,
            "processor": processor,
            "image": img,
            "prompt": "<image>\nText:",
            "max_tokens": 50,
            "temperature": 0.0,
            "use_cache": True
        }
    },
    {
        "name": "方式 6: 添加 use_cache=False",
        "params": {
            "model": model,
            "processor": processor,
            "image": img,
            "prompt": "<image>\nText:",
            "max_tokens": 50,
            "temperature": 0.0,
            "use_cache": False
        }
    }
]

successful_method = None

for i, test_case in enumerate(test_cases, 1):
    print(f"\n[测试 {i}] {test_case['name']}")
    print(f"参数: {list(test_case['params'].keys())}")
    
    try:
        res = generate(**test_case['params'])
        
        if res is None:
            print("  ⚠️  返回 None")
            continue
        
        text = res.text if hasattr(res, 'text') else str(res)
        print(f"  ✅ 成功! 结果长度: {len(text)} 字符")
        
        if successful_method is None:
            successful_method = test_case
            print(f"  🎯 这是第一个成功的方式！")
            print(f"  📝 推荐使用此配置:")
            print(f"     参数: {list(test_case['params'].keys())}")
            
    except AttributeError as e:
        if "'NoneType' object has no attribute 'token'" in str(e):
            print(f"  ❌ 失败: 已知错误 - last_response 为 None")
        else:
            print(f"  ❌ 失败: {e}")
    except Exception as e:
        print(f"  ❌ 失败: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
if successful_method:
    print("✅ 找到可工作的方式！")
    print("\n推荐的最基本调用方式:")
    print("-" * 70)
    print("res = generate(")
    for key, value in successful_method['params'].items():
        if key in ['model', 'processor', 'image']:
            print(f"    {key}={key},")
        else:
            print(f"    {key}={repr(value)},")
    print(")")
    print("-" * 70)
else:
    print("❌ 所有方式都失败了")
    print("可能需要检查:")
    print("  1. mlx-vlm 版本是否兼容")
    print("  2. 模型文件是否完整")
    print("  3. CPU 模式是否支持")
print("=" * 70)




#!/usr/bin/env python3
"""
服务器环境最终测试脚本
运行方式: python /app/test_server_final.py
"""

import os
import sys
os.environ['MLX_USE_CPU'] = '1'

print("=" * 70)
print("服务器环境测试 - MLX DeepSeek-OCR")
print("=" * 70)

try:
    from PIL import Image
    import mlx.core as mx
    from mlx_vlm import load, generate
    
    # 1. 设置设备
    mx.set_default_device(mx.cpu)
    print(f"[1] 设备设置: {mx.default_device()}")
    
    # 2. 加载模型
    print("[2] 加载模型...")
    model, processor = load("mlx-community/DeepSeek-OCR-8bit")
    print("[2] ✓ 模型加载成功")
    
    # 3. 创建图像
    img = Image.new('RGB', (256, 256), color='white')
    print(f"[3] ✓ 图像创建: {img.size}")
    
    # 4. 测试生成 - 与 app.py 完全相同的调用
    print("[4] 测试 generate() - 与 app.py 相同的参数...")
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt="<image>\nExtract text.",
        max_tokens=50,
        temperature=0.0
    )
    
    if res is None:
        print("[4] ✗ 返回 None")
        sys.exit(1)
    
    text = res.text if hasattr(res, 'text') else str(res)
    print(f"[4] ✓ 成功! 结果: {text[:50]}")
    
    print("\n" + "=" * 70)
    print("✅ 测试通过！模型可以正常工作")
    print("=" * 70)
    sys.exit(0)
    
except AttributeError as e:
    if "'NoneType' object has no attribute 'token'" in str(e):
        print(f"\n[4] ✗ 检测到已知错误: last_response 为 None")
        print("这是 mlx-vlm 库在 CPU 模式下的 bug")
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n[4] ✗ 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)




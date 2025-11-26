#!/usr/bin/env python3
"""快速测试 - 只检查导入和函数签名"""

import os
os.environ['MLX_USE_CPU'] = '1'

print("=" * 60)
print("快速诊断测试")
print("=" * 60)

# 1. 测试导入
print("\n[1] 测试导入...")
try:
    import mlx.core as mx
    from mlx_vlm import load, generate
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    exit(1)

# 2. 检查 generate 函数签名
print("\n[2] 检查 generate 函数...")
import inspect
sig = inspect.signature(generate)
print(f"✅ generate 函数参数: {list(sig.parameters.keys())}")

# 3. 检查是否有 use_cache 参数
if 'use_cache' in sig.parameters:
    print(f"✅ use_cache 参数存在，默认值: {sig.parameters['use_cache'].default}")
else:
    print("⚠️  use_cache 参数不存在！")

# 4. 测试设备设置
print("\n[3] 测试设备设置...")
mx.set_default_device(mx.cpu)
print(f"✅ 设备: {mx.default_device()}")

print("\n" + "=" * 60)
print("基础检查完成！")
print("=" * 60)




#!/usr/bin/env python3
"""
诊断脚本 - 检查 mlx-vlm 版本和参数支持
"""

import os
os.environ['MLX_USE_CPU'] = '1'

import sys

print("=" * 60)
print("MLX-VLM 诊断工具")
print("=" * 60)

# 1. 检查版本
print("\n[1] 检查已安装的版本...")
try:
    import mlx_vlm
    print(f"mlx-vlm 位置: {mlx_vlm.__file__}")
    
    # 尝试获取版本
    try:
        version = mlx_vlm.__version__
        print(f"mlx-vlm 版本: {version}")
    except:
        print("无法获取版本号")
    
    import mlx
    try:
        mlx_version = mlx.__version__
        print(f"mlx 版本: {mlx_version}")
    except:
        print("无法获取 mlx 版本号")
        
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 2. 检查 generate 函数签名
print("\n[2] 检查 generate 函数参数...")
try:
    from mlx_vlm import generate
    import inspect
    sig = inspect.signature(generate)
    params = list(sig.parameters.keys())
    print(f"generate 函数参数: {params}")
    
    # 检查关键参数
    if 'use_cache' in params:
        default = sig.parameters['use_cache'].default
        print(f"  - use_cache: 默认值 = {default}")
    else:
        print("  - use_cache: 不存在")
        
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 尝试查看 generate.py 源码（如果可能）
print("\n[3] 检查 generate.py 源码位置...")
try:
    import mlx_vlm.generate as gen_module
    print(f"generate.py 位置: {gen_module.__file__}")
    
    # 尝试读取第 572 行附近
    try:
        with open(gen_module.__file__, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 572:
                print(f"\n第 570-575 行内容:")
                for i in range(569, min(576, len(lines))):
                    print(f"  {i+1}: {lines[i].rstrip()}")
    except Exception as e:
        print(f"无法读取源码: {e}")
        
except Exception as e:
    print(f"无法定位源码: {e}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)




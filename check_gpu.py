#!/usr/bin/env python3
"""
GPU/Metal 验证脚本
用于检查 MLX 是否真的在使用 GPU（Metal）而不是 CPU
"""

import mlx.core as mx
import mlx.nn as nn
import numpy as np
import time
import sys

def check_metal_availability():
    """检查 Metal 是否可用"""
    print("=" * 60)
    print("🔍 MLX Metal GPU 验证工具")
    print("=" * 60)
    print()
    
    # 1. 检查 Metal 是否可用
    print("1️⃣ 检查 Metal 可用性...")
    metal_available = mx.metal.is_available()
    print(f"   Metal 可用: {'✅ 是' if metal_available else '❌ 否'}")
    
    if not metal_available:
        print("   ⚠️  警告: Metal 不可用，MLX 将使用 CPU")
        print("   💡 可能原因:")
        print("      - 不是 Apple Silicon Mac (M1/M2/M3/M4)")
        print("      - macOS 版本过低")
        print("      - MLX 安装问题")
        return False
    
    print()
    
    # 2. 检查默认设备
    print("2️⃣ 检查默认计算设备...")
    default_device = mx.default_device()
    print(f"   默认设备: {default_device}")
    
    if 'gpu' in str(default_device).lower() or 'metal' in str(default_device).lower():
        print("   ✅ 使用 GPU/Metal")
    else:
        print("   ⚠️  可能使用 CPU")
    
    print()
    
    # 3. 性能测试：GPU vs CPU
    print("3️⃣ 性能测试（GPU vs CPU）...")
    print("   创建测试矩阵...")
    
    # 创建较大的矩阵进行测试
    size = 2048
    a = mx.random.normal((size, size))
    b = mx.random.normal((size, size))
    
    # GPU 测试
    print("   🔥 测试 GPU 性能...")
    start_time = time.time()
    for _ in range(10):
        c = mx.matmul(a, b)
        mx.eval(c)  # 强制执行
    gpu_time = time.time() - start_time
    print(f"   GPU 时间: {gpu_time:.4f} 秒 (10次矩阵乘法)")
    
    # CPU 测试（强制使用 CPU）
    print("   🐌 测试 CPU 性能（对比）...")
    a_cpu = mx.array(np.array(a), device=mx.cpu)
    b_cpu = mx.array(np.array(b), device=mx.cpu)
    
    start_time = time.time()
    for _ in range(10):
        c_cpu = mx.matmul(a_cpu, b_cpu)
        mx.eval(c_cpu)
    cpu_time = time.time() - start_time
    print(f"   CPU 时间: {cpu_time:.4f} 秒 (10次矩阵乘法)")
    
    speedup = cpu_time / gpu_time if gpu_time > 0 else 0
    print(f"   ⚡ 加速比: {speedup:.2f}x")
    
    if speedup > 2:
        print("   ✅ GPU 加速明显，正在使用 Metal")
    elif speedup > 1.2:
        print("   ⚠️  GPU 加速不明显，可能部分使用 CPU")
    else:
        print("   ❌ 几乎没有 GPU 加速，可能主要使用 CPU")
    
    print()
    
    # 4. 检查 Metal 设备信息
    print("4️⃣ Metal 设备信息...")
    try:
        if hasattr(mx.metal, 'get_device_count'):
            device_count = mx.metal.get_device_count()
            print(f"   Metal 设备数量: {device_count}")
        
        # 尝试获取设备名称
        if hasattr(mx.metal, 'get_device_name'):
            try:
                device_name = mx.metal.get_device_name(0)
                print(f"   设备名称: {device_name}")
            except:
                pass
    except Exception as e:
        print(f"   ⚠️  无法获取设备信息: {e}")
    
    print()
    
    # 5. 实际模型加载测试
    print("5️⃣ 测试模型加载（如果可能）...")
    try:
        from mlx_vlm import load
        print("   尝试加载模型...")
        print("   ⏳ 这可能需要一些时间...")
        
        model_path = "mlx-community/DeepSeek-OCR-8bit"
        model, processor = load(model_path)
        print("   ✅ 模型加载成功")
        print(f"   📊 Metal 可用: {mx.metal.is_available()}")
        
        # 清理
        del model, processor
        mx.clear_cache()
        
    except Exception as e:
        print(f"   ⚠️  模型加载测试跳过: {e}")
        print("   💡 这是正常的，如果模型未下载")
    
    print()
    
    # 6. 总结
    print("=" * 60)
    print("📊 验证结果总结")
    print("=" * 60)
    
    if metal_available and speedup > 2:
        print("✅ 结论: MLX 正在使用 GPU (Metal) 加速")
        print("   - Metal 可用: ✅")
        print("   - GPU 加速明显: ✅")
        print("   - 性能优化: ✅")
    elif metal_available:
        print("⚠️  结论: Metal 可用，但加速不明显")
        print("   - Metal 可用: ✅")
        print("   - GPU 加速: ⚠️  不明显")
        print("   - 建议: 检查系统配置")
    else:
        print("❌ 结论: 未使用 GPU，仅使用 CPU")
        print("   - Metal 可用: ❌")
        print("   - 性能: 受限")
        print("   - 建议: 检查 Mac 型号和 macOS 版本")
    
    print()
    return metal_available and speedup > 2

def check_system_info():
    """检查系统信息"""
    print("=" * 60)
    print("💻 系统信息")
    print("=" * 60)
    
    import platform
    import subprocess
    
    # macOS 版本
    print(f"macOS 版本: {platform.mac_ver()[0]}")
    
    # 处理器信息
    try:
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                              capture_output=True, text=True)
        cpu_info = result.stdout.strip()
        print(f"处理器: {cpu_info}")
        
        # 检查是否是 Apple Silicon
        if 'Apple' in cpu_info or 'M1' in cpu_info or 'M2' in cpu_info or 'M3' in cpu_info or 'M4' in cpu_info:
            print("✅ Apple Silicon 检测到")
        else:
            print("⚠️  不是 Apple Silicon，MLX Metal 可能不可用")
    except:
        print("⚠️  无法获取处理器信息")
    
    print()

if __name__ == "__main__":
    check_system_info()
    result = check_metal_availability()
    
    print()
    print("=" * 60)
    if result:
        print("✅ 验证完成: GPU (Metal) 正在使用")
    else:
        print("⚠️  验证完成: 请检查上述信息")
    print("=" * 60)
    
    sys.exit(0 if result else 1)


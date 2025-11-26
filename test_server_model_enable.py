#!/usr/bin/env python3
"""
服务器环境模型启用测试
展示如何在服务器（Hugging Face Spaces）上启用和使用 MLX DeepSeek-OCR 模型
运行方式: python /app/test_server_model_enable.py
"""

import os
import sys

print("=" * 70)
print("🚀 服务器环境模型启用测试")
print("=" * 70)

# ============================================================================
# 步骤 1: 环境设置（必须在所有 import 之前）
# ============================================================================
print("\n[步骤 1] 设置 CPU 模式环境变量...")
os.environ['MLX_USE_CPU'] = '1'
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'
print("✅ MLX_USE_CPU=1 (CPU 模式)")
print("✅ METAL_DEVICE_WRAPPER_TYPE=1")

# ============================================================================
# 步骤 2: 设置 HF_HOME（与 app.py 一致）
# ============================================================================
from pathlib import Path
os.environ["HF_HOME"] = str(Path.home() / "hf_cache")
print(f"✅ HF_HOME: {os.environ['HF_HOME']}")

# ============================================================================
# 步骤 3: 导入库
# ============================================================================
print("\n[步骤 2] 导入必要的库...")
try:
    from PIL import Image
    import mlx.core as mx
    from mlx_vlm import load, generate
    print("✅ PIL, mlx.core, mlx_vlm 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# ============================================================================
# 步骤 4: 设置 MLX 设备
# ============================================================================
print("\n[步骤 3] 设置 MLX 设备为 CPU...")
mx.set_default_device(mx.cpu)
device = mx.default_device()
print(f"✅ 设备设置: {device}")
print("   说明: 服务器环境使用 CPU 模式")

# ============================================================================
# 步骤 5: 检查 Hugging Face Token
# ============================================================================
print("\n[步骤 4] 检查 Hugging Face Token...")
hf_token = (
    os.environ.get('HF_TOKEN') or 
    os.environ.get('HUGGINGFACE_TOKEN') or 
    os.environ.get('HUGGING_FACE_HUB_TOKEN')
)

if hf_token:
    print(f"✅ HF_TOKEN 已设置 (长度: {len(hf_token)})")
    # 确保所有环境变量都设置
    os.environ['HF_TOKEN'] = hf_token
    os.environ['HUGGINGFACE_TOKEN'] = hf_token
    os.environ['HUGGING_FACE_HUB_TOKEN'] = hf_token
else:
    print("⚠️  HF_TOKEN 未设置")
    print("   在 Hugging Face Spaces:")
    print("   Settings → Secrets → 添加 HF_TOKEN")
    print("   或设置环境变量: export HF_TOKEN=your_token")

# ============================================================================
# 步骤 6: 加载模型（启用模型）
# ============================================================================
print("\n[步骤 5] 加载 MLX DeepSeek-OCR 模型（启用模型）...")
print("-" * 70)

model_path = "mlx-community/DeepSeek-OCR-8bit"
print(f"📦 模型路径: {model_path}")
print(f"📁 HF_HOME: {os.environ.get('HF_HOME', 'Not set')}")
print(f"🔧 MLX_USE_CPU: {os.environ.get('MLX_USE_CPU', 'Not set')}")

try:
    print("⏳ 正在加载模型（这可能需要几分钟）...")
    model, processor = load(model_path)
    
    if model is None or processor is None:
        print("❌ 模型或处理器为 None - 加载失败")
        sys.exit(1)
    
    print("✅ 模型加载成功！模型已启用")
    print(f"   模型类型: {type(model).__name__}")
    print(f"   处理器类型: {type(processor).__name__}")
    
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    print("\n可能的原因:")
    print("  1. HF_TOKEN 未设置或无效")
    print("  2. 网络连接问题")
    print("  3. 模型仓库需要接受使用条款")
    print("  4. 磁盘空间不足")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# 步骤 7: 创建测试图像
# ============================================================================
print("\n[步骤 6] 创建测试图像...")
try:
    img = Image.new('RGB', (256, 256), color='white')
    if img.mode != 'RGB':
        img = img.convert('RGB')
    print(f"✅ 图像创建成功: {img.size}, mode: {img.mode}")
except Exception as e:
    print(f"❌ 图像创建失败: {e}")
    sys.exit(1)

# ============================================================================
# 步骤 8: 使用模型进行 OCR（这是使用模型的关键步骤）
# ============================================================================
print("\n[步骤 7] 使用模型进行 OCR（调用 generate() 启用模型）...")
print("-" * 70)

# 使用与 app.py 完全相同的参数
prompt = "<image>\nExtract all text from the image."
max_tokens = 512

print(f"📝 Prompt: {prompt[:60]}...")
print(f"🔢 Max tokens: {max_tokens}")
print(f"🖼️  Image: {img.size}, mode: {img.mode}")
print(f"🌡️  Temperature: 0.0")
print(f"💾 Use cache: False")

try:
    print("\n⏳ 调用 generate() 启用模型进行 OCR...")
    
    # 这是启用和使用模型的关键步骤
    res = generate(
        model=model,              # 已加载的模型
        processor=processor,      # 已加载的处理器
        image=img,                # 输入图像
        prompt=prompt,            # 提示词
        max_tokens=max_tokens,    # 最大生成 token 数
        temperature=0.0,          # 温度参数（0.0 = 确定性输出）
        use_cache=False           # 不使用缓存（CPU 模式下推荐）
    )
    
    # 检查结果
    if res is None:
        print("❌ generate() 返回 None - 模型未正确启用")
        sys.exit(1)
    
    # 处理结果
    text = res.text if hasattr(res, 'text') else str(res)
    text = text.strip()
    
    if not text:
        print("⚠️  生成成功但结果为空")
    else:
        print(f"\n✅ 模型使用成功！OCR 结果:")
        print(f"   结果长度: {len(text)} 字符")
        print(f"   结果: {text[:200]}...")
    
    print("\n" + "=" * 70)
    print("✅ 模型启用和使用测试完成！")
    print("=" * 70)
    
    print("\n📋 服务器环境模型启用步骤总结:")
    print("   1. ✅ 设置环境变量 (MLX_USE_CPU=1)")
    print("   2. ✅ 设置 HF_HOME")
    print("   3. ✅ 导入库 (mlx.core, mlx_vlm)")
    print("   4. ✅ 设置设备 (mx.set_default_device(mx.cpu))")
    print("   5. ✅ 检查 Token (HF_TOKEN)")
    print("   6. ✅ 加载模型 (load()) - 模型启用")
    print("   7. ✅ 创建图像 (PIL Image)")
    print("   8. ✅ 调用 generate() - 使用模型进行 OCR")
    
    print("\n🎯 模型已成功启用并可以正常工作！")
    print("   现在可以在 Flask 应用中使用这个模型进行 OCR 处理。")
    
except AttributeError as e:
    if "'NoneType' object has no attribute 'token'" in str(e):
        print(f"\n❌ 检测到 mlx-vlm bug: last_response 为 None")
        print("   错误: stream_generate() 没有产生响应")
        print("\n解决方案:")
        print("   1. 使用更小的 max_tokens 值（如 256）")
        print("   2. 添加重试机制（代码已实现）")
        print("   3. 降级 mlx-vlm 版本到 0.3.4")
        print("   4. 检查模型是否正确加载")
    else:
        print(f"❌ AttributeError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ 模型使用失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)




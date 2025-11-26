#!/usr/bin/env python3
"""
模型启用测试 - 展示如何正确启用 MLX DeepSeek-OCR 模型
"""

import os
import sys

print("=" * 70)
print("🧪 MLX DeepSeek-OCR 模型启用测试")
print("=" * 70)

# ============================================================================
# 步骤 1: 环境设置（必须在所有 import 之前）
# ============================================================================
print("\n[步骤 1] 设置环境变量...")
os.environ['MLX_USE_CPU'] = '1'
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'
print("✅ MLX_USE_CPU=1")
print("✅ METAL_DEVICE_WRAPPER_TYPE=1")

# ============================================================================
# 步骤 2: 导入库
# ============================================================================
print("\n[步骤 2] 导入必要的库...")
try:
    from PIL import Image
    import mlx.core as mx
    from mlx_vlm import load, generate
    print("✅ 所有库导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# ============================================================================
# 步骤 3: 设置设备
# ============================================================================
print("\n[步骤 3] 设置 MLX 设备...")
mx.set_default_device(mx.cpu)
device = mx.default_device()
print(f"✅ 设备设置: {device}")

# ============================================================================
# 步骤 4: 检查 Hugging Face Token
# ============================================================================
print("\n[步骤 4] 检查 Hugging Face Token...")
hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
if hf_token:
    print(f"✅ HF_TOKEN 已设置 (长度: {len(hf_token)})")
    os.environ['HF_TOKEN'] = hf_token
    os.environ['HUGGINGFACE_TOKEN'] = hf_token
else:
    print("⚠️  HF_TOKEN 未设置（如果模型需要认证，可能会失败）")
    print("   设置方法: export HF_TOKEN=your_token")

# ============================================================================
# 步骤 5: 加载模型
# ============================================================================
print("\n[步骤 5] 加载 MLX DeepSeek-OCR 模型...")
model_path = "mlx-community/DeepSeek-OCR-8bit"
print(f"📦 模型路径: {model_path}")

try:
    model, processor = load(model_path)
    
    if model is None or processor is None:
        print("❌ 模型或处理器为 None")
        sys.exit(1)
    
    print("✅ 模型加载成功!")
    print(f"   模型类型: {type(model)}")
    print(f"   处理器类型: {type(processor)}")
    
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# 步骤 6: 创建测试图像
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
# 步骤 7: 测试模型生成（启用模型）
# ============================================================================
print("\n[步骤 7] 测试模型生成（启用模型进行 OCR）...")
print("=" * 70)

# 使用与 app.py 完全相同的参数
prompt = "<image>\nExtract all text from the image."
max_tokens = 512

print(f"📝 Prompt: {prompt[:50]}...")
print(f"🔢 Max tokens: {max_tokens}")
print(f"🖼️  Image: {img.size}, mode: {img.mode}")

try:
    # 这是启用模型的关键步骤
    res = generate(
        model=model,
        processor=processor,
        image=img,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.0,
        use_cache=False
    )
    
    # 检查结果
    if res is None:
        print("❌ generate() 返回 None")
        sys.exit(1)
    
    # 处理结果
    text = res.text if hasattr(res, 'text') else str(res)
    text = text.strip()
    
    if not text:
        print("⚠️  生成成功但结果为空")
    else:
        print(f"✅ 模型启用成功！生成结果:")
        print(f"   结果长度: {len(text)} 字符")
        print(f"   结果预览: {text[:100]}...")
    
    print("\n" + "=" * 70)
    print("✅ 模型启用测试完成！")
    print("=" * 70)
    print("\n📋 模型启用步骤总结:")
    print("   1. ✅ 设置环境变量 (MLX_USE_CPU=1)")
    print("   2. ✅ 导入库 (mlx.core, mlx_vlm)")
    print("   3. ✅ 设置设备 (mx.set_default_device(mx.cpu))")
    print("   4. ✅ 检查 Token (HF_TOKEN)")
    print("   5. ✅ 加载模型 (load())")
    print("   6. ✅ 创建图像 (PIL Image)")
    print("   7. ✅ 调用 generate() - 这是启用模型的关键步骤")
    print("\n🎯 模型已成功启用并可以正常工作！")
    
except AttributeError as e:
    if "'NoneType' object has no attribute 'token'" in str(e):
        print(f"\n❌ 检测到 mlx-vlm bug: last_response 为 None")
        print("   这说明 stream_generate() 没有产生响应")
        print("   解决方案:")
        print("   1. 使用更小的 max_tokens 值")
        print("   2. 添加重试机制")
        print("   3. 降级 mlx-vlm 版本")
    else:
        print(f"❌ AttributeError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ 模型启用失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)




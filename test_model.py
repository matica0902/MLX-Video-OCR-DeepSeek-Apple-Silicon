# test_model.py
import os
from pathlib import Path
from mlx_vlm import load, generate
from PIL import Image
import mlx.core as mx

# 1. 設定環境
os.environ["HF_HOME"] = str(Path.home() / "hf_cache")

# 2. 檢查 MLX
print(f"✅ MLX Metal available: {mx.metal.is_available()}")

# 3. 載入模型
print("⏳ Loading model...")
try:
    model, processor = load("mlx-community/DeepSeek-OCR-4bit")
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Model load failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. 測試圖像 OCR
print("⏳ Testing OCR...")
try:
    # 創建測試圖像
    test_img = Image.new('RGB', (100, 100), color='red')
    
    result = generate(
        model=model,
        processor=processor,
        image=test_img,
        prompt="<image>\nWhat do you see?",
        max_tokens=100,
        temperature=0.0,
        verbose=False
    )
    
    print(f"✅ OCR result type: {type(result)}")
    print(f"✅ Result: {result}")
except Exception as e:
    print(f"❌ OCR failed: {e}")
    import traceback
    traceback.print_exc()
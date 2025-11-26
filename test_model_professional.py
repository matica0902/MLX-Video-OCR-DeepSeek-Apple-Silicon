#!/usr/bin/env python3
"""
专业的 MLX DeepSeek-OCR 模型测试脚本
用于验证模型在服务器 CPU 环境下是否能正常工作
"""

import os
import sys
import traceback
from pathlib import Path

# 必须在所有 import 之前设置环境变量
os.environ['MLX_USE_CPU'] = '1'
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'

# 设置 HF_HOME（与 app.py 一致）
os.environ["HF_HOME"] = str(Path.home() / "hf_cache")

from PIL import Image
import mlx.core as mx
from mlx_vlm import load, generate

class ModelTester:
    """专业的模型测试类"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.test_results = []
        
    def log(self, message, status="INFO"):
        """记录测试日志"""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")
        
    def test_environment(self):
        """测试 1: 环境设置"""
        self.log("测试 1: 环境设置", "INFO")
        try:
            # 设置设备
            mx.set_default_device(mx.cpu)
            device = mx.default_device()
            self.log(f"设备设置成功: {device}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"环境设置失败: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def test_model_loading(self):
        """测试 2: 模型加载"""
        self.log("测试 2: 模型加载", "INFO")
        try:
            model_path = "mlx-community/DeepSeek-OCR-8bit"
            self.log(f"加载模型: {model_path}", "INFO")
            
            self.model, self.processor = load(model_path)
            
            if self.model is None or self.processor is None:
                self.log("模型或处理器为 None", "ERROR")
                return False
                
            self.log("模型加载成功", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"模型加载失败: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def test_image_creation(self):
        """测试 3: 图像创建"""
        self.log("测试 3: 图像创建", "INFO")
        try:
            # 创建测试图像（与 app.py 中处理流程一致）
            img = Image.new('RGB', (512, 512), color='white')
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            self.log(f"图像创建成功: {img.size}, mode: {img.mode}", "SUCCESS")
            return img
        except Exception as e:
            self.log(f"图像创建失败: {e}", "ERROR")
            traceback.print_exc()
            return None
    
    def test_generate_basic(self, img):
        """测试 4: 基本生成测试（与 app.py 完全一致）"""
        self.log("测试 4: 基本生成测试", "INFO")
        self.log("使用与 app.py 完全相同的参数调用 generate()", "INFO")
        
        try:
            prompt = "<image>\nExtract all text from the image."
            max_tokens = 512
            
            # 这是 app.py 第 472-479 行的完全相同的调用方式
            res = generate(
                model=self.model,
                processor=self.processor,
                image=img,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.0
            )
            
            # 检查结果
            if res is None:
                self.log("generate() 返回 None", "ERROR")
                return False
            
            # 处理结果（与 app.py 第 487-488 行一致）
            text = res.text if hasattr(res, 'text') else str(res)
            text = text.strip()
            
            if not text:
                self.log("生成结果为空", "WARNING")
                return False
            
            self.log(f"生成成功! 结果长度: {len(text)} 字符", "SUCCESS")
            self.log(f"结果预览: {text[:100]}...", "INFO")
            return True
            
        except AttributeError as e:
            if "'NoneType' object has no attribute 'token'" in str(e):
                self.log("检测到已知错误: last_response 为 None", "ERROR")
                self.log("这可能是 mlx-vlm 库在 CPU 模式下的 bug", "WARNING")
            self.log(f"AttributeError: {e}", "ERROR")
            traceback.print_exc()
            return False
        except Exception as e:
            self.log(f"生成失败: {type(e).__name__}: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def test_generate_different_tokens(self, img):
        """测试 5: 不同 max_tokens 值"""
        self.log("测试 5: 不同 max_tokens 值", "INFO")
        
        test_cases = [50, 100, 512]
        success_count = 0
        
        for max_tokens in test_cases:
            try:
                self.log(f"测试 max_tokens={max_tokens}", "INFO")
                res = generate(
                    model=self.model,
                    processor=self.processor,
                    image=img,
                    prompt="<image>\nText:",
                    max_tokens=max_tokens,
                    temperature=0.0
                )
                
                if res is not None:
                    self.log(f"max_tokens={max_tokens} 成功", "SUCCESS")
                    success_count += 1
                else:
                    self.log(f"max_tokens={max_tokens} 返回 None", "WARNING")
                    
            except Exception as e:
                self.log(f"max_tokens={max_tokens} 失败: {e}", "ERROR")
        
        self.log(f"成功: {success_count}/{len(test_cases)}", "INFO")
        return success_count > 0
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("🧪 MLX DeepSeek-OCR 专业测试套件")
        print("=" * 70)
        print()
        
        # 测试 1: 环境设置
        if not self.test_environment():
            return False
        print()
        
        # 测试 2: 模型加载
        if not self.test_model_loading():
            return False
        print()
        
        # 测试 3: 图像创建
        img = self.test_image_creation()
        if img is None:
            return False
        print()
        
        # 测试 4: 基本生成（最重要）
        if not self.test_generate_basic(img):
            print()
            print("=" * 70)
            print("❌ 基本生成测试失败 - 这是关键测试")
            print("=" * 70)
            return False
        print()
        
        # 测试 5: 不同参数
        self.test_generate_different_tokens(img)
        print()
        
        # 总结
        print("=" * 70)
        print("✅ 所有关键测试通过！模型可以正常工作")
        print("=" * 70)
        return True

def main():
    """主函数"""
    tester = ModelTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 未预期的错误: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()




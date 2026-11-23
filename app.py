#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MLX DeepSeek-OCR.
# Copyright (C) 2025 MLX DeepSeek-OCR contributors
# Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
# See the LICENSE file in the project root for full license text:
# https://www.gnu.org/licenses/agpl-3.0.en.html

import os
import gc
import re
import traceback
import atexit
import tempfile
import uuid
import fitz
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import threading
import io
import base64
import multiprocessing
import queue
import cv2
import numpy as np
import zipfile
import shutil

import mlx.core as mx
from mlx_vlm import load, generate

os.environ["HF_HOME"] = str(Path.home() / "hf_cache")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512MB limit for video uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

model_loaded_status = multiprocessing.Value('b', False)
pdf_tasks = {}
preprocess_tasks = {}
video_tasks = {}

UPLOAD_FOLDER = tempfile.gettempdir()
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# ==============================================================================
# 9 分類 × 5 Complexity 的前處理配置
# ==============================================================================

PREPROCESSING_CONFIG = {
    'Document': {
        'Academic': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Business': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Content': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Table': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Handwritten': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Complex': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        }
    },
    'Scene': {
        'Street': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Photo': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Objects': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 512},
            'Small': {'image_size': (640, 640), 'max_tokens': 1024},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 2048},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 4096},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 8192}
        },
        'Verification': {
            'Tiny': {'image_size': (512, 512), 'max_tokens': 256},
            'Small': {'image_size': (640, 640), 'max_tokens': 512},
            'Medium': {'image_size': (1024, 1024), 'max_tokens': 1024},
            'Large': {'image_size': (1280, 1280), 'max_tokens': 2048},
            'Gundam': {'image_size': (1024, 1024), 'max_tokens': 4096}
        }
    }
}

# 舊 5 mode 到新分類的快速映射
MODE_QUICK_MAP = {
    'basic': {'content_type': 'Document', 'subcategory': 'Academic', 'complexity': 'Medium'},
    'table': {'content_type': 'Document', 'subcategory': 'Table', 'complexity': 'Large'},
    'markdown': {'content_type': 'Document', 'subcategory': 'Content', 'complexity': 'Medium'},
    'formula': {'content_type': 'Document', 'subcategory': 'Academic', 'complexity': 'Large'},
    'product': {'content_type': 'Scene', 'subcategory': 'Photo', 'complexity': 'Small'}
}

prompts = {
    'product': '<image>\nExtract all printed text from this product packaging exactly as it appears. Use Traditional Chinese.',
    'basic': '<image>\nExtract all text from the image. Keep original Traditional Chinese and formatting.',
    'table': '<image>\nConvert this table to clean Markdown format.',
    'markdown': '<image>\nConvert this document page to clean Markdown format.',
    'formula': '<image>\nExtract all mathematical formulas using LaTeX format.'
}

# ==============================================================================
# 照片前處理功能
# ==============================================================================

def remove_background_pil(image):
    """使用 rembg 去除背景"""
    try:
        from rembg import remove
        result = remove(image)
        return result
    except ImportError:
        print("⚠️ rembg not available, using simple background removal")
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        rgba = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)
        rgba[:, :, :3] = img_array
        rgba[:, :, 3] = mask
        
        return Image.fromarray(rgba, 'RGBA')
    except Exception as e:
        print(f"❌ Background removal failed: {e}")
        return image

def auto_rotate_image(image):
    """自動旋轉圖像"""
    try:
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        if lines is not None:
            angles = []
            for rho, theta in lines[:20, 0]:
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                if abs(median_angle) > 1:
                    (h, w) = img_array.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(img_array, M, (w, h), flags=cv2.INTER_CUBIC, 
                                           borderMode=cv2.BORDER_REPLICATE)
                    return Image.fromarray(rotated)
    except Exception as e:
        print(f"⚠️ Auto-rotate failed: {e}")
    
    return image

def enhance_image(image):
    """圖像增強處理"""
    img_array = np.array(image)
    
    # 對比度增強
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    # 銳化
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    return Image.fromarray(sharpened)

def remove_shadows(image):
    """去除陰影"""
    img_array = np.array(image)
    rgb_planes = cv2.split(img_array)
    
    result_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        result_planes.append(diff_img)
    
    result = cv2.merge(result_planes)
    return Image.fromarray(result)

def binarize_image(image):
    """二值化處理"""
    img_array = np.array(image.convert('L'))
    _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary, 'L')

PREPROCESS_PRESETS = {
    'scan_optimize': {
        'auto_rotate': True,
        'enhance': True,
        'remove_shadows': True,
        'binarize': True,
        'remove_bg': False
    },
    'photo_optimize': {
        'auto_rotate': True,
        'enhance': True,
        'remove_shadows': True,
        'binarize': False,
        'remove_bg': False
    },
    'enhance_blurry': {
        'auto_rotate': False,
        'enhance': True,
        'remove_shadows': False,
        'binarize': False,
        'remove_bg': False
    },
    'remove_background_only': {
        'auto_rotate': False,
        'enhance': False,
        'remove_shadows': False,
        'binarize': False,
        'remove_bg': True
    }
}

def preprocess_single_image(image, settings):
    """單張圖片前處理"""
    processed = image.copy()
    intermediate_images = []
    
    try:
        if settings.get('auto_rotate', False):
            new_img = auto_rotate_image(processed)
            if new_img is not processed:
                intermediate_images.append(processed)
                processed = new_img
        
        if settings.get('enhance', False):
            new_img = enhance_image(processed)
            if new_img is not processed:
                intermediate_images.append(processed)
                processed = new_img
        
        if settings.get('remove_shadows', False):
            new_img = remove_shadows(processed)
            if new_img is not processed:
                intermediate_images.append(processed)
                processed = new_img
        
        if settings.get('binarize', False):
            new_img = binarize_image(processed)
            if new_img is not processed:
                intermediate_images.append(processed)
                processed = new_img
        
        if settings.get('remove_bg', False):
            new_img = remove_background_pil(processed)
            if new_img is not processed:
                intermediate_images.append(processed)
                processed = new_img
        
        # 成功處理，清理中間圖片
        for img in intermediate_images:
            if img is not None and img is not processed:
                try:
                    img.close()
                except:
                    pass
        
        return processed
    
    except Exception as e:
        # 發生錯誤時，清理所有中間圖片和處理結果
        print(f"⚠️ Image preprocessing failed: {e}")
        for img in intermediate_images:
            if img is not None:
                try:
                    img.close()
                except:
                    pass
        if processed is not None and processed is not image:
            try:
                processed.close()
            except:
                pass
        raise

# ==============================================================================
# 影片截圖功能
# ==============================================================================

def extract_frames_from_video(video_path, output_dir, method='fixed_count', interval=5, total_frames=1000, sensitivity=0.5):
    """從影片提取幀"""
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("無法開啟影片檔案")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_video_frames / fps if fps > 0 else 0
    
    print(f"📹 影片資訊: {total_video_frames} 幀, {fps:.2f} FPS, {duration:.2f} 秒")
    
    frames = []
    
    if method == 'fixed_interval':
        # 固定間隔（每秒N張）
        frame_interval = max(1, int(fps / interval))
        if frame_interval == 0:
            frame_interval = 1
        
        for frame_idx in range(0, total_video_frames, frame_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(output_dir, f"frame_{len(frames):06d}.jpg")
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                frames.append(frame_path)
            
            if len(frames) >= total_frames:
                break
    
    elif method == 'fixed_count':
        # 固定數量
        frame_interval = max(1, total_video_frames // total_frames)
        
        for frame_idx in range(0, total_video_frames, frame_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(output_dir, f"frame_{len(frames):06d}.jpg")
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                frames.append(frame_path)
            
            if len(frames) >= total_frames:
                break
    
    elif method == 'scene_change':
        # 場景變化檢測（簡化版）
        prev_frame = None
        # 將 sensitivity (0.1-1.0) 轉換為閾值：sensitivity越高，閾值越低，檢測更多變化
        # sensitivity=0.1(低) → threshold≈0.73, sensitivity=1.0(高) → threshold≈0.40
        # 閾值範圍：0.4~0.75（大幅提高範圍，增強鑑別度，每秒不超過5張）
        scene_change_threshold = (1.0 - sensitivity) * 0.35 + 0.4
        print(f"🎬 場景變化檢測：敏感度={sensitivity:.2f}, 閾值={scene_change_threshold:.3f}")
        
        for frame_idx in range(total_video_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            if prev_frame is not None:
                # 計算幀間差異
                diff = cv2.absdiff(prev_frame, frame)
                non_zero_count = np.count_nonzero(diff)
                total_pixels = diff.shape[0] * diff.shape[1] * diff.shape[2]
                change_ratio = non_zero_count / total_pixels
                
                if change_ratio > scene_change_threshold:
                    frame_path = os.path.join(output_dir, f"frame_{len(frames):06d}.jpg")
                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    frames.append(frame_path)
            
            prev_frame = frame.copy()
            
            if len(frames) >= total_frames:
                break
    
    cap.release()
    print(f"✅ 提取完成: {len(frames)} 張幀")
    return frames

# ==============================================================================
# 模型載入和 OCR 相關函數
# ==============================================================================

_model_instance = None
_processor_instance = None
_model_instance_lock = threading.Lock()

def _load_model_for_subprocess():
    global _model_instance, _processor_instance, _model_instance_lock
    with _model_instance_lock:
        if _model_instance is not None and _processor_instance is not None:
            return True
        try:
            print(f"[{os.getpid()}] 🚀 Loading MLX DeepSeek-OCR model in subprocess...")
            model_path = "mlx-community/DeepSeek-OCR-8bit"
            _model_instance, _processor_instance = load(model_path, revision="148305747fad0be1d6f417d3c7cb477216c63a90")
            print(f"[{os.getpid()}] ✅ Model loaded successfully in subprocess!")
            print(f"[{os.getpid()}] 🔊 Metal available: {mx.metal.is_available()}")
            return True
        except Exception as e:
            print(f"[{os.getpid()}] ❌ Error loading model in subprocess: {e}")
            traceback.print_exc()
            _model_instance = None
            _processor_instance = None
            return False

def _run_ocr_in_process(image_bytes, prompt, max_tokens, output_queue):
    if not _load_model_for_subprocess():
        output_queue.put({'error': 'Model load failed in subprocess'})
        return
    try:
        t_load_start = time.time()
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        t_load_end = time.time()
        print(f"[{os.getpid()}] 📸 Image loaded: {img.size}, mode: {img.mode}, time: {t_load_end - t_load_start:.2f}s")
        
        print(f"[{os.getpid()}] 🔍 Starting OCR in subprocess...")
        print(f"[{os.getpid()}] 🔍 Image object type: {type(img)}")
        print(f"[{os.getpid()}] 🔍 Image size: {img.size}, mode: {img.mode}")
        
        # 確保設備設置正確
        # 確保設備設置正確
        if mx.metal.is_available():
            # mx.set_default_device(mx.gpu) # Default is usually GPU on Apple Silicon
            print(f"[{os.getpid()}] 🔧 Metal available, using default device (GPU)")
        else:
            mx.set_default_device(mx.cpu)
            print(f"[{os.getpid()}] 🔧 Set default device to CPU")
        
        print(f"[{os.getpid()}] 🔍 Prompt: {prompt[:100]}...")
        print(f"[{os.getpid()}] 🔍 Max tokens: {max_tokens}")
        
        # 確保模型和處理器已正確初始化
        if _model_instance is None or _processor_instance is None:
            raise RuntimeError("Model or processor is None - model not properly loaded")
        
        t_ocr_start = time.time()
        
        # 修復 mlx-vlm 0.3.5 bug：stream_generate() 可能返回空生成器，導致 last_response 為 None
        # 解決方案：使用較小的 max_tokens 值，並添加重試機制
        
        max_retries = 3
        retry_tokens = [min(max_tokens, 2048), min(max_tokens, 512), 256]
        res = None
        
        for attempt in range(max_retries):
            try:
                current_max_tokens = retry_tokens[attempt]
                print(f"[{os.getpid()}] 🔍 嘗試 {attempt + 1}/{max_retries}: max_tokens={current_max_tokens}")
                
                res = generate(
                    model=_model_instance,
                    processor=_processor_instance,
                    image=img,
                    prompt=prompt,
                    max_tokens=current_max_tokens,
                    temperature=0.0,
                    use_cache=False
                )
                
                # 如果成功，跳出循環
                if res is not None:
                    break
                    
            except AttributeError as e:
                if "'NoneType' object has no attribute 'token'" in str(e):
                    print(f"[{os.getpid()}] ⚠️ 嘗試 {attempt + 1} 失敗: mlx-vlm bug (last_response=None)")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # 等待後重試（time 已在文件開頭導入）
                        continue
                    else:
                        raise RuntimeError("mlx-vlm generate() 失敗：stream_generate() 沒有產生響應。這可能是 CPU 模式下的已知問題。")
                else:
                    raise
            except Exception as e:
                print(f"[{os.getpid()}] ⚠️ 嘗試 {attempt + 1} 失敗: {type(e).__name__}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待後重試（time 已在文件開頭導入）
                    continue
                else:
                    raise
        
        t_ocr_end = time.time()
        
        # 檢查結果是否有效
        if res is None:
            raise RuntimeError("generate() 在所有重試後仍返回 None")
        
        text = res.text if hasattr(res, 'text') else str(res)
        text = re.sub(r'<\|grounding\|>|\[\[.*?\]\]', '', text).strip()
        
        print(f"[{os.getpid()}] ✅ OCR completed in {t_ocr_end - t_ocr_start:.2f}s, text length: {len(text)}")
        output_queue.put({'success': True, 'text': text, 'timing': {
            'load': t_load_end - t_load_start,
            'inference': t_ocr_end - t_ocr_start
        }})
    except Exception as e:
        traceback.print_exc()
        output_queue.put({'error': f'OCR processing failed in subprocess: {str(e)}'})
    finally:
        if 'img' in locals() and img is not None:
            img.close()
        gc.collect()

def generate_with_timeout_and_process(image, prompt, max_tokens=8192, timeout=160):
    t_serialize_start = time.time()
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    image_bytes = buffered.getvalue()
    t_serialize_end = time.time()
    
    print(f"📦 Image serialized: {len(image_bytes) / 1024:.1f}KB (JPEG), time: {t_serialize_end - t_serialize_start:.2f}s")
    
    output_queue = multiprocessing.Queue()
    t_process_start = time.time()
    
    process = multiprocessing.Process(
        target=_run_ocr_in_process,
        args=(image_bytes, prompt, max_tokens, output_queue)
    )
    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        print(f"[{os.getpid()}] ⏰ OCR processing timed out. Terminating subprocess {process.pid}.")
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
        raise TimeoutError("OCR processing timeout")

    if process.exitcode != 0:
        print(f"[{os.getpid()}] ❌ OCR subprocess exited with code {process.exitcode}")
        try:
            result = output_queue.get_nowait()
            if 'error' in result:
                raise RuntimeError(result['error'])
        except queue.Empty:
            pass
        raise RuntimeError(f"OCR subprocess exited unexpectedly (code {process.exitcode})")

    try:
        result = output_queue.get(timeout=1)
        t_process_end = time.time()
        
        if 'success' in result:
            timing = result.get('timing', {})
            print(f"⏱️ 總耗時: {t_process_end - t_process_start:.2f}s (序列化: {t_serialize_end - t_serialize_start:.2f}s, 推理: {timing.get('inference', 0):.2f}s)")
            return result['text']
        else:
            raise RuntimeError(result.get('error', 'Unknown OCR error in subprocess'))
    except queue.Empty:
        raise RuntimeError("OCR subprocess finished but no result in queue.")

# ==============================================================================
# 前處理函數
# ==============================================================================

def get_preprocessing_config(content_type, subcategory, complexity):
    """根據三維分類獲取前處理配置"""
    try:
        config = PREPROCESSING_CONFIG[content_type][subcategory][complexity]
        return config
    except KeyError:
        return None

def preprocess_image_by_config(image, image_size):
    """調整圖像到指定尺寸"""
    img_processed = image.copy()
    img_processed.thumbnail(image_size, Image.Resampling.LANCZOS)
    print(f"🖼️ Image preprocessed to {image_size}, actual size: {img_processed.size}")
    return img_processed

# ==============================================================================
# 路由和主應用程式邏輯
# ==============================================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def is_model_healthy():
    return model_loaded_status.value

def preload_model_main_process():
    print("🔧 Setting model preloaded status for main process...")
    try:
        if not mx.metal.is_available():
            print("WARNING: Metal is not available, MLX might not perform well.")
        
        model_loaded_status.value = True
        print("✅ Model preloaded status set successfully for main process.")
        return True
    except Exception as e:
        print(f"❌ Failed to set model preloaded status: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'model_loaded': model_loaded_status.value,
        'model_healthy': is_model_healthy()
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded_status.value,
        'model_healthy': is_model_healthy(),
        'active_tasks': len(pdf_tasks),
        'preprocess_tasks': len(preprocess_tasks),
        'video_tasks': len(video_tasks)
    })

# ==============================================================================
# 照片前處理 API
# ==============================================================================

@app.route('/api/preprocess/upload', methods=['POST'])
def preprocess_upload():
    """上傳照片進行前處理"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    task_id = str(uuid.uuid4())
    task_dir = Path(UPLOAD_FOLDER) / f"preprocess_{task_id}"
    raw_dir = task_dir / "raw"
    processed_dir = task_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = []
    
    for file in files:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            raw_path = raw_dir / filename
            file.save(raw_path)
            
            img = None
            try:
                # 生成縮圖預覽
                img = Image.open(raw_path)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                thumb_b64 = base64.b64encode(buffered.getvalue()).decode()
                
                image_files.append({
                    'filename': filename,
                    'raw_path': str(raw_path),
                    'thumb_b64': f"data:image/png;base64,{thumb_b64}",
                    'processed_path': None,
                    'status': 'pending'
                })
            except Exception as e:
                print(f"⚠️ Error generating thumbnail for {filename}: {e}")
                # 即使縮圖失敗，仍然加入列表
                image_files.append({
                    'filename': filename,
                    'raw_path': str(raw_path),
                    'thumb_b64': None,
                    'processed_path': None,
                    'status': 'pending'
                })
            finally:
                if img:
                    img.close()
    
    if not image_files:
        return jsonify({'error': 'No valid image files'}), 400
    
    preprocess_tasks[task_id] = {
        'task_dir': str(task_dir),
        'images': image_files,
        'settings': {},
        'created_at': datetime.now()
    }
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'images': image_files,
        'total_images': len(image_files)
    })

@app.route('/api/preprocess/process', methods=['POST'])
def preprocess_process():
    """執行照片前處理"""
    data = request.get_json()
    task_id = data.get('task_id')
    settings = data.get('settings', {})
    
    if task_id not in preprocess_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = preprocess_tasks[task_id]
    task['settings'] = settings
    
    processed_dir = Path(task['task_dir']) / "processed"
    
    results = []
    
    for img_info in task['images']:
        original_img = None
        processed_img = None
        thumb_img = None
        
        try:
            raw_path = img_info['raw_path']
            filename = img_info['filename']
            
            # 處理圖片
            original_img = Image.open(raw_path)
            processed_img = preprocess_single_image(original_img, settings)
            
            # 保存處理後的圖片
            output_path = processed_dir / filename
            if processed_img.mode == 'RGBA':
                output_path = output_path.with_suffix('.png')
                processed_img.save(output_path, 'PNG')
            else:
                processed_img.save(output_path, 'JPEG', quality=95)
            
            # 生成處理後的縮圖
            thumb_img = processed_img.copy()
            thumb_img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            buffered = io.BytesIO()
            thumb_img.save(buffered, format="PNG")
            processed_thumb_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            img_info.update({
                'processed_path': str(output_path),
                'processed_thumb_b64': f"data:image/png;base64,{processed_thumb_b64}",
                'status': 'completed'
            })
            
            results.append({
                'filename': filename,
                'status': 'completed',
                'processed_path': str(output_path),
                'processed_thumb_b64': f"data:image/png;base64,{processed_thumb_b64}"
            })
            
        except Exception as e:
            print(f"❌ Error processing {img_info['filename']}: {e}")
            traceback.print_exc()
            img_info['status'] = 'failed'
            results.append({
                'filename': img_info['filename'],
                'status': 'failed',
                'error': str(e)
            })
        
        finally:
            # 確保所有圖片都被關閉
            if original_img:
                try:
                    original_img.close()
                except:
                    pass
            if processed_img and processed_img is not original_img:
                try:
                    processed_img.close()
                except:
                    pass
            if thumb_img:
                try:
                    thumb_img.close()
                except:
                    pass
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/api/preprocess/download', methods=['POST'])
def preprocess_download():
    """下載處理後的照片"""
    data = request.get_json()
    task_id = data.get('task_id')
    
    if task_id not in preprocess_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = preprocess_tasks[task_id]
    processed_dir = Path(task['task_dir']) / "processed"
    
    # 創建 ZIP 檔案
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for img_info in task['images']:
            if img_info['status'] == 'completed' and img_info['processed_path']:
                file_path = Path(img_info['processed_path'])
                if file_path.exists():
                    zip_file.write(file_path, file_path.name)
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"processed_images_{task_id}.zip",
        mimetype='application/zip'
    )

@app.route('/api/preprocess/to-ocr', methods=['POST'])
def preprocess_to_ocr():
    """將處理後的照片發送到 OCR"""
    data = request.get_json()
    task_id = data.get('task_id')
    
    if task_id not in preprocess_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = preprocess_tasks[task_id]
    
    # 返回處理後圖片的資訊，前端可以將這些圖片發送到 OCR
    processed_images = []
    for img_info in task['images']:
        if img_info['status'] == 'completed' and img_info['processed_path']:
            processed_images.append({
                'filename': img_info['filename'],
                'processed_path': img_info['processed_path'],
                'thumb_b64': img_info['processed_thumb_b64']
            })
    
    return jsonify({
        'success': True,
        'processed_images': processed_images
    })

# ==============================================================================
# 影片截圖 API
# ==============================================================================

@app.route('/api/video/upload', methods=['POST'])
def video_upload():
    """上傳影片進行截圖"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_video_file(file.filename):
        return jsonify({'error': 'Invalid video format'}), 400
    
    task_id = str(uuid.uuid4())
    task_dir = Path(UPLOAD_FOLDER) / f"video_{task_id}"
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存影片
    video_filename = secure_filename(file.filename)
    video_path = task_dir / video_filename
    file.save(video_path)
    
    # 獲取影片資訊
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return jsonify({'error': 'Cannot open video file'}), 400
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    video_tasks[task_id] = {
        'task_dir': str(task_dir),
        'video_path': str(video_path),
        'video_info': {
            'filename': video_filename,
            'duration': duration,
            'fps': fps,
            'total_frames': total_frames,
            'resolution': f"{width}x{height}"
        },
        'frames': [],
        'settings': {},
        'created_at': datetime.now()
    }
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'video_info': video_tasks[task_id]['video_info']
    })

@app.route('/api/video/extract', methods=['POST'])
def video_extract():
    """從影片提取幀"""
    data = request.get_json()
    task_id = data.get('task_id')
    settings = data.get('settings', {})
    
    if task_id not in video_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = video_tasks[task_id]
    task['settings'] = settings
    
    frames_dir = Path(task['task_dir']) / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    method = settings.get('method', 'fixed_count')
    interval = settings.get('interval', 5)
    total_frames = settings.get('total_frames', 1000)
    sensitivity = settings.get('sensitivity', 0.5)
    output_format = settings.get('format', 'jpg')
    
    try:
        frames = extract_frames_from_video(
            task['video_path'],
            str(frames_dir),
            method=method,
            interval=interval,
            total_frames=total_frames,
            sensitivity=sensitivity
        )
        
        # 生成幀的縮圖預覽
        frame_previews = []
        for i, frame_path in enumerate(frames):
            img = None
            try:
                img = Image.open(frame_path)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                thumb_b64 = base64.b64encode(buffered.getvalue()).decode()
                
                frame_previews.append({
                    'index': i + 1,
                    'path': frame_path,
                    'thumb_b64': f"data:image/png;base64,{thumb_b64}",
                    'selected': True
                })
            except Exception as e:
                print(f"⚠️ Error generating thumbnail for frame {i}: {e}")
                frame_previews.append({
                    'index': i + 1,
                    'path': frame_path,
                    'thumb_b64': None,
                    'selected': True
                })
            finally:
                if img:
                    try:
                        img.close()
                    except:
                        pass
        
        task['frames'] = frame_previews
        
        return jsonify({
            'success': True,
            'total_frames': len(frames),
            'frames': frame_previews
        })
    
    except Exception as e:
        print(f"❌ Video extraction failed: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Frame extraction failed: {str(e)}'}), 500
    
@app.route('/api/video/download', methods=['POST'])
def video_download():
    """下載影片截圖"""
    data = request.get_json()
    task_id = data.get('task_id')
    selected_frames = data.get('selected_frames', [])
    
    if task_id not in video_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = video_tasks[task_id]
    
    # 創建 ZIP 檔案
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for frame_info in task['frames']:
            if frame_info['index'] in selected_frames or not selected_frames:
                frame_path = Path(frame_info['path'])
                if frame_path.exists():
                    zip_file.write(frame_path, frame_path.name)
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"video_frames_{task_id}.zip",
        mimetype='application/zip'
    )

# ==============================================================================
# OCR 路由 (保持不變)
# ==============================================================================

@app.route('/api/ocr', methods=['POST'])
def ocr():
    """單張圖片 OCR - 支援新的三維分類和舊的快速 mode"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Format not supported'}), 400
    
    # 判斷是用新分類還是舊 mode
    old_mode = request.form.get('mode')
    if old_mode and old_mode in MODE_QUICK_MAP:
        # 快速映射舊 mode
        mapping = MODE_QUICK_MAP[old_mode]
        content_type = mapping['content_type']
        subcategory = mapping['subcategory']
        complexity = mapping['complexity']
    else:
        # 使用新分類
        content_type = request.form.get('content_type', 'Document')
        subcategory = request.form.get('subcategory', 'Academic')
        complexity = request.form.get('complexity', 'Medium')
    
    # 獲取前處理配置
    config = get_preprocessing_config(content_type, subcategory, complexity)
    if not config:
        return jsonify({'error': f'Invalid configuration: {content_type}/{subcategory}/{complexity}'}), 400
    
    if not is_model_healthy():
        return jsonify({'error': 'Model not ready. Please check server status.'}), 500
    
    tmp_path = None
    img = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        if tmp_path.lower().endswith('.pdf'):
            return jsonify({'error': 'Use PDF batch API for PDF files'}), 400
        
        img = Image.open(tmp_path).convert('RGB')
        
        # 根據配置進行前處理
        img_processed = preprocess_image_by_config(img, config['image_size'])
        
        # 使用舊 mode 的 prompt（如果提供了）
        if old_mode and old_mode in prompts:
            prompt = prompts[old_mode]
        else:
            prompt = prompts['basic']
        
        print(f"📋 Processing with: content_type={content_type}, subcategory={subcategory}, complexity={complexity}")
        print(f"   Image size: {config['image_size']}, max_tokens: {config['max_tokens']}")
        
        text = generate_with_timeout_and_process(
            image=img_processed,
            prompt=prompt,
            max_tokens=config['max_tokens'],
            timeout=160
        )
        
        print(f"✅ OCR completed, text length: {len(text)}")
        return jsonify({
            'success': True,
            'text': text,
            'config': {
                'content_type': content_type,
                'subcategory': subcategory,
                'complexity': complexity,
                'image_size': config['image_size'],
                'max_tokens': config['max_tokens']
            }
        })
    
    except TimeoutError:
        return jsonify({'error': 'OCR processing timeout'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'OCR processing failed: {str(e)}'}), 500
    finally:
        if img:
            img.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        gc.collect()

# ==============================================================================
# PDF 處理 (保持不變)
# ==============================================================================

def cleanup_old_tasks():
    now = datetime.now()
    
    # 清理 PDF 任務
    expired = [tid for tid, t in pdf_tasks.items() if now - t['created_at'] > timedelta(minutes=30)]
    for tid in expired:
        pdf_file_path = pdf_tasks[tid].get('pdf_path')
        if pdf_file_path and os.path.exists(pdf_file_path):
            try:
                os.remove(pdf_file_path)
                print(f"🗑️ Removed expired PDF file: {pdf_file_path}")
            except Exception as e:
                print(f"❌ Error removing expired PDF file {pdf_file_path}: {e}")
        del pdf_tasks[tid]
    
    # 清理前處理任務
    expired = [tid for tid, t in preprocess_tasks.items() if now - t['created_at'] > timedelta(minutes=30)]
    for tid in expired:
        task_dir = preprocess_tasks[tid].get('task_dir')
        if task_dir and os.path.exists(task_dir):
            try:
                shutil.rmtree(task_dir)
                print(f"🗑️ Removed expired preprocess task: {task_dir}")
            except Exception as e:
                print(f"❌ Error removing preprocess task {task_dir}: {e}")
        del preprocess_tasks[tid]
    
    # 清理影片任務
    expired = [tid for tid, t in video_tasks.items() if now - t['created_at'] > timedelta(minutes=30)]
    for tid in expired:
        task_dir = video_tasks[tid].get('task_dir')
        if task_dir and os.path.exists(task_dir):
            try:
                shutil.rmtree(task_dir)
                print(f"🗑️ Removed expired video task: {task_dir}")
            except Exception as e:
                print(f"❌ Error removing video task {task_dir}: {e}")
        del video_tasks[tid]
    
    if expired:
        print(f"🧹 Cleaned up {len(expired)} expired tasks")

@app.route('/api/pdf/init', methods=['POST'])
def init_pdf_task():
    cleanup_old_tasks()
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
    
    # 判斷是用新分類還是舊 mode
    old_mode = request.form.get('mode')
    if old_mode and old_mode in MODE_QUICK_MAP:
        mapping = MODE_QUICK_MAP[old_mode]
        content_type = mapping['content_type']
        subcategory = mapping['subcategory']
        complexity = mapping['complexity']
    else:
        content_type = request.form.get('content_type', 'Document')
        subcategory = request.form.get('subcategory', 'Academic')
        complexity = request.form.get('complexity', 'Medium')
    
    pdf_save_path = None
    thumbnails = []
    
    try:
        task_id = str(uuid.uuid4())
        pdf_filename = secure_filename(file.filename)
        pdf_save_path = Path(UPLOAD_FOLDER) / f"{task_id}_{pdf_filename}"
        file.save(pdf_save_path)
        print(f"📄 Saved PDF for task {task_id} to: {pdf_save_path}")
        
        doc = fitz.open(pdf_save_path)
        total_pages = len(doc)
        print(f"📄 Processing PDF with {total_pages} pages for thumbnails")
        
        for page_num in range(total_pages):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
            img_thumb = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            img_thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)
            buffered = io.BytesIO()
            img_thumb.save(buffered, format="PNG")
            thumb_b64 = base64.b64encode(buffered.getvalue()).decode()
            thumbnails.append(f"data:image/png;base64,{thumb_b64}")
            img_thumb.close()
            del pix
            
            if page_num % 10 == 0:
                print(f"📊 Generated thumbnails for {page_num + 1}/{total_pages} pages")
        
        doc.close()
        
        pdf_tasks[task_id] = {
            'pdf_path': str(pdf_save_path),
            'thumbnails': thumbnails,
            'content_type': content_type,
            'subcategory': subcategory,
            'complexity': complexity,
            'created_at': datetime.now(),
            'total_pages': total_pages
        }
        
        print(f"✅ PDF task initialized: {task_id}, pages: {total_pages}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'total_pages': total_pages,
            'thumbnails': thumbnails
        })
    except Exception as e:
        traceback.print_exc()
        if pdf_save_path and os.path.exists(pdf_save_path):
            os.remove(pdf_save_path)
        return jsonify({'error': f'PDF initialization failed: {str(e)}'}), 500
    finally:
        gc.collect()

@app.route('/api/pdf/extract-pages', methods=['POST'])
def extract_pdf_pages():
    """提取PDF所有頁面為圖片文件，供前處理使用"""
    data = request.get_json()
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({'success': False, 'error': 'Task ID is required'}), 400
    
    if task_id not in pdf_tasks:
        return jsonify({'success': False, 'error': 'Task expired or not found'}), 404
    
    task = pdf_tasks[task_id]
    pdf_path = task.get('pdf_path')
    total_pages = task.get('total_pages')
    
    if not pdf_path:
        return jsonify({'success': False, 'error': 'PDF path not found in task'}), 400
    
    if not total_pages or total_pages <= 0:
        return jsonify({'success': False, 'error': 'Invalid total pages'}), 400
    
    # 檢查PDF文件是否存在
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return jsonify({'success': False, 'error': f'PDF file not found: {pdf_path}'}), 404
    
    # 創建臨時目錄保存提取的圖片
    extract_dir = Path(UPLOAD_FOLDER) / f"pdf_extract_{task_id}"
    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to create extract directory: {str(e)}'}), 500
    
    image_files = []
    doc = None
    
    try:
        doc = fitz.open(str(pdf_path))
        print(f"📄 Extracting {total_pages} pages from PDF for preprocessing...")
        
        upload_folder_path = Path(UPLOAD_FOLDER).resolve()
        
        for page_num in range(total_pages):
            try:
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # 保存為PNG文件
                filename = f"page_{page_num + 1}.png"
                file_path = extract_dir / filename
                img.save(file_path, 'PNG')
                
                # 生成縮圖
                thumb = img.copy()
                thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)
                buffered = io.BytesIO()
                thumb.save(buffered, format="PNG")
                thumb_b64 = base64.b64encode(buffered.getvalue()).decode()
                
                # 計算相對路徑用於API訪問
                try:
                    file_path_resolved = file_path.resolve()
                    relative_path = str(file_path_resolved.relative_to(upload_folder_path))
                except ValueError:
                    # 如果無法計算相對路徑，使用文件名
                    relative_path = f"pdf_extract_{task_id}/{filename}"
                
                image_files.append({
                    'filename': filename,
                    'file_path': str(file_path),
                    'file_url': f"/api/files/{relative_path}",
                    'thumb_b64': f"data:image/png;base64,{thumb_b64}",
                    'page_number': page_num + 1
                })
                
                img.close()
                thumb.close()
                del pix
                
                if (page_num + 1) % 10 == 0:
                    print(f"📊 Extracted {page_num + 1}/{total_pages} pages")
            except Exception as e:
                print(f"⚠️ Error extracting page {page_num + 1}: {e}")
                traceback.print_exc()
                # 繼續處理下一頁
                continue
        
        if doc:
            doc.close()
            doc = None
        
        # 保存提取的文件路徑到task中
        task['extracted_images'] = image_files
        task['extract_dir'] = str(extract_dir)
        
        if len(image_files) == 0:
            return jsonify({'success': False, 'error': 'No pages were extracted successfully'}), 500
        
        print(f"✅ Extracted {len(image_files)}/{total_pages} pages from PDF")
        
        return jsonify({
            'success': True,
            'images': image_files,
            'total_images': len(image_files)
        })
    except Exception as e:
        traceback.print_exc()
        error_msg = str(e)
        print(f"❌ Error in extract_pdf_pages: {error_msg}")
        return jsonify({'success': False, 'error': f'Failed to extract pages: {error_msg}'}), 500
    finally:
        if doc:
            try:
                doc.close()
            except:
                pass
        gc.collect()

@app.route('/api/files/<path:filepath>')
def serve_file(filepath):
    """提供文件访问服务"""
    try:
        # 解析文件路径，防止路径遍历攻击
        file_path = Path(UPLOAD_FOLDER) / filepath
        file_path = file_path.resolve()
        upload_folder_path = Path(UPLOAD_FOLDER).resolve()
        
        # 确保文件在UPLOAD_FOLDER目录下
        try:
            file_path.relative_to(upload_folder_path)
        except ValueError:
            return jsonify({'error': 'Access denied: File outside upload folder'}), 403
        
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/preview-page', methods=['POST'])
def preview_page():
    data = request.get_json()
    task_id = data.get('task_id')
    page_number = data.get('page_number', 1)
    
    if task_id not in pdf_tasks:
        return jsonify({'error': 'Task expired or not found'}), 404
    
    task = pdf_tasks[task_id]
    pdf_path = task['pdf_path']
    total_pages = task['total_pages']
    
    if page_number < 1 or page_number > total_pages:
        return jsonify({'error': 'Page out of range'}), 400
    
    img_b64 = None
    doc = None
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_number - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        img.close()
        del pix
        
        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{img_b64}"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate preview: {str(e)}'}), 500
    finally:
        if doc:
            doc.close()
        gc.collect()

@app.route('/api/pdf/process-batch', methods=['POST'])
def process_pdf_batch():
    data = request.get_json()
    task_id = data.get('task_id')
    batch_index = data.get('batch_index', 0)
    batch_size = data.get('batch_size', 2)
    processed_images = data.get('processed_images', {})  # ===== 修正：接收處理後的圖片路徑映射 =====
    
    if task_id not in pdf_tasks:
        return jsonify({'error': 'Task not found or expired'}), 404
    
    task = pdf_tasks[task_id]
    pdf_path = task['pdf_path']
    content_type = task['content_type']
    subcategory = task['subcategory']
    complexity = task['complexity']
    total_pages = task['total_pages']
    
    # 獲取前處理配置
    config = get_preprocessing_config(content_type, subcategory, complexity)
    if not config:
        return jsonify({'error': f'Invalid configuration: {content_type}/{subcategory}/{complexity}'}), 400
    
    # 使用預設 prompt
    prompt = prompts.get('basic', '<image>\nExtract all text from the image.')
    
    start_page_idx = batch_index * batch_size
    end_page_idx = min(start_page_idx + batch_size, total_pages)
    
    if not is_model_healthy():
        return jsonify({'error': 'Model not ready. Please check server status.'}), 500
    
    results = []
    doc = None
    
    try:
        # ===== 修正：如果有處理後的圖片，使用處理後的圖片；否則使用原始PDF =====
        use_processed_images = bool(processed_images)
        
        if use_processed_images:
            print(f"🔍 Processing batch {batch_index + 1} with PREPROCESSED images, pages {start_page_idx + 1}-{end_page_idx}")
            print(f"📋 Received processed_images keys: {list(processed_images.keys())}")
        else:
            doc = fitz.open(pdf_path)
            print(f"🔍 Processing batch {batch_index + 1}, pages {start_page_idx + 1}-{end_page_idx}")
        
        for i in range(start_page_idx, end_page_idx):
            page_num = i + 1
            pix = None  # 初始化 pix 變數
            
            if use_processed_images and str(page_num) in processed_images:
                # ===== 使用處理後的圖片 =====
                processed_path = processed_images[str(page_num)]
                print(f"📄 Loading PREPROCESSED page {page_num}/{total_pages} for OCR...")
                
                # 載入處理後的圖片（processed_path 是完整路徑）
                try:
                    file_path = Path(processed_path)
                    if not file_path.exists():
                        raise FileNotFoundError(f"Processed image not found: {processed_path}")
                    
                    img = Image.open(file_path).convert('RGB')
                    print(f"✅ Loaded preprocessed image for page {page_num}: {file_path}")
                except Exception as e:
                    print(f"⚠️ Failed to load preprocessed image for page {page_num}: {e}")
                    # 回退到原始PDF
                    if doc is None:
                        doc = fitz.open(pdf_path)
                    page = doc[page_num - 1]
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:
                # ===== 使用原始PDF =====
                if doc is None:
                    doc = fitz.open(pdf_path)
                print(f"📄 Loading page {page_num}/{total_pages} for OCR...")
                page = doc[page_num - 1]
                
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # 根據配置進行前處理（尺寸調整）
            img_processed = preprocess_image_by_config(img, config['image_size'])
            
            print(f"📄 Processing page {page_num} with: {content_type}/{subcategory}/{complexity}")
            text = generate_with_timeout_and_process(
                image=img_processed,
                prompt=prompt,
                max_tokens=config['max_tokens'],
                timeout=160
            )
            
            results.append({'page': page_num, 'text': text})
            
            # 清理資源
            img.close()
            if pix is not None:
                del pix
            del img
            gc.collect()

            print(f"✅ Page {page_num} completed, text length: {len(text)}")
        
        has_more = end_page_idx < total_pages
        next_batch = batch_index + 1 if has_more else None
        
        print(f"✅ Batch {batch_index + 1} completed, processed: {end_page_idx}/{total_pages}")
        
        return jsonify({
            'success': True,
            'results': results,
            'has_more': has_more,
            'next_batch_index': next_batch,
            'processed_pages': end_page_idx,
            'config': {
                'content_type': content_type,
                'subcategory': subcategory,
                'complexity': complexity,
                'image_size': config['image_size'],
                'max_tokens': config['max_tokens']
            }
        })
    except TimeoutError:
        return jsonify({'error': 'OCR processing timeout'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500
    finally:
        if doc:
            doc.close()
        gc.collect()

@app.route('/api/video/process-batch', methods=['POST'])
def process_video_batch():
    """處理視頻截圖批次OCR"""
    data = request.get_json()
    batch_index = data.get('batch_index', 0)
    batch_size = data.get('batch_size', 2)
    processed_images = data.get('processed_images', {})  # 處理後的圖片路徑映射
    content_type = data.get('content_type', 'Document')
    subcategory = data.get('subcategory', 'Academic')
    complexity = data.get('complexity', 'Medium')
    
    if not processed_images:
        return jsonify({'error': 'No processed images provided'}), 400
    
    # 獲取前處理配置
    config = get_preprocessing_config(content_type, subcategory, complexity)
    if not config:
        return jsonify({'error': f'Invalid configuration: {content_type}/{subcategory}/{complexity}'}), 400
    
    # 使用預設 prompt
    prompt = prompts.get('basic', '<image>\nExtract all text from the image.')
    
    # 獲取所有截圖編號並排序
    frame_numbers = sorted([int(k) for k in processed_images.keys()])
    total_frames = len(frame_numbers)
    
    start_idx = batch_index * batch_size
    end_idx = min(start_idx + batch_size, total_frames)
    
    if not is_model_healthy():
        return jsonify({'error': 'Model not ready. Please check server status.'}), 500
    
    results = []
    
    try:
        print(f"🔍 Processing video frames batch {batch_index + 1}, frames {start_idx + 1}-{end_idx}")
        
        for i in range(start_idx, end_idx):
            if i >= len(frame_numbers):
                break
                
            frame_num = frame_numbers[i]
            processed_path = processed_images[str(frame_num)]
            
            print(f"📄 Loading PREPROCESSED frame {frame_num}/{total_frames} for OCR...")
            
            # 載入處理後的圖片
            try:
                file_path = Path(processed_path)
                if not file_path.exists():
                    raise FileNotFoundError(f"Processed image not found: {processed_path}")
                
                img = Image.open(file_path).convert('RGB')
                print(f"✅ Loaded preprocessed image for frame {frame_num}: {file_path}")
            except Exception as e:
                print(f"⚠️ Failed to load preprocessed image for frame {frame_num}: {e}")
                results.append({'page': frame_num, 'text': '', 'error': str(e)})
                continue
            
            # 根據配置進行前處理（尺寸調整）
            img_processed = preprocess_image_by_config(img, config['image_size'])
            
            print(f"📄 Processing frame {frame_num} with: {content_type}/{subcategory}/{complexity}")
            text = generate_with_timeout_and_process(
                image=img_processed,
                prompt=prompt,
                max_tokens=config['max_tokens'],
                timeout=160
            )
            
            results.append({'page': frame_num, 'text': text})
            
            # 清理資源
            img.close()
            del img
            gc.collect()
            
            print(f"✅ Frame {frame_num} completed, text length: {len(text)}")
        
        has_more = end_idx < total_frames
        next_batch = batch_index + 1 if has_more else None
        
        print(f"✅ Video batch {batch_index + 1} completed, processed: {end_idx}/{total_frames}")
        
        return jsonify({
            'success': True,
            'results': results,
            'has_more': has_more,
            'next_batch_index': next_batch,
            'processed_pages': end_idx,
            'config': {
                'content_type': content_type,
                'subcategory': subcategory,
                'complexity': complexity,
                'image_size': config['image_size'],
                'max_tokens': config['max_tokens']
            }
        })
    except TimeoutError:
        return jsonify({'error': 'OCR processing timeout'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500
    finally:
        gc.collect()

@app.route('/api/pdf/cancel', methods=['POST'])
def cancel_pdf_task():
    data = request.get_json()
    task_id = data.get('task_id')
    if task_id in pdf_tasks:
        pdf_file_path = pdf_tasks[task_id].get('pdf_path')
        if pdf_file_path and os.path.exists(pdf_file_path):
            try:
                os.remove(pdf_file_path)
                print(f"🗑️ Removed PDF file for cancelled task: {pdf_file_path}")
            except Exception as e:
                print(f"❌ Error removing PDF file for cancelled task {pdf_file_path}: {e}")
        del pdf_tasks[task_id]
        gc.collect()
        print(f"❌ PDF task cancelled: {task_id}")
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found or expired'}), 404

def cleanup():
    print("🧹 Cleaning up resources on application exit...")
    model_loaded_status.value = False
    
    # 清理所有任務
    for task_dict in [pdf_tasks, preprocess_tasks, video_tasks]:
        for task_id in list(task_dict.keys()):
            task = task_dict[task_id]
            task_dir = task.get('task_dir')
            pdf_path = task.get('pdf_path')
            
            if task_dir and os.path.exists(task_dir):
                try:
                    shutil.rmtree(task_dir)
                    print(f"🗑️ Removed task directory: {task_dir}")
                except Exception as e:
                    print(f"❌ Error removing task directory {task_dir}: {e}")
            
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    print(f"🗑️ Removed PDF file: {pdf_path}")
                except Exception as e:
                    print(f"❌ Error removing PDF file {pdf_path}: {e}")
            
            del task_dict[task_id]
    
    gc.collect()
    print("✅ All resources cleaned up.")

atexit.register(cleanup)

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn', force=True)
    
    print("🚀 Starting Flask OCR Application with Enhanced Features...")
    if not preload_model_main_process():
        print("❌ CRITICAL: Model preload status setting failed. Cannot start application.")
        sys.exit(1)
    
    print("✅ Application starting on http://0.0.0.0:5001")
    print("\n📊 Enhanced Features:")
    print("   - 📄 OCR 辨識 (現有功能)")
    print("   - 🎨 照片前處理 (新功能)")
    print("   - 🎬 影片截圖 (新功能)")
    print("   - 📋 PDF 批次處理 (現有功能)")
    print("\n🔄 Legacy Mode Support:")
    print("   - 'basic' → Document/Academic/Medium")
    print("   - 'table' → Document/Table/Large")
    print("   - 'markdown' → Document/Content/Medium")
    print("   - 'formula' → Document/Academic/Large")
    print("   - 'product' → Scene/Photo/Small")
    print("\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
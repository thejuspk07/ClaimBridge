"""
GPU Verification and Single-Claim Benchmark for PaddleOCR.
"""
import os
import sys
import time
from pathlib import Path

# Add NVIDIA package bin directories to DLL search path if present
venv_site = Path(__file__).resolve().parent / ".venv311" / "Lib" / "site-packages"
nvidia_dir = venv_site / "nvidia"

if nvidia_dir.exists():
    for sub in nvidia_dir.iterdir():
        bin_path = sub / "bin"
        if bin_path.exists():
            try:
                os.add_dll_directory(str(bin_path))
                os.environ["PATH"] = str(bin_path) + os.pathsep + os.environ.get("PATH", "")
            except Exception as e:
                print(f"Warning adding dll dir {bin_path}: {e}")

print("Testing Paddle GPU imports...")
import paddle

print(f"Paddle Version: {paddle.__version__}")
print(f"CUDA Compiled: {paddle.is_compiled_with_cuda()}")
print(f"CUDA Device Count: {paddle.device.cuda.device_count()}")
print(f"Current Device: {paddle.device.get_device()}")

# Run tensor calculation on GPU to verify CUDA execution
try:
    x = paddle.to_tensor([1.0, 2.0, 3.0], place=paddle.CUDAPlace(0))
    y = x * 2.0
    print("GPU Tensor multiplication succeeded:", y.numpy())
except Exception as e:
    print("GPU Tensor multiplication failed:", e)

# Test PaddleOCR
from paddleocr import PaddleOCR

image_path = Path("data/dataset/images/claim_001.png")
if not image_path.exists():
    image_path = Path("data/raw/claim_001.png")

print(f"\nInitializing PaddleOCR with device='gpu:0'...")
t0 = time.time()
try:
    ocr = PaddleOCR(
        lang="en",
        device="gpu:0",
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    )
except TypeError:
    ocr = PaddleOCR(
        lang="en",
        use_gpu=True,
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    )

init_time = time.time() - t0
print(f"PaddleOCR initialized in {init_time:.2f}s")

print(f"Running OCR on {image_path}...")
t1 = time.time()
result = ocr.predict(str(image_path)) if hasattr(ocr, 'predict') else ocr.ocr(str(image_path))
ocr_time = time.time() - t1
print(f"OCR inference completed in {ocr_time:.2f}s")

# Print detected elements count
if isinstance(result, list) and len(result) > 0:
    first = result[0]
    if isinstance(first, dict) and "rec_texts" in first:
        texts = first["rec_texts"]
        print(f"Detected {len(texts)} text elements.")
        print(f"Sample detections: {texts[:5]}")
    elif isinstance(first, list):
        print(f"Detected {len(first)} text elements.")
        print(f"Sample detections: {[line[1][0] for line in first[:5]]}")

print("\nBENCHMARK SUCCESSFUL!")

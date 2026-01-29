import sys, os

try:
    import torch

    print("torch.__version__:", getattr(torch, "__version__", None))
    print("cuda_available:", torch.cuda.is_available())
    try:
        print("device_count:", torch.cuda.device_count())
        if torch.cuda.is_available():
            print("device_name(0):", torch.cuda.get_device_name(0))
    except Exception as e:
        print("cuda device info error:", e)
except Exception as e:
    print("torch import error:", e)

try:
    import onnxruntime as ort

    print("onnxruntime providers:", ort.get_available_providers())
except Exception as e:
    print("onnxruntime import error:", e)

print("CUDA_VISIBLE_DEVICES=", os.environ.get("CUDA_VISIBLE_DEVICES"))
print("NVIDIA_VISIBLE_DEVICES=", os.environ.get("NVIDIA_VISIBLE_DEVICES"))
print("FORCE_CPU=", os.environ.get("FORCE_CPU"))
print("PATH=", os.environ.get("PATH")[:200])
sys.exit(0)

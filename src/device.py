import os

try:
    import torch
except Exception:
    torch = None

# Allow forcing CPU via environment variable for debugging
FORCE_CPU = os.getenv("FORCE_CPU", "").lower() in ("1", "true", "yes")

if FORCE_CPU:
    DEVICE = "cpu"
else:
    if (
        torch is not None
        and getattr(torch, "cuda", None) is not None
        and torch.cuda.is_available()
    ):
        DEVICE = "cuda"
    else:
        DEVICE = "cpu"


def is_cuda():
    return DEVICE == "cuda"


def name():
    return DEVICE

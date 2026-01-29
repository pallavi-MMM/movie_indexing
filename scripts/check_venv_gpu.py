import importlib.util as iu

def found(m):
    return iu.find_spec(m) is not None

mods = ['torch','torchvision','onnx','onnxruntime','ultralytics','open_clip','open_clip_torch','faster_whisper','insightface','faiss','scenedetect']
for m in mods:
    print(m, 'FOUND' if found(m) else 'MISSING')

# torch details
try:
    import torch
    print('torch_version', torch.__version__, 'cuda_available', torch.cuda.is_available())
    if torch.cuda.is_available():
        try:
            print('cuda_device_count', torch.cuda.device_count(), 'device_name', torch.cuda.get_device_name(0))
        except Exception as e:
            print('cuda_info_error', e)
except Exception as e:
    print('torch_error', e)

# onnxruntime details
try:
    import onnxruntime as ort
    print('onnxruntime_version', ort.__version__)
    try:
        print('onnxruntime_providers', ort.get_available_providers())
    except Exception as e:
        print('onnxruntime_providers_error', e)
except Exception as e:
    print('onnxruntime_error', e)

# ultralytics version
try:
    import ultralytics
    print('ultralytics_version', ultralytics.__version__)
except Exception as e:
    print('ultralytics_error', e)

# faster_whisper
try:
    import faster_whisper
    print('faster_whisper_version', faster_whisper.__version__)
except Exception as e:
    print('faster_whisper_error', e)

# insightface
try:
    import insightface
    print('insightface_version', insightface.__version__)
except Exception as e:
    print('insightface_error', e)

# faiss
try:
    import faiss
    print('faiss_version', getattr(faiss, '__version__', 'unknown'))
except Exception as e:
    print('faiss_error', e)

# scenedetect
try:
    import scenedetect
    print('scenedetect_version', scenedetect.__version__)
except Exception as e:
    print('scenedetect_error', e)

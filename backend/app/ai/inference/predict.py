import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.ai.model.model import EfficientNetB3Wrapper
from app.ai.data.transforms import infer_transforms
from albumentations.pytorch import ToTensorV2
from PIL import Image
import io
from app.ai.inference.gradcam import GradCAM


# Singleton holder for model to avoid reloading in process
_model_singleton: Optional[EfficientNetB3Wrapper] = None
_label_map = None
_device: str = "cpu"


def _load_label_map():
    global _label_map
    if _label_map is not None:
        return _label_map
    # Try to load labels file shipped with ai package
    labels_path = Path(__file__).parent.parent / "model" / "labels.json"
    if labels_path.exists():
        import json

        with open(labels_path, "r") as fh:
            _label_map = json.load(fh)
    else:
        # default fallback (must be adapted for your dataset)
        _label_map = ["normal", "abnormal"]
    return _label_map


def _get_model():
    global _model_singleton, _device
    if _model_singleton is not None:
        return _model_singleton
    # load settings for model
    num_classes = len(_load_label_map())
    weights = getattr(settings, "MODEL_WEIGHTS_PATH", None)
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    _model_singleton = EfficientNetB3Wrapper.build(num_classes=num_classes, weights_path=weights, device=_device)
    _model_singleton.eval()
    return _model_singleton


def _prepare_image(path: str):
    # load image bytes and apply transforms
    img = Image.open(path).convert("RGB")
    img_np = np.array(img)
    tf = infer_transforms()
    img_t = tf(image=img_np)["image"].unsqueeze(0)  # 1,C,H,W
    return img_t


def predict_from_path(path: str, with_gradcam: bool = True) -> Dict[str, Any]:
    """
    Load the model (singleton), prepare the image, run inference and optionally produce Grad-CAM overlay bytes.
    Returns: { predicted_class: str, probabilities: {label: float}, gradcam_bytes: bytes (PNG) or None }
    """
    model = _get_model()
    device = _device
    input_tensor = _prepare_image(path).to(device)
    with torch.no_grad():
        logits = model(input_tensor)
        probs = torch.nn.functional.softmax(logits, dim=1)[0].cpu().numpy()
    labels = _load_label_map()
    probabilities = {labels[i]: float(probs[i]) for i in range(len(labels))}
    top_idx = int(probs.argmax())
    predicted = labels[top_idx]

    gradcam_bytes = None
    if with_gradcam:
        try:
            cam = GradCAM(model.model, target_layer_name=None)
            overlay = cam.generate_cam(input_tensor, target_class=top_idx)
            # overlay is a numpy HxWx3 uint8 image RGB — convert to PNG bytes
            from PIL import Image

            im = Image.fromarray(overlay)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            gradcam_bytes = buf.getvalue()
        except Exception:
            gradcam_bytes = None

    return {
        "predicted_class": predicted,
        "probabilities": probabilities,
        "gradcam_bytes": gradcam_bytes,
    }

import os
import numpy as np
import cv2
import torch
from typing import Dict, Any
from .model import ModelWrapper
from .gradcam import minimal_gradcam_stub, save_heatmap_on_image

# Map indices to class names
CLASS_MAP = {0: "Normal", 1: "CIN1", 2: "CIN2", 3: "CIN3", 4: "Cervical Cancer"}

class PredictService:
    def __init__(self, model_path: str):
        self.model_wrapper = ModelWrapper(model_path=model_path)
        self.model = self.model_wrapper.model
        self.device = self.model_wrapper.device
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def preprocess(self, image_path: str):
        # Read image (BGR)
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Unable to read image")
        # Resize to 300x300 (EfficientNet-B3 common input 300)
        img = cv2.resize(img, (300, 300))
        # Denoise
        img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        # Contrast enhancement (CLAHE on L channel)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        # Normalize to 0..1 and channel order RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        # Standard normalization values (ImageNet)
        mean = np.array([0.485, 0.456, 0.406])
        std  = np.array([0.229, 0.224, 0.225])
        img = (img - mean) / std
        # HWC -> CHW
        tensor = torch.from_numpy(np.transpose(img, (2,0,1))).unsqueeze(0).to(self.device).float()
        return tensor

    def predict(self, image_path: str) -> Dict[str, Any]:
        tensor = self.preprocess(image_path)
        logits = self.model_wrapper.predict_tensor(tensor)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        idx = int(probs.argmax())
        prediction = CLASS_MAP.get(idx, "Unknown")
        confidence = float(probs[idx])
        probabilities = {CLASS_MAP[i]: float(probs[i]) for i in range(len(probs))}

        # Grad-CAM (placeholder)
        heatmap = minimal_gradcam_stub(self.model, tensor, target_class=idx)
        gradcam_fname = f"gradcam_{os.path.basename(image_path)}"
        gradcam_path = os.path.join(self.upload_dir, gradcam_fname)
        save_heatmap_on_image(image_path, heatmap, gradcam_path)

        return {
            "prediction": prediction,
            "confidence": confidence,
            "probabilities": probabilities,
            "gradcam_path": gradcam_path
        }

"""
Model loader and helper for the EfficientNet-B3 classifier.
This file encapsulates model loading and warmup.

Notes:
- For production, save the full checkpoint and include model config.
- Training/validation code is separate (training scripts).
"""
import os
import torch
import timm
from typing import Any

class ModelWrapper:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()

    def _load_model(self) -> torch.nn.Module:
        # Create efficientnet_b3 backbone with correct number of classes (5)
        model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=5)
        if os.path.exists(self.model_path):
            state = torch.load(self.model_path, map_location=self.device)
            try:
                model.load_state_dict(state)
            except Exception:
                # If state contains optimizer or nested keys, adapt as needed
                model.load_state_dict(state.get("model", state))
        model.to(self.device)
        model.eval()
        return model

    def predict_tensor(self, tensor: torch.Tensor) -> Any:
        """
        tensor: shape (B, C, H, W) and already on self.device
        Returns raw logits
        """
        with torch.no_grad():
            logits = self.model(tensor)
        return logits

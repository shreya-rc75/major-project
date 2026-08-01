import torch
import torch.nn as nn
import timm
from typing import Optional, List, Dict
from pathlib import Path


class EfficientNetB3Wrapper(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = False):
        super().__init__()
        # use timm to build EfficientNet-B3
        self.model = timm.create_model("tf_efficientnet_b3_ns", pretrained=pretrained, num_classes=num_classes)
        self.num_classes = num_classes

    @classmethod
    def build(cls, num_classes: int, weights_path: Optional[str] = None, device: str = "cpu") -> "EfficientNetB3Wrapper":
        model = cls(num_classes=num_classes, pretrained=False)
        if weights_path:
            p = Path(weights_path)
            if not p.exists():
                raise FileNotFoundError(f"Model weights not found at {weights_path}")
            state = torch.load(str(p), map_location=device)
            # handle checkpoints that store state_dict under 'model' or similar
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            model.load_state_dict(state)
        return model.to(device)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def predict_batch(self, x: torch.Tensor, device: Optional[str] = None) -> torch.Tensor:
        if device:
            x = x.to(device)
        self.eval()
        with torch.no_grad():
            out = self.forward(x)
            probs = nn.functional.softmax(out, dim=1)
        return probs

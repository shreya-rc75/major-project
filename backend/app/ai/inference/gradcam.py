from typing import Optional
import torch
import numpy as np
from torch import nn


class GradCAM:
    """
    Minimal, robust Grad-CAM implementation that works with many PyTorch models.
    It finds the last convolutional layer if target_layer_name is None.
    """

    def __init__(self, model: nn.Module, target_layer_name: Optional[str] = None):
        self.model = model
        self.model.eval()
        self.gradients = None
        self.activations = None
        self.target_layer = None
        self.target_layer_name = target_layer_name
        self._find_target_layer()

    def _find_target_layer(self):
        if self.target_layer_name:
            # lookup by name
            for name, module in self.model.named_modules():
                if name == self.target_layer_name:
                    self.target_layer = module
                    break
        else:
            # heuristic: choose the last Conv2d layer
            last_conv = None
            for module in self.model.modules():
                if isinstance(module, torch.nn.Conv2d):
                    last_conv = module
            if last_conv is None:
                raise RuntimeError("No Conv2d layer found in model for Grad-CAM")
            self.target_layer = last_conv

        if self.target_layer is None:
            raise RuntimeError("Could not find target layer for Grad-CAM")

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            # grad_output is a tuple
            self.gradients = grad_output[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_backward_hook(backward_hook)

    def generate_cam(self, input_tensor: torch.Tensor, target_class: int = 0) -> np.ndarray:
        """
        input_tensor: 1,C,H,W on the appropriate device
        Returns: overlayed RGB numpy image uint8
        """
        device = input_tensor.device
        self.gradients = None
        self.activations = None
        self._register_hooks()
        # forward
        output = self.model(input_tensor)
        if isinstance(output, tuple):
            logits = output[0]
        else:
            logits = output
        # select target
        score = logits[:, target_class]
        self.model.zero_grad()
        score.backward(retain_graph=True)
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or activations were not captured by hooks")
        # compute weights
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])  # C
        activations = self.activations[0]  # C,H,W
        for i in range(activations.shape[0]):
            activations[i, :, :] *= pooled_gradients[i]
        heatmap = torch.sum(activations, dim=0).cpu()
        heatmap = np.maximum(heatmap.numpy(), 0)
        heatmap = heatmap / (heatmap.max() + 1e-8)
        # resize heatmap to input size
        import cv2

        heatmap = cv2.resize(heatmap, (input_tensor.shape[3], input_tensor.shape[2]))
        heatmap = np.uint8(255 * heatmap)
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        # get original image from tensor
        img = input_tensor[0].cpu().numpy()
        # img is C,H,W normalized; convert back to H,W,C uint8
        img = np.transpose(img, (1, 2, 0))
        # unnormalize using ImageNet stats
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img = std * img + mean
        img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        overlay = cv2.addWeighted(img, 0.6, heatmap_color, 0.4, 0)
        return overlay

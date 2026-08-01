"""
A placeholder minimal Grad-CAM utility. For production, use a robust implementation:
- capture activations and gradients of a target layer
- compute weights and generate heatmap
- overlay heatmap over original image

This file provides a stub and convenience save function.
"""
import numpy as np
import cv2
import torch
import os

def save_heatmap_on_image(orig_img_path: str, heatmap: np.ndarray, out_path: str):
    """
    heatmap: normalized 0..1, same HxW as orig_img
    """
    img = cv2.imread(orig_img_path)
    heat = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img, 0.6, heat, 0.4, 0)
    cv2.imwrite(out_path, overlay)

def minimal_gradcam_stub(model, input_tensor: torch.Tensor, target_class: int):
    """
    Very minimal stub: returns a uniform heatmap.
    Replace with proper Grad-CAM.
    """
    _, _, H, W = input_tensor.shape
    heatmap = np.ones((H, W), dtype=np.float32) * 0.5
    return heatmap

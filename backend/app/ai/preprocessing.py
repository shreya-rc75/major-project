"""Image preprocessing helpers for the cervical screening pipeline.

The original image is kept intact for display on the frontend. A copy is resized and
normalized for inference so the true image content remains available for 2.5D
rendering, masks, and overlays.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MAX_IMAGE_BYTES = 25 * 1024 * 1024


def validate_image_upload(filename: str, file_size: int, allowed_exts: set[str] | None = None) -> None:
    """Validate uploaded image metadata before model inference."""
    allowed = allowed_exts or ALLOWED_IMAGE_EXTENSIONS
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in allowed:
        raise ValueError(
            f"Unsupported image type '{ext}'. Supported types: {', '.join(sorted(allowed))}"
        )
    if file_size <= 0:
        raise ValueError("Uploaded file is empty.")
    if file_size > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Uploaded file exceeds the maximum supported size ({MAX_IMAGE_BYTES / (1024 * 1024):.0f} MB)."
        )


def read_image_for_inference(image_path: str, target_size: Tuple[int, int] = (300, 300)) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Return original image and normalized model tensor for inference."""
    original = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if original is None:
        raise ValueError(f"Could not read image from path: {image_path}")

    h, w = original.shape[:2]
    model_img = cv2.resize(original, target_size, interpolation=cv2.INTER_LINEAR)

    model_img = cv2.fastNlMeansDenoisingColored(model_img, None, 10, 10, 7, 21)
    lab = cv2.cvtColor(model_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    model_img = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

    rgb = cv2.cvtColor(model_img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    rgb = (rgb - mean) / std
    tensor = np.transpose(rgb, (2, 0, 1))[None, ...]

    metadata = {
        "shape": (h, w),
        "target_size": target_size,
        "channels": 3,
    }
    return original, tensor, metadata


def heatmap_to_mask(heatmap: np.ndarray, threshold: float = 0.55) -> np.ndarray:
    """Convert a 2D heatmap to a binary abnormality mask."""
    heat = np.asarray(heatmap, dtype=np.float32)
    if heat.ndim != 2:
        raise ValueError("Heatmap must be 2D before mask generation.")
    heat = (heat - np.min(heat)) / max(np.ptp(heat), 1e-8)
    return (heat >= threshold).astype(np.uint8)


def mask_to_bounding_boxes(mask: np.ndarray, min_area: int = 16) -> List[Dict[str, float]]:
    """Create bounding boxes from a binary mask with a contour-based approach."""
    if mask.ndim != 2:
        return []
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: List[Dict[str, float]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append({
            "x": float(x),
            "y": float(y),
            "width": float(w),
            "height": float(h),
            "area": float(area),
        })
    return boxes


def save_mask_overlay(mask: np.ndarray, out_path: str, original_image: np.ndarray | None = None) -> None:
    """Save a binary mask to disk; optionally overlay it on the original image."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if original_image is not None:
        original = np.asarray(original_image)
        if original.ndim == 3:
            mask_rgb = np.zeros_like(original, dtype=np.uint8)
            mask_rgb[:, :, 0] = 255
            mask_rgb[:, :, 2] = 0
            overlay = cv2.addWeighted(original, 0.7, mask_rgb, 0.3, 0)
            cv2.imwrite(out_path, overlay)
            return
    cv2.imwrite(out_path, (mask * 255).astype(np.uint8))


def save_heatmap_json(heatmap: np.ndarray, out_path: str) -> None:
    """Persist a normalized heatmap to JSON for browser rendering."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    heat = np.asarray(heatmap, dtype=np.float32)
    if heat.ndim != 2:
        raise ValueError("Heatmap must be 2D to save JSON metadata.")
    heat = (heat - np.min(heat)) / max(np.ptp(heat), 1e-8)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "shape": [int(heat.shape[0]), int(heat.shape[1])],
            "values": heat.astype(float).ravel().tolist(),
        }, f)


def save_heatmap_png(heatmap: np.ndarray, out_path: str) -> None:
    """Save a colorized heatmap as a PNG for frontend display."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    heat = np.asarray(heatmap, dtype=np.float32)
    if heat.ndim != 2:
        raise ValueError("Heatmap must be 2D before PNG export.")
    heat = (heat - np.min(heat)) / max(np.ptp(heat), 1e-8)
    heat_u8 = np.uint8(255 * heat)
    heat_color = cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET)
    cv2.imwrite(out_path, heat_color)


def create_analysis_response(prediction: str, confidence: float, probabilities: Dict[str, float], heatmap_path: str, mask_path: str, bounding_boxes: List[Dict[str, float]], analysis_id: str) -> Dict[str, Any]:
    """Create a standardized response payload for image analysis results."""
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "stage": prediction,
        "confidence": float(confidence),
        "probabilities": probabilities,
        "heatmap_path": heatmap_path,
        "mask_path": mask_path,
        "bounding_boxes": bounding_boxes,
        "needs_expert_review": confidence < 0.6,
        "disclaimer": "For research/educational use only. Not a medical diagnosis. Consult a qualified clinician.",
    }

import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from skimage import measure
from skimage.feature import greycomatrix, greycoprops
from typing import Tuple, Dict, Any, List


def _to_rgb_bytes(img_np: np.ndarray) -> bytes:
    # img_np expected RGB uint8 HWC
    im = Image.fromarray(img_np)
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _to_png_bytes(img_np: np.ndarray) -> bytes:
    im = Image.fromarray(img_np)
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _clahe_bgr(img_bgr: np.ndarray) -> np.ndarray:
    # Convert to LAB and apply CLAHE on L channel
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    res = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return res


def _denoise(img_bgr: np.ndarray) -> np.ndarray:
    # Fast Non-local means for color images
    return cv2.fastNlMeansDenoisingColored(img_bgr, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)


def _color_normalize_reinhard(img_bgr: np.ndarray, ref_mean: Tuple[float, float, float] = None, ref_std: Tuple[float, float, float] = None) -> np.ndarray:
    # Convert to LAB and match mean/std to reference if provided; otherwise perform per-channel scaling to 0-255
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    l, a, b = cv2.split(lab)
    if ref_mean is None or ref_std is None:
        # simple per-channel scaling using percentile stretch
        result = np.empty_like(img_bgr)
        for ch in range(3):
            p2, p98 = np.percentile(img_bgr[:, :, ch], (2, 98))
            result[:, :, ch] = np.clip((img_bgr[:, :, ch] - p2) * 255.0 / (p98 - p2 + 1e-8), 0, 255)
        return result.astype(np.uint8)
    else:
        # match LAB channel means/stds
        means = [l.mean(), a.mean(), b.mean()]
        stds = [l.std(), a.std(), b.std()]
        target_means = ref_mean
        target_stds = ref_std
        l = (l - means[0]) * (target_stds[0] / (stds[0] + 1e-8)) + target_means[0]
        a = (a - means[1]) * (target_stds[1] / (stds[1] + 1e-8)) + target_means[1]
        b = (b - means[2]) * (target_stds[2] / (stds[2] + 1e-8)) + target_means[2]
        lab = cv2.merge([l, a, b]).astype(np.uint8)
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _contrast_enhance(img_bgr: np.ndarray) -> np.ndarray:
    # Histogram equalization on Y channel in YCrCb
    ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    y_eq = cv2.equalizeHist(y)
    merged = cv2.merge([y_eq, cr, cb])
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)


def _remove_noise_median(img_bgr: np.ndarray, ksize: int = 3) -> np.ndarray:
    return cv2.medianBlur(img_bgr, ksize)


def _segment_cells(img_gray: np.ndarray) -> np.ndarray:
    # Use adaptive threshold + morphology to segment cells
    # img_gray expected uint8
    blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 5)
    # remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=2)
    # close holes
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)
    return closed


def _detect_cell_contours(seg_mask: np.ndarray, min_area: int = 200, max_area: int = 20000) -> List[Dict[str, Any]]:
    contours, _ = cv2.findContours(seg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        M = cv2.moments(cnt)
        cx = int(M["m10"] / (M["m00"] + 1e-8)) if M.get("m00", 0) != 0 else x + w // 2
        cy = int(M["m01"] / (M.get("m00", 0) + 1e-8)) if M.get("m00", 0) != 0 else y + h // 2
        results.append({"bbox": [int(x), int(y), int(w), int(h)], "area": float(area), "centroid": [cx, cy]})
    return results


def _detect_nuclei(img_gray: np.ndarray, cell_bbox: Tuple[int, int, int, int]) -> List[Dict[str, Any]]:
    x, y, w, h = cell_bbox
    roi = img_gray[y : y + h, x : x + w]
    if roi.size == 0:
        return []
    # enhance contrast locally
    roi_eq = cv2.equalizeHist(roi)
    # Otsu threshold to isolate nucleus candidates
    _, th = cv2.threshold(roi_eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # morphological opening to remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    nuclei = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 20 or area > (w * h) * 0.9:
            continue
        rx, ry, rw, rh = cv2.boundingRect(cnt)
        nuclei.append({"bbox": [int(x + rx), int(y + ry), int(rw), int(rh)], "area": float(area)})
    return nuclei


def _extract_features(img_gray: np.ndarray, cell_info: Dict[str, Any]) -> Dict[str, Any]:
    x, y, w, h = cell_info["bbox"]
    roi = img_gray[y : y + h, x : x + w]
    # basic intensity stats
    mean_int = float(np.mean(roi))
    std_int = float(np.std(roi))
    # morphological features via regionprops (approx)
    mask = (roi > 0).astype(np.uint8)
    props = {"area": float(np.sum(mask)), "perimeter": 0.0}
    try:
        regions = measure.regionprops(mask)
        if regions:
            r = regions[0]
            props["perimeter"] = float(r.perimeter)
            props["eccentricity"] = float(r.eccentricity)
            props["solidity"] = float(r.solidity)
        else:
            props["perimeter"] = 0.0
            props["eccentricity"] = 0.0
            props["solidity"] = 0.0
    except Exception:
        props["perimeter"] = 0.0
        props["eccentricity"] = 0.0
        props["solidity"] = 0.0
    # texture features via GLCM
    glcm_features = {}
    try:
        # reduce roi to 8-bit gray levels 0-255 -> 0-7
        levels = 8
        roi_small = (roi / 32).astype(np.uint8)
        glcm = greycomatrix(roi_small, distances=[1], angles=[0], levels=levels, symmetric=True, normed=True)
        contrast = greycoprops(glcm, 'contrast')[0, 0]
        dissimilarity = greycoprops(glcm, 'dissimilarity')[0, 0]
        homogeneity = greycoprops(glcm, 'homogeneity')[0, 0]
        energy = greycoprops(glcm, 'energy')[0, 0]
        correlation = greycoprops(glcm, 'correlation')[0, 0]
        glcm_features = {
            "contrast": float(contrast),
            "dissimilarity": float(dissimilarity),
            "homogeneity": float(homogeneity),
            "energy": float(energy),
            "correlation": float(correlation),
        }
    except Exception:
        glcm_features = {"contrast": 0.0, "dissimilarity": 0.0, "homogeneity": 0.0, "energy": 0.0, "correlation": 0.0}

    features = {"mean_intensity": mean_int, "std_intensity": std_int}
    features.update(props)
    features.update(glcm_features)
    return features


def preprocess_image_bytes(
    image_bytes: bytes,
    target_size: Tuple[int, int] = (300, 300),
    do_clahe: bool = True,
    do_denoise: bool = True,
    do_contrast: bool = True,
    do_color_norm: bool = False,
    segmentation_min_area: int = 200,
) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for a pap-smear image.
    Returns a dict with:
      - processed_image_bytes: resized, normalized RGB jpeg bytes
      - segmentation_mask_bytes: PNG bytes of binary segmentation mask
      - cell_bboxes: list of detected cell bounding boxes and areas
      - nucleus_bboxes: list of detected nuclei across all cells
      - per_cell_features: list of dicts with extracted features
      - global_features: dict of overall image features
    """
    # read bytes to cv2 image
    arr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Could not decode image bytes")

    # Resize while preserving aspect by padding
    h, w = img_bgr.shape[:2]
    target_h, target_w = target_size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # pad to target
    top = (target_h - new_h) // 2
    bottom = target_h - new_h - top
    left = (target_w - new_w) // 2
    right = target_w - new_w - left
    resized = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    proc = resized.copy()

    # Denoise
    if do_denoise:
        proc = _denoise(proc)

    # CLAHE
    if do_clahe:
        proc = _clahe_bgr(proc)

    # Contrast enhancement
    if do_contrast:
        proc = _contrast_enhance(proc)

    # Color normalize (optional)
    if do_color_norm:
        proc = _color_normalize_reinhard(proc)

    # Convert to gray for segmentation
    img_gray = cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)

    # Segmentation
    seg_mask = _segment_cells(img_gray)

    # Detect cells
    cells = _detect_cell_contours(seg_mask, min_area=segmentation_min_area)

    # Detect nuclei per cell and extract features
    nuclei_all = []
    per_cell_features = []
    for c in cells:
        bbox = c["bbox"]
        nuclei = _detect_nuclei(img_gray, tuple(bbox))
        nuclei_all.extend(nuclei)
        feats = _extract_features(img_gray, c)
        feats.update({"bbox": c["bbox"], "centroid": c["centroid"]})
        per_cell_features.append(feats)

    # Build outputs
    processed_rgb = cv2.cvtColor(proc, cv2.COLOR_BGR2RGB)
    processed_bytes = _to_rgb_bytes(processed_rgb)
    mask_png_bytes = _to_png_bytes((seg_mask * 255).astype(np.uint8))

    # global features
    global_feats = {
        "orig_width": int(w),
        "orig_height": int(h),
        "resized_width": int(target_w),
        "resized_height": int(target_h),
        "num_cells": len(cells),
        "num_nuclei": len(nuclei_all),
    }

    return {
        "processed_image_bytes": processed_bytes,
        "segmentation_mask_bytes": mask_png_bytes,
        "cell_bboxes": cells,
        "nucleus_bboxes": nuclei_all,
        "per_cell_features": per_cell_features,
        "global_features": global_feats,
    }


def preprocess_image_file(path: str, **kwargs) -> Dict[str, Any]:
    with open(path, "rb") as fh:
        data = fh.read()
    return preprocess_image_bytes(data, **kwargs)

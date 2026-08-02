from typing import Dict, Any, List, Optional
from app.ai.clinical import constants as C


def _safe_get_prob(probs: Dict[str, float], keys: List[str]) -> float:
    for k in keys:
        if k in probs:
            try:
                return float(probs[k])
            except Exception:
                continue
    return 0.0


def _aggregate_cell_features(per_cell_features: Optional[List[Dict[str, Any]]]) -> Dict[str, float]:
    if not per_cell_features:
        return {"mean_nucleus_area": 0.0, "mean_solidity": 0.0, "num_cells": 0}
    total_area = 0.0
    total_solidity = 0.0
    count = 0
    for c in per_cell_features:
        count += 1
        total_area += float(c.get("mean_nucleus_area", c.get("area", 0))) if (c.get("mean_nucleus_area") is not None or c.get("area") is not None) else 0.0
        total_solidity += float(c.get("solidity", 0.0))
    return {
        "mean_nucleus_area": (total_area / count) if count else 0.0,
        "mean_solidity": (total_solidity / count) if count else 0.0,
        "num_cells": count,
    }


def estimate_stage(
    clinical_data: Optional[Dict[str, Any]],
    image_probs: Dict[str, float],
    per_cell_features: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Explainable heuristic clinical stage estimator.

    IMPORTANT: This function implements an explainable heuristic combining image-based
    predictions and available clinical data. It is NOT a clinical diagnosis tool.
    Use only as decision support; final clinical staging must be performed by qualified clinicians.

    Inputs:
      - clinical_data: dict with optional keys (hpv, biopsy, imaging, symptoms) -- case-insensitive
      - image_probs: dict of label->probability (e.g., {"normal":0.1, "low_grade":0.2, "high_grade":0.3, "cancer":0.4})
      - per_cell_features: list of per-cell feature dicts, each may include 'mean_nucleus_area', 'solidity', 'area'

    Returns:
      {
        "stage": "Stage II",
        "confidence": 0.78,
        "explanation": "...",
        "contributing_factors": [...],
        "normalized_score": 0.512
      }
    """
    # Normalize probabilities keys to lowercase
    probs = {k.lower(): float(v) for k, v in (image_probs or {}).items()}

    cancer_prob = _safe_get_prob(probs, ["cancer", "suspected malignancy", "malignancy"])
    high_grade_prob = _safe_get_prob(probs, ["high_grade", "hsil", "high-grade"]) 
    low_grade_prob = _safe_get_prob(probs, ["low_grade", "lsil", "low-grade"]) 

    # Base score from image model using configurable weights
    score = cancer_prob * C.WEIGHT_CANCER + high_grade_prob * C.WEIGHT_HIGH_GRADE + low_grade_prob * C.WEIGHT_LOW_GRADE
    factors: List[str] = []
    factors.append(f"model:cancer={cancer_prob:.3f}")
    factors.append(f"model:high_grade={high_grade_prob:.3f}")
    factors.append(f"model:low_grade={low_grade_prob:.3f}")

    # Clinical inputs
    hpv_positive = False
    biopsy_info = None
    imaging_info = None
    symptoms = None

    if clinical_data:
        cd = {k.lower(): v for k, v in clinical_data.items()}
        hpv_val = cd.get("hpv") or cd.get("hpv_status")
        if isinstance(hpv_val, str):
            if hpv_val.lower() in ["positive", "pos", "yes", "true", "1"]:
                hpv_positive = True
        elif isinstance(hpv_val, bool):
            hpv_positive = hpv_val
        if hpv_positive:
            score += C.WEIGHT_HPV_POSITIVE
            factors.append("clinical:hpv=positive")

        biopsy_info = cd.get("biopsy") or cd.get("histopathology")
        if biopsy_info:
            b = str(biopsy_info).lower()
            if "invasive" in b or "carcinoma" in b or "squamous cell carcinoma" in b:
                score += C.WEIGHT_BIOPSY_INVASIVE
                factors.append("clinical:biopsy=invasive")
            elif "high-grade" in b or "hsil" in b or "high grade" in b:
                score += C.WEIGHT_BIOPSY_HIGH_GRADE
                factors.append("clinical:biopsy=high_grade")
            elif "low-grade" in b or "lsil" in b:
                score += C.WEIGHT_BIOPSY_LOW_GRADE
                factors.append("clinical:biopsy=low_grade")

        imaging_info = cd.get("imaging")
        if imaging_info and isinstance(imaging_info, str):
            im = imaging_info.lower()
            if "node" in im or "metast" in im or "paramet" in im:
                score += C.WEIGHT_IMAGING_SPREAD
                factors.append("clinical:imaging_suggests_spread")
            elif "mass" in im or "lesion" in im:
                score += C.WEIGHT_IMAGING_MASS
                factors.append("clinical:imaging_mass_or_lesion")

        symptoms = cd.get("symptoms")
        if symptoms and isinstance(symptoms, str):
            s = symptoms.lower()
            if any(x in s for x in ["bleeding", "pelvic pain", "weight loss"]):
                score += C.WEIGHT_SYMPTOMS
                factors.append("clinical:symptoms_severe")

    # Aggregate cell features
    agg = _aggregate_cell_features(per_cell_features)
    mean_nucleus_area = agg.get("mean_nucleus_area", 0.0)
    mean_solidity = agg.get("mean_solidity", 0.0)
    num_cells = agg.get("num_cells", 0)

    if mean_nucleus_area > C.NUCLEUS_AREA_THRESHOLD:
        score += C.WEIGHT_NUCLEUS_AREA
        factors.append(f"cell:mean_nucleus_area={mean_nucleus_area:.1f}")
    if mean_solidity < C.SOLIDITY_THRESHOLD and mean_solidity > 0:
        score += C.WEIGHT_SOLIDITY
        factors.append(f"cell:mean_solidity={mean_solidity:.2f}")
    if num_cells > 1000:
        score += 0.05
        factors.append(f"cell:num_cells={num_cells}")

    # Normalize score
    norm_score = max(0.0, min(score / C.MAX_SCORE, 1.0))

    # Map normalized score to stage using configurable thresholds
    stage = "Stage 0"
    for sname, (low, high) in C.STAGE_THRESHOLDS.items():
        if norm_score >= low and norm_score < high:
            stage = sname
            break
    else:
        # If exactly 1.0
        if norm_score >= 1.0:
            stage = "Stage IV"

    # Confidence based on distance to center of bucket
    low, high = C.STAGE_THRESHOLDS.get(stage, (0.0, 1.0))
    midpoint = (low + high) / 2.0
    distance = abs(norm_score - midpoint)
    half_width = (high - low) / 2.0 if (high - low) > 0 else 0.001
    confidence = float(0.5 + 0.5 * min(1.0, distance / (half_width + 1e-8)))

    explanation = (
        f"Heuristic combined evidence score {score:.3f} normalized {norm_score:.3f}; primary contributors: " + ", ".join(factors)
    )

    return {
        "stage": stage,
        "confidence": round(confidence, 3),
        "explanation": explanation,
        "contributing_factors": factors,
        "normalized_score": round(norm_score, 3),
    }

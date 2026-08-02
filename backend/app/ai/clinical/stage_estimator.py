from typing import Dict, Any, List, Optional
import math


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
        total_area += float(c.get("mean_nucleus_area", c.get("area", 0))) if c.get("mean_nucleus_area") is not None or c.get("area") is not None else 0.0
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
    Estimate clinical stage (Stage 0, I, II, III, IV) using a deterministic, explainable rule-based approach
    that combines image model probabilities with available clinical data and simple image-derived features.

    Returns:
      {
        "stage": "Stage II",
        "confidence": 0.78,  # 0..1
        "explanation": "...",
        "contributing_factors": ["model_prob_cancer=0.82", "biopsy=invasive", "hpv=positive"]
      }

    Notes:
      - This is intentionally rule-based to avoid depending on a pre-trained clinical model artifact.
      - Clinical data keys supported (case-insensitive): 'hpv', 'biopsy', 'symptoms', 'imaging'
    """
    # Normalize keys: lower-case
    probs = {k.lower(): float(v) for k, v in (image_probs or {}).items()}

    # Map probable labels (depends on your label map). We support common label aliases
    cancer_prob = _safe_get_prob(probs, ["cancer", "suspected malignancy", "malignancy"])
    high_grade_prob = _safe_get_prob(probs, ["high_grade", "hsil", "high-grade"])
    low_grade_prob = _safe_get_prob(probs, ["low_grade", "lsil", "low-grade"])
    normal_prob = _safe_get_prob(probs, ["normal", "neg"])

    # Base score from image model
    # Weights chosen so cancer contributes most, then high_grade, then low_grade
    score = cancer_prob * 1.0 + high_grade_prob * 0.6 + low_grade_prob * 0.25
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
        # normalize keys to lower
        cd = {k.lower(): v for k, v in clinical_data.items()}
        # HPV
        hpv_val = cd.get("hpv") or cd.get("hpv_status")
        if isinstance(hpv_val, str):
            if hpv_val.lower() in ["positive", "pos", "yes", "true", "1"]:
                hpv_positive = True
        elif isinstance(hpv_val, bool):
            hpv_positive = hpv_val
        if hpv_positive:
            score += 0.25
            factors.append("clinical:hpv=positive")

        # biopsy
        biopsy_info = cd.get("biopsy") or cd.get("histopathology")
        if biopsy_info:
            b = str(biopsy_info).lower()
            if "invasive" in b or "carcinoma" in b or "squamous cell carcinoma" in b:
                score += 1.0
                factors.append("clinical:biopsy=invasive")
            elif "high-grade" in b or "hsil" in b or "high grade" in b:
                score += 0.5
                factors.append("clinical:biopsy=high_grade")
            elif "low-grade" in b or "lsil" in b:
                score += 0.15
                factors.append("clinical:biopsy=low_grade")

        # imaging
        imaging_info = cd.get("imaging")
        if imaging_info and isinstance(imaging_info, str):
            im = imaging_info.lower()
            if "node" in im or "metast" in im or "paramet" in im:
                score += 0.8
                factors.append("clinical:imaging_suggests_spread")
            elif "mass" in im or "lesion" in im:
                score += 0.3
                factors.append("clinical:imaging_mass_or_lesion")

        # symptoms
        symptoms = cd.get("symptoms")
        if symptoms and isinstance(symptoms, str):
            s = symptoms.lower()
            if any(x in s for x in ["bleeding", "pelvic pain", "weight loss"]):
                score += 0.15
                factors.append("clinical:symptoms_severe")

    # Per-cell features aggregation
    agg = _aggregate_cell_features(per_cell_features)
    mean_nucleus_area = agg.get("mean_nucleus_area", 0.0)
    mean_solidity = agg.get("mean_solidity", 0.0)
    num_cells = agg.get("num_cells", 0)
    # Heuristics: large nucleus area and low solidity may indicate malignancy
    if mean_nucleus_area > 300.0:  # threshold empiric; depends on pixel scale
        score += 0.3
        factors.append(f"cell:mean_nucleus_area={mean_nucleus_area:.1f}")
    if mean_solidity < 0.5 and mean_solidity > 0:
        score += 0.2
        factors.append(f"cell:mean_solidity={mean_solidity:.2f}")
    if num_cells > 1000:
        # crowded field may indicate sample type, moderate influence
        score += 0.05
        factors.append(f"cell:num_cells={num_cells}")

    # Bound score to [0, 2.5] possible max; normalize to [0,1]
    max_score = 3.0
    norm_score = max(0.0, min(score / max_score, 1.0))

    # Map normalized score to stages
    # Conservative mapping: higher score -> higher stage
    if norm_score < 0.15:
        stage = "Stage 0"
    elif norm_score < 0.35:
        stage = "Stage I"
    elif norm_score < 0.6:
        stage = "Stage II"
    elif norm_score < 0.85:
        stage = "Stage III"
    else:
        stage = "Stage IV"

    # Confidence: base on how far score is from adjacent thresholds
    # compute distance to midpoint of assigned bucket
    thresholds = {
        "Stage 0": (0.0, 0.15),
        "Stage I": (0.15, 0.35),
        "Stage II": (0.35, 0.6),
        "Stage III": (0.6, 0.85),
        "Stage IV": (0.85, 1.0),
    }
    low, high = thresholds[stage]
    midpoint = (low + high) / 2.0
    # confidence scaled from 0.5..1.0 depending distance from boundary
    distance = abs(norm_score - midpoint)
    half_width = (high - low) / 2.0 if (high - low) > 0 else 0.001
    confidence = float(0.5 + 0.5 * min(1.0, distance / (half_width + 1e-8)))

    explanation = (
        f"Combined evidence score {score:.3f} normalized {norm_score:.3f}; primary contributors: " + ", ".join(factors)
    )

    return {
        "stage": stage,
        "confidence": round(confidence, 3),
        "explanation": explanation,
        "contributing_factors": factors,
        "normalized_score": round(norm_score, 3),
    }

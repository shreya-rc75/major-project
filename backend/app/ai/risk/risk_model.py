from typing import Dict, Any, List, Optional
from app.ai.risk import constants as C


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


def _categorize_risk(score: float) -> str:
    if score < C.RISK_THRESHOLDS["low"]:
        return "low"
    if score < C.RISK_THRESHOLDS["medium"]:
        return "medium"
    return "high"


def predict_risk(
    clinical_data: Optional[Dict[str, Any]],
    image_probs: Dict[str, float],
    per_cell_features: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Predicts 1/3/5 year progression risk using an explainable heuristic combining image and clinical features.

    Returns:
      {
        "risk_1y": 0.05,
        "risk_3y": 0.12,
        "risk_5y": 0.25,
        "risk_category": "medium",
        "confidence": 0.78,
        "recommendations": "...",
        "contributing_factors": [...]
      }
    """
    probs = {k.lower(): float(v) for k, v in (image_probs or {}).items()}
    cancer_prob = _safe_get_prob(probs, ["cancer", "suspected malignancy", "malignancy"]) 
    high_grade_prob = _safe_get_prob(probs, ["high_grade", "hsil", "high-grade"]) 
    low_grade_prob = _safe_get_prob(probs, ["low_grade", "lsil", "low-grade"]) 

    base = cancer_prob * C.WEIGHT_CANCER + high_grade_prob * C.WEIGHT_HIGH_GRADE + low_grade_prob * C.WEIGHT_LOW_GRADE
    factors: List[str] = [f"model:cancer={cancer_prob:.3f}", f"model:high_grade={high_grade_prob:.3f}", f"model:low_grade={low_grade_prob:.3f}"]

    # Clinical data influence
    hpv_positive = False
    if clinical_data:
        cd = {k.lower(): v for k, v in clinical_data.items()}
        hpv_val = cd.get("hpv") or cd.get("hpv_status")
        if isinstance(hpv_val, str):
            if hpv_val.lower() in ["positive", "pos", "yes", "true", "1"]:
                hpv_positive = True
        elif isinstance(hpv_val, bool):
            hpv_positive = hpv_val
        if hpv_positive:
            base += C.WEIGHT_HPV
            factors.append("clinical:hpv=positive")

        biopsy = cd.get("biopsy") or cd.get("histopathology")
        if biopsy:
            b = str(biopsy).lower()
            if "invasive" in b or "carcinoma" in b:
                base += C.WEIGHT_BIOPSY_INVASIVE
                factors.append("clinical:biopsy=invasive")
            elif "high-grade" in b or "hsil" in b:
                base += C.WEIGHT_BIOPSY_HIGH_GRADE
                factors.append("clinical:biopsy=high_grade")
            elif "low-grade" in b or "lsil" in b:
                base += C.WEIGHT_BIOPSY_LOW_GRADE
                factors.append("clinical:biopsy=low_grade")

        imaging = cd.get("imaging")
        if imaging and isinstance(imaging, str):
            im = imaging.lower()
            if "node" in im or "metast" in im:
                base += C.WEIGHT_IMAGING_SPREAD
                factors.append("clinical:imaging_suggests_spread")

    # Cell-derived features
    agg = _aggregate_cell_features(per_cell_features)
    mean_nucleus_area = agg.get("mean_nucleus_area", 0.0)
    mean_solidity = agg.get("mean_solidity", 0.0)
    num_cells = agg.get("num_cells", 0)

    if mean_nucleus_area > C.NUCLEUS_AREA_THRESHOLD:
        base += C.WEIGHT_NUCLEUS_AREA
        factors.append(f"cell:mean_nucleus_area={mean_nucleus_area:.1f}")
    if mean_solidity < C.SOLIDITY_THRESHOLD and mean_solidity > 0:
        base += C.WEIGHT_SOLIDITY
        factors.append(f"cell:mean_solidity={mean_solidity:.2f}")

    # Scale base to a 0..1 raw risk score using configurable MAX_BASE
    raw = max(0.0, min(base / C.MAX_BASE, 1.0))

    # Derive timepoint risks (heuristic scaling)
    risk_1y = float(min(0.99, raw * C.SCALE_1Y))
    risk_3y = float(min(0.99, raw * C.SCALE_3Y))
    risk_5y = float(min(0.99, raw * C.SCALE_5Y))

    # Aggregate risk score for category & confidence
    overall = max(risk_1y, risk_3y, risk_5y)
    category = _categorize_risk(overall)

    # Confidence: based on amount of clinical + image evidence
    evidence_strength = 0.0
    # model evidence weight
    evidence_strength += (cancer_prob * 0.6 + high_grade_prob * 0.3 + low_grade_prob * 0.1)
    # clinical evidence
    if hpv_positive:
        evidence_strength += 0.15
    if clinical_data and (clinical_data.get("biopsy") or clinical_data.get("histopathology")):
        evidence_strength += 0.25
    # cell features
    if mean_nucleus_area > C.NUCLEUS_AREA_THRESHOLD:
        evidence_strength += 0.1

    confidence = float(max(0.0, min(1.0, evidence_strength)))

    # Recommendations based on category
    recs = []
    if category == "high":
        recs.append("Urgent referral to oncology and expedited biopsy recommended.")
    if category == "medium":
        recs.append("Recommend colposcopy and closer follow-up within 3 months.")
    if category == "low":
        recs.append("Routine surveillance as per screening guidelines.")

    return {
        "risk_1y": round(risk_1y, 4),
        "risk_3y": round(risk_3y, 4),
        "risk_5y": round(risk_5y, 4),
        "risk_category": category,
        "confidence": round(confidence, 3),
        "recommendations": recs,
        "contributing_factors": factors,
    }

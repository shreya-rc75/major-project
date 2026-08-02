import pytest
from app.ai.clinical.stage_estimator import estimate_stage


def test_estimate_stage_normal():
    clinical = {"hpv": "negative"}
    probs = {"normal": 0.9, "low_grade": 0.05, "high_grade": 0.03, "cancer": 0.02}
    res = estimate_stage(clinical, probs, [])
    assert res["stage"] == "Stage 0"
    assert 0.0 <= res["confidence"] <= 1.0


def test_estimate_stage_low_grade():
    clinical = {"hpv": "positive"}
    probs = {"normal": 0.6, "low_grade": 0.3, "high_grade": 0.08, "cancer": 0.02}
    res = estimate_stage(clinical, probs, [])
    assert res["stage"] in ["Stage 0", "Stage I"]


def test_estimate_stage_high_grade():
    clinical = {"hpv": "positive", "biopsy": "high-grade dysplasia"}
    probs = {"normal": 0.1, "low_grade": 0.1, "high_grade": 0.6, "cancer": 0.2}
    res = estimate_stage(clinical, probs, [{"mean_nucleus_area": 250, "solidity": 0.6}])
    assert res["stage"] in ["Stage I", "Stage II"]


def test_estimate_stage_cancer_with_biopsy():
    clinical = {"biopsy": "invasive squamous cell carcinoma", "imaging": "pelvic node enlargement"}
    probs = {"normal": 0.01, "low_grade": 0.02, "high_grade": 0.07, "cancer": 0.90}
    res = estimate_stage(clinical, probs, [{"mean_nucleus_area": 500, "solidity": 0.4}])
    assert res["stage"] in ["Stage III", "Stage IV"]
    assert res["confidence"] > 0.6


def test_estimate_stage_missing_inputs():
    # No clinical data and ambiguous probs
    res = estimate_stage(None, {"normal": 0.3, "low_grade": 0.3, "high_grade": 0.2, "cancer": 0.2}, None)
    assert "stage" in res
    assert 0.0 <= res["confidence"] <= 1.0

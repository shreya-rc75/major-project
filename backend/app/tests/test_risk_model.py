import pytest
from app.ai.risk.risk_model import predict_risk


def test_risk_low():
    clinical = {"hpv": "negative"}
    probs = {"normal": 0.9, "low_grade": 0.05, "high_grade": 0.03, "cancer": 0.02}
    res = predict_risk(clinical, probs, [])
    assert res["risk_category"] == "low"
    assert 0.0 <= res["risk_1y"] <= 1.0


def test_risk_medium():
    clinical = {"hpv": "positive"}
    probs = {"normal": 0.5, "low_grade": 0.3, "high_grade": 0.15, "cancer": 0.05}
    res = predict_risk(clinical, probs, [{"mean_nucleus_area": 350, "solidity": 0.6}])
    assert res["risk_category"] in ["low", "medium"]


def test_risk_high():
    clinical = {"biopsy": "invasive carcinoma", "imaging": "lymph node metastasis"}
    probs = {"normal": 0.01, "low_grade": 0.01, "high_grade": 0.08, "cancer": 0.9}
    res = predict_risk(clinical, probs, [{"mean_nucleus_area": 500, "solidity": 0.4}])
    assert res["risk_category"] == "high"
    assert res["confidence"] > 0.5


def test_risk_missing_inputs():
    res = predict_risk(None, {"normal": 0.3, "low_grade": 0.3, "high_grade": 0.2, "cancer": 0.2}, None)
    assert "risk_category" in res
    assert 0.0 <= res["confidence"] <= 1.0

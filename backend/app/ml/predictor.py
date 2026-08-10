from typing import Dict

def score_from_data(data: dict) -> Dict:
    # Ported from frontend heuristic (demo only)
    def safe_int(v):
        try:
            return int(v)
        except Exception:
            return 0

    score = 0
    age_score = 2 if safe_int(data.get("age", 0)) > 40 else 0
    if age_score:
        score += 2
    hpv_score = 3 if data.get("hpv") == "yes" else 0
    score += hpv_score
    smoking_score = 1 if data.get("smoking") == "yes" else 0
    score += smoking_score
    symptoms_score = 2 if data.get("symptoms") == "yes" else 0
    score += symptoms_score
    history_score = 2 if data.get("history") == "yes" else 0
    score += history_score
    abnormal_score = 2 if data.get("abnormalBleeding") == "yes" else 0
    score += abnormal_score
    previous_score = 1 if data.get("previousScreening") == "yes" else 0
    score += previous_score

    maxScore = 13
    riskPercentage = round((score / maxScore) * 100)

    stage = "Normal / Low Risk"
    risk = "Low"
    advice = "Routine screening and regular follow-up recommended."

    if score >= 3 and score <= 5:
        stage = "Possible Pre-Cancerous Changes"
        risk = "Moderate"
        advice = "Further Pap smear/HPV review and clinical monitoring advised."
    elif score >= 6 and score <= 8:
        stage = "Possible Early Stage Cervical Cancer"
        risk = "High"
        advice = "Detailed examination and specialist consultation recommended."
    elif score > 8:
        stage = "Possible Advanced Risk Condition"
        risk = "Very High"
        advice = "Immediate clinical investigation and oncologist review advised."

    risk_breakdown = {
        "age": age_score,
        "hpv": hpv_score,
        "smoking": smoking_score,
        "symptoms": symptoms_score,
        "history": history_score,
        "abnormalBleeding": abnormal_score,
        "previousScreening": previous_score,
    }

    result = {
        "score": score,
        "maxScore": maxScore,
        "riskPercentage": riskPercentage,
        "stage": stage,
        "risk": risk,
        "advice": advice,
        "riskBreakdown": risk_breakdown,
        "model_version": "demo-v1",
    }
    return result

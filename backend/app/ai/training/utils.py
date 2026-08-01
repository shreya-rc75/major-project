from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from typing import List, Dict


def compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    acc = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()
    return {"accuracy": float(acc), "precision": float(precision), "recall": float(recall), "f1": float(f1), "confusion_matrix": cm}

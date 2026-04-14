from __future__ import annotations

from sklearn.metrics import accuracy_score as sklearn_accuracy_score
from sklearn.metrics import f1_score as sklearn_f1_score


def accuracy_score(y_true: list[str], y_pred: list[str]) -> float:
    return float(sklearn_accuracy_score(y_true, y_pred))


def f1_score(y_true: list[str], y_pred: list[str]) -> float:
    return float(sklearn_f1_score(y_true, y_pred, average="weighted"))

from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics import accuracy_score, f1_score

from ticket_router_agent.domain.models import EvaluationSummary


@dataclass
class EvaluationMetrics:
    def compute(self, expected: list[str], predicted: list[str]) -> EvaluationSummary:
        return EvaluationSummary(
            accuracy=float(accuracy_score(expected, predicted)),
            f1_macro=float(f1_score(expected, predicted, average="macro")),
            sample_size=len(expected),
        )

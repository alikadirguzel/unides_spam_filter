"""Tiny JSON-backed linear models for scoring text features."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class LinearModel:
    """Simple logistic regression style model read from JSON."""

    bias: float
    weights: Dict[str, float]

    @classmethod
    def load(cls, path: Path) -> "LinearModel":
        with path.open("r", encoding="utf-8") as handler:
            payload = json.load(handler)
        return cls(bias=payload["bias"], weights=payload["features"])

    def predict_proba(self, features: Dict[str, float]) -> float:
        score = self.bias
        for feature, weight in self.weights.items():
            score += weight * float(features.get(feature, 0.0))
        return 1.0 / (1.0 + math.exp(-score))


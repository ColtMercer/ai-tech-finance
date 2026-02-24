from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import numpy as np


@dataclass
class TrendSignal:
    topic: str
    source: str
    score: float
    raw: dict
    detected_at: datetime


def velocity_score(series: Iterable[float]) -> float:
    values = np.array(list(series), dtype=float)
    if values.size < 2:
        return 0.0
    x = np.arange(values.size)
    slope = np.polyfit(x, values, 1)[0]
    return float(slope)

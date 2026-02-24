from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from pytrends.request import TrendReq

from src.config import get_logger
from src.trends.scorer import TrendSignal, velocity_score

DEFAULT_KEYWORDS = [
    "AI tools",
    "personal finance",
    "side hustle",
    "make money with AI",
    "investing",
]


def fetch_google_trends(keywords: Iterable[str] | None = None) -> list[TrendSignal]:
    logger = get_logger()
    keywords = list(keywords or DEFAULT_KEYWORDS)
    pytrends = TrendReq(hl="en-US", tz=360)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    timeframe = f"{start_time:%Y-%m-%d} {end_time:%Y-%m-%d}"

    signals: list[TrendSignal] = []
    for keyword in keywords:
        try:
            pytrends.build_payload([keyword], timeframe=timeframe, geo="US")
            data = pytrends.interest_over_time()
            if data.empty or keyword not in data:
                continue
            score = velocity_score(data[keyword].tolist())
            signals.append(
                TrendSignal(
                    topic=keyword,
                    source="google_trends",
                    score=score,
                    raw={"series": data[keyword].tolist(), "timeframe": timeframe},
                    detected_at=datetime.utcnow(),
                )
            )
        except Exception as exc:
            logger.exception("Google Trends fetch failed for %s: %s", keyword, exc)

    return signals

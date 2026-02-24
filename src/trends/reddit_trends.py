from __future__ import annotations

from datetime import datetime, timedelta

import praw

from src.config import get_config, get_logger
from src.trends.scorer import TrendSignal

SUBREDDITS = ["personalfinance", "artificial", "SideHustle"]


def fetch_reddit_trends(limit: int = 25) -> list[TrendSignal]:
    config = get_config()
    logger = get_logger()

    if not config.reddit_client_id or not config.reddit_client_secret:
        logger.warning("Reddit credentials missing; skipping Reddit trends.")
        return []

    reddit = praw.Reddit(
        client_id=config.reddit_client_id,
        client_secret=config.reddit_client_secret,
        user_agent=config.reddit_user_agent,
    )

    signals: list[TrendSignal] = []
    since = datetime.utcnow() - timedelta(days=2)

    for subreddit in SUBREDDITS:
        try:
            for submission in reddit.subreddit(subreddit).hot(limit=limit):
                created = datetime.utcfromtimestamp(submission.created_utc)
                if created < since:
                    continue
                velocity = (submission.score + submission.num_comments) / max(
                    (datetime.utcnow() - created).total_seconds() / 3600, 1
                )
                signals.append(
                    TrendSignal(
                        topic=submission.title,
                        source=f"reddit:{subreddit}",
                        score=float(velocity),
                        raw={
                            "score": submission.score,
                            "comments": submission.num_comments,
                            "url": submission.url,
                            "created_utc": submission.created_utc,
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        except Exception as exc:
            logger.exception("Reddit fetch failed for %s: %s", subreddit, exc)

    return signals

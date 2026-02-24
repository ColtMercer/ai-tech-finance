from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
import time

from apscheduler.schedulers.background import BackgroundScheduler

from src.config import (
    COLLECTION_POSTS,
    COLLECTION_SCRIPTS,
    COLLECTION_TRENDS,
    COLLECTION_VIDEOS,
    DB_NAME,
    get_config,
    get_logger,
    get_mongo_client,
)
from src.scripts.generator import generate_script
from src.trends.google_trends import fetch_google_trends
from src.trends.reddit_trends import fetch_reddit_trends
from src.trends.tiktok_trends import fetch_tiktok_trends
from src.video.producer import produce_video
from src.video.voiceover import VoiceoverGenerator
from src.poster.uploader import post_video

OUTPUT_DIR = Path("output")
ASSETS_DIR = Path("assets")


def _topic_hash(topic: str) -> str:
    return hashlib.sha256(topic.lower().encode("utf-8")).hexdigest()


def store_trends(trends: list[dict]) -> None:
    client = get_mongo_client()
    collection = client[DB_NAME][COLLECTION_TRENDS]
    if trends:
        collection.insert_many(trends)


def detect_trends() -> list[dict]:
    logger = get_logger()
    signals = [
        *fetch_google_trends(),
        *fetch_reddit_trends(),
        *fetch_tiktok_trends(),
    ]
    signals.sort(key=lambda s: s.score, reverse=True)

    trends = [
        {
            "topic": signal.topic,
            "source": signal.source,
            "score": signal.score,
            "raw": signal.raw,
            "detected_at": signal.detected_at,
        }
        for signal in signals
    ]

    store_trends(trends)
    logger.info("Detected %d trend signals", len(trends))
    return trends


def select_trend(trends: list[dict]) -> dict | None:
    client = get_mongo_client()
    collection = client[DB_NAME][COLLECTION_POSTS]

    for trend in trends:
        topic_hash = _topic_hash(trend["topic"])
        if collection.find_one({"topic_hash": topic_hash}):
            continue
        return trend
    return None


def run_pipeline() -> None:
    logger = get_logger()
    config = get_config()
    client = get_mongo_client()

    logger.info("Pipeline run started")
    try:
        trends = detect_trends()
        trend = select_trend(trends)
        if not trend:
            logger.warning("No new trends available.")
            return

        script = generate_script(trend["topic"])
        script_doc = {
            **script,
            "topic": trend["topic"],
            "created_at": datetime.utcnow(),
        }
        client[DB_NAME][COLLECTION_SCRIPTS].insert_one(script_doc)

        voice = VoiceoverGenerator()
        audio_path = OUTPUT_DIR / f"{_topic_hash(trend['topic'])}.wav"
        voice.synthesize(script["narration"], audio_path)

        video_path = OUTPUT_DIR / f"{_topic_hash(trend['topic'])}.mp4"
        video_result = produce_video(script, audio_path, video_path, ASSETS_DIR)

        client[DB_NAME][COLLECTION_VIDEOS].insert_one(
            {
                "topic": trend["topic"],
                "video_path": str(video_result.video_path),
                "duration": video_result.duration,
                "created_at": datetime.utcnow(),
            }
        )

        title = f\"{script['hook']} #{' #'.join(script['hashtags'])}\"
        upload_result = post_video(video_path, title=title)

        client[DB_NAME][COLLECTION_POSTS].insert_one(
            {
                "topic": trend["topic"],
                "topic_hash": _topic_hash(trend["topic"]),
                "publish_id": upload_result.publish_id,
                "status": upload_result.status,
                "created_at": datetime.utcnow(),
                "privacy": config.post_privacy,
            }
        )

        logger.info("Pipeline run finished")
    except Exception as exc:
        logger.exception("Pipeline run failed: %s", exc)


def schedule_jobs() -> BackgroundScheduler:
    logger = get_logger()
    scheduler = BackgroundScheduler()

    scheduler.add_job(detect_trends, "interval", hours=6, id="trend_detection")

    interval_hours = max(1, int(24 / max(get_config().posts_per_day, 1)))
    scheduler.add_job(run_pipeline, "interval", hours=interval_hours, id="pipeline")

    scheduler.start()
    logger.info("Scheduler started: trends every 6h, pipeline every %dh", interval_hours)
    return scheduler


def main() -> None:
    schedule_jobs()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        get_logger().info("Shutting down")


if __name__ == "__main__":
    main()

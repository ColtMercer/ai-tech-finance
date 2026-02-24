import logging
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    tiktok_client_key: str = os.getenv("TIKTOK_CLIENT_KEY", "")
    tiktok_client_secret: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    tiktok_redirect_uri: str = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8080/callback")
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "ai-tech-finance-bot/1.0")
    mongo_uri: str = os.getenv(
        "MONGO_URI",
        "mongodb://opus:opus_dev@localhost:27017/ai_tech_finance?authSource=admin",
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    posts_per_day: int = int(os.getenv("POSTS_PER_DAY", "2"))
    post_privacy: str = os.getenv("POST_PRIVACY", "SELF_ONLY")


DB_NAME = "ai_tech_finance"
COLLECTION_TRENDS = "trends"
COLLECTION_SCRIPTS = "scripts"
COLLECTION_VIDEOS = "videos"
COLLECTION_POSTS = "posts"


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    return MongoClient(get_config().mongo_uri)


@lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    config = get_config()
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    return logging.getLogger("ai_tech_finance")

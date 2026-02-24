from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx

from src.config import get_config, get_logger
from src.poster.auth import ensure_token

VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
VIDEO_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


@dataclass
class UploadResult:
    publish_id: str
    status: str


def init_video_upload(access_token: str, title: str, privacy: str, video_size: int) -> dict:
    payload = {
        "post_info": {
            "title": title,
            "privacy_level": privacy,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
        },
    }

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = httpx.post(VIDEO_INIT_URL, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    if "data" not in data:
        raise RuntimeError(f"Video init error: {data}")
    return data["data"]


def upload_video_file(upload_url: str, video_path: Path) -> None:
    with video_path.open("rb") as handle:
        response = httpx.put(upload_url, content=handle.read(), timeout=300)
        response.raise_for_status()


def fetch_publish_status(access_token: str, publish_id: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = httpx.post(
        VIDEO_STATUS_URL,
        json={"publish_id": publish_id},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "data" not in payload:
        raise RuntimeError(f"Status fetch error: {payload}")
    return payload["data"].get("status", "UNKNOWN")


def post_video(video_path: Path, title: str) -> UploadResult:
    config = get_config()
    logger = get_logger()

    token = ensure_token(scopes=["video.publish", "user.info.basic"])
    init_data = init_video_upload(
        token.access_token,
        title=title,
        privacy=config.post_privacy,
        video_size=video_path.stat().st_size,
    )

    upload_url = init_data.get("upload_url")
    publish_id = init_data.get("publish_id")
    if not upload_url or not publish_id:
        raise RuntimeError(f"Missing upload_url or publish_id: {init_data}")

    upload_video_file(upload_url, video_path)
    status = fetch_publish_status(token.access_token, publish_id)
    logger.info("TikTok publish status: %s", status)

    return UploadResult(publish_id=publish_id, status=status)

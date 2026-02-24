from __future__ import annotations

import json
from datetime import datetime

import httpx
import os

from src.config import get_config, get_logger

SYSTEM_PROMPT = (
    "You are a TikTok scriptwriter specializing in AI and personal finance. "
    "Create viral 30-60 second scripts with strong hooks, pattern interrupts, "
    "clear value delivery, and a concise CTA."
)


def build_prompt(topic: str) -> str:
    return (
        "Write a 30-60 second TikTok script about the topic below. "
        "Use a pattern-interrupt hook in the first 2 seconds. "
        "Deliver 3-5 concise value points in the body. "
        "End with a short CTA. Provide suggested hashtags. "
        "Also provide a full narration string for TTS.\n\n"
        f"Topic: {topic}\n\n"
        "Return ONLY valid JSON with keys: "
        "hook (string), body_points (array of strings), cta (string), "
        "hashtags (array of strings without #), narration (string)."
    )


def generate_script(topic: str) -> dict:
    config = get_config()
    logger = get_logger()

    # Support both direct Anthropic key and OpenAI-compatible endpoints
    api_key = config.anthropic_api_key or os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.anthropic.com")
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY or OPENAI_API_KEY missing.")

    prompt = build_prompt(topic)

    try:
        # Use Anthropic Messages API directly
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 800,
            "temperature": 0.7,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = httpx.post(
            f"{base_url}/v1/messages",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        content = result["content"][0]["text"] if result.get("content") else ""
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            if content.endswith("```"):
                content = content[:-3]
        data = json.loads(content.strip())
        data["topic"] = topic
        data["generated_at"] = datetime.utcnow().isoformat()
        return data
    except json.JSONDecodeError as exc:
        logger.exception("LLM JSON parse error: %s\nRaw: %s", exc, content)
        raise
    except Exception as exc:
        logger.exception("LLM generation failed: %s", exc)
        raise

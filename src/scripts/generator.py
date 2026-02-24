from __future__ import annotations

import json
from datetime import datetime

import anthropic

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

    if not config.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY missing.")

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    prompt = build_prompt(topic)

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text if response.content else ""
        data = json.loads(content)
        data["topic"] = topic
        data["generated_at"] = datetime.utcnow().isoformat()
        return data
    except json.JSONDecodeError as exc:
        logger.exception("Claude JSON parse error: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Claude generation failed: %s", exc)
        raise

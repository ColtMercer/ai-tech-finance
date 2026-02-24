from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, vfx

from src.config import get_logger
from src.video.captions import build_captions

WIDTH = 1080
HEIGHT = 1920


@dataclass
class VideoResult:
    video_path: Path
    duration: float


def _find_font(fonts_dir: Path) -> Path | None:
    for ext in ("*.ttf", "*.otf"):
        matches = list(fonts_dir.glob(ext))
        if matches:
            return matches[0]
    return None


def _gradient_background() -> Image.Image:
    top = np.array([11, 15, 26], dtype=float)
    bottom = np.array([28, 34, 51], dtype=float)
    gradient = np.linspace(0, 1, HEIGHT)[:, None]
    colors = (top + (bottom - top) * gradient).astype(np.uint8)
    image = np.tile(colors[:, np.newaxis, :], (1, WIDTH, 1))
    noise = np.random.normal(0, 6, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(image, mode="RGB")


def _render_text(text: str, font_path: Path | None, font_size: int, stroke: int = 4) -> Image.Image:
    font = (
        ImageFont.truetype(str(font_path), font_size)
        if font_path and font_path.exists()
        else ImageFont.load_default()
    )
    dummy = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    text_bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    text_width = int(text_bbox[2] - text_bbox[0])
    text_height = int(text_bbox[3] - text_bbox[1])
    padding = 20
    canvas = Image.new("RGBA", (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.multiline_text(
        (padding, padding),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        align="center",
        stroke_width=stroke,
        stroke_fill=(0, 0, 0, 200),
    )
    return canvas


def _word_timings(text: str, duration: float) -> list[tuple[str, float, float]]:
    words = text.split()
    if not words:
        return []
    per_word = duration / len(words)
    timings = []
    for i, word in enumerate(words):
        start = i * per_word
        end = start + per_word
        timings.append((word, start, end))
    return timings


def produce_video(script: dict, audio_path: Path, output_path: Path, assets_dir: Path) -> VideoResult:
    logger = get_logger()
    audio_clip = AudioFileClip(str(audio_path))
    duration = audio_clip.duration

    background = _gradient_background()
    bg_clip = ImageClip(np.array(background)).with_duration(duration)

    font_path = _find_font(assets_dir / "fonts")

    word_clips = []
    for word, start, end in _word_timings(script["hook"] + " " + " ".join(script["body_points"]), duration):
        img = _render_text(word.upper(), font_path, font_size=96)
        clip = (
            ImageClip(np.array(img))
            .with_start(start)
            .with_end(end)
            .with_position(("center", "center"))
            .with_effects([vfx.CrossFadeIn(0.15)])
        )
        word_clips.append(clip)

    caption_clips = []
    captions = build_captions(script["narration"], duration)
    for caption in captions:
        img = _render_text(caption.text, font_path, font_size=54, stroke=3)
        clip = (
            ImageClip(np.array(img))
            .with_start(caption.start)
            .with_end(caption.end)
            .with_position(("center", HEIGHT - 320))
            .with_effects([vfx.CrossFadeIn(0.1)])
        )
        caption_clips.append(clip)

    composite = CompositeVideoClip([bg_clip, *word_clips, *caption_clips], size=(WIDTH, HEIGHT))
    composite = composite.with_audio(audio_clip)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    composite.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="medium",
        threads=4,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    logger.info("Video rendered: %s", output_path)

    return VideoResult(video_path=output_path, duration=duration)

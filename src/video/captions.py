from __future__ import annotations

from dataclasses import dataclass

@dataclass
class Caption:
    text: str
    start: float
    end: float


def build_captions(text: str, duration: float, max_chars: int = 28) -> list[Caption]:
    words = text.split()
    if not words:
        return []

    lines = []
    current = []
    for word in words:
        tentative = " ".join(current + [word])
        if len(tentative) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))

    per_line = duration / max(len(lines), 1)
    captions = []
    for idx, line in enumerate(lines):
        start = idx * per_line
        end = start + per_line
        captions.append(Caption(text=line, start=start, end=end))
    return captions

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import soundfile as sf
from pykokoro import KokoroPipeline, PipelineConfig

from src.config import get_logger


@dataclass
class VoiceoverResult:
    audio_path: Path
    sample_rate: int
    duration: float


class VoiceoverGenerator:
    def __init__(self, voice: str = "af_bella") -> None:
        self.voice = voice
        self._pipeline: KokoroPipeline | None = None
        self.logger = get_logger()

    def _get_pipeline(self) -> KokoroPipeline:
        if self._pipeline is None:
            self._pipeline = KokoroPipeline(PipelineConfig(voice=self.voice))
        return self._pipeline

    def synthesize(self, text: str, output_path: Path) -> VoiceoverResult:
        pipeline = self._get_pipeline()
        result = pipeline.run(text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), result.audio, result.sample_rate)
        duration = len(result.audio) / float(result.sample_rate)
        self.logger.info("Generated voiceover: %s (%.2fs)", output_path, duration)
        return VoiceoverResult(output_path, result.sample_rate, duration)

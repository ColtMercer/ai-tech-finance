"""End-to-end test: generate script → voiceover → video."""
import json
from pathlib import Path
from src.scripts.generator import generate_script
from src.video.voiceover import VoiceoverGenerator
from src.video.producer import produce_video

OUTPUT = Path("output")
ASSETS = Path("assets")
OUTPUT.mkdir(exist_ok=True)

# Step 1: Generate script
print("=== Generating script ===")
script = generate_script("make money with AI")
print(json.dumps(script, indent=2))

# Step 2: Generate voiceover
print("\n=== Generating voiceover ===")
voice = VoiceoverGenerator()
audio_path = OUTPUT / "test_voiceover.wav"
voice.synthesize(script["narration"], audio_path)
print(f"Audio saved: {audio_path}")

# Step 3: Produce video
print("\n=== Producing video ===")
video_path = OUTPUT / "test_video.mp4"
result = produce_video(script, audio_path, video_path, ASSETS)
print(f"Video saved: {result.video_path} ({result.duration:.1f}s)")
print("\nDone! Check output/test_video.mp4")

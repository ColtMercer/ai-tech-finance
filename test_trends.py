"""Quick test: fetch Google Trends and generate a script for the top trend."""
import json
from src.trends.google_trends import fetch_google_trends
from src.scripts.generator import generate_script

print("=== Fetching Google Trends ===")
signals = fetch_google_trends()
for s in signals:
    print(f"  {s.topic}: score={s.score:.2f} (source={s.source})")

if signals:
    top = max(signals, key=lambda s: s.score)
    print(f"\n=== Generating script for: {top.topic} ===")
    script = generate_script(top.topic)
    print(json.dumps(script, indent=2))
else:
    print("No trends found.")

# AI Tech Finance - TikTok Shorts Automation

Automated pipeline for creating and posting AI/finance TikTok shorts to @ai.tech.finance.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Trend      │────▶│   Script     │────▶│   Video     │────▶│  TikTok  │
│   Detection  │     │   Generator  │     │   Producer  │     │  Poster  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
```

## Stack
- **Language:** Python 3.12+
- **Trend Detection:** TikTok Creative Center, Google Trends (pytrends), Reddit/X monitoring
- **Script Generation:** Claude API (via Anthropic SDK)
- **Voice:** Kokoro TTS (local, free)
- **Video Assembly:** MoviePy + stock footage
- **Posting:** TikTok Content Posting API
- **Database:** MongoDB (existing local infra)
- **Scheduler:** APScheduler

## Setup
```bash
docker compose up -d
```

## Environment Variables
See `.env.example` for required variables.

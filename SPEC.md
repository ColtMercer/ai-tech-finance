# AI Tech Finance - Project Specification

## Overview
Automated TikTok shorts pipeline for @ai.tech.finance. Detects trending AI/finance topics, generates scripts, produces faceless short videos with AI voiceover, and posts to TikTok.

## MVP Scope (Phase 1)

### 1. Trend Detection Module (`src/trends/`)
- **Google Trends**: Monitor rising queries for "AI tools", "personal finance", "side hustle", "make money with AI", etc.
- **TikTok Creative Center**: Scrape trending hashtags and sounds in tech/finance categories
- **Reddit**: Monitor r/personalfinance, r/artificial, r/SideHustle for hot topics
- Scoring: rank trends by velocity (growth rate) not absolute volume
- Store trends in MongoDB collection `trends`
- Run every 6 hours

### 2. Script Generator (`src/scripts/`)
- Takes a trending topic and generates a 30-60 second TikTok script
- Uses Claude API (Anthropic SDK)
- Script format:
  - Hook (first 2 seconds, pattern-interrupt)
  - Body (value delivery, 3-5 key points)
  - CTA (follow, like, save)
- Include suggested hashtags
- Store scripts in MongoDB collection `scripts`

### 3. Video Producer (`src/video/`)
- Text-on-screen overlay with animations
- AI voiceover using Kokoro TTS (local)
- Background: stock footage or gradient animations
- Output: MP4, 1080x1920 (9:16 vertical), H.264
- Captions/subtitles burned in (for silent viewers)
- Store video metadata in MongoDB collection `videos`

### 4. TikTok Poster (`src/poster/`)
- OAuth 2.0 flow with TikTok API
- Upload video via Content Posting API (Direct Post)
- Set title with hashtags
- Privacy: PUBLIC_TO_EVERYONE (after audit; SELF_ONLY during testing)
- Track post status in MongoDB collection `posts`

### 5. Orchestrator (`src/orchestrator.py`)
- Coordinates the full pipeline: detect → script → video → post
- Configurable schedule (default: 2 posts/day)
- Deduplication: don't post about same topic twice
- Logging and error handling

### 6. Docker Setup
- Dockerfile for the app
- docker-compose.yml that connects to existing opus_infra network (MongoDB on localhost:27017)
- Volume mount for generated videos

## Tech Stack
- Python 3.12
- anthropic SDK (Claude for scripts)
- pytrends (Google Trends)
- praw (Reddit API)
- kokoro (TTS)
- moviepy (video assembly)
- Pillow (text rendering)
- pymongo (MongoDB)
- httpx (TikTok API calls)
- APScheduler (scheduling)
- Docker + docker-compose

## Database (MongoDB)
- Database name: `ai_tech_finance`
- Collections: `trends`, `scripts`, `videos`, `posts`
- Connect via: `mongodb://opus:opus_dev@localhost:27017/ai_tech_finance?authSource=admin`

## Environment Variables (.env.example)
```
ANTHROPIC_API_KEY=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_REDIRECT_URI=http://localhost:8080/callback
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=ai-tech-finance-bot/1.0
MONGO_URI=mongodb://opus:opus_dev@localhost:27017/ai_tech_finance?authSource=admin
```

## File Structure
```
ai-tech-finance/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py            # Load env vars, constants
│   ├── trends/
│   │   ├── __init__.py
│   │   ├── google_trends.py
│   │   ├── tiktok_trends.py
│   │   ├── reddit_trends.py
│   │   └── scorer.py        # Velocity scoring
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── generator.py     # Claude-powered script gen
│   ├── video/
│   │   ├── __init__.py
│   │   ├── producer.py      # MoviePy video assembly
│   │   ├── voiceover.py     # Kokoro TTS
│   │   └── captions.py      # Subtitle burn-in
│   ├── poster/
│   │   ├── __init__.py
│   │   ├── auth.py          # TikTok OAuth
│   │   └── uploader.py      # Content Posting API
│   └── orchestrator.py      # Main pipeline coordinator
├── assets/
│   ├── fonts/               # Bold fonts for text overlay
│   └── backgrounds/         # Stock video/gradient templates
├── output/                  # Generated videos (gitignored)
└── tests/
    └── ...
```

## Notes
- Until TikTok audit passes, all posts are private (SELF_ONLY)
- Start with Google Trends + Reddit for trend detection (TikTok Creative Center scraping can be added later)
- Kokoro TTS is free and local — no API costs
- Video style: bold text on screen, AI voiceover, engaging background

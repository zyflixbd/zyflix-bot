# ZyFlix Telegram Bot 🎬

TMDB থেকে daily popular movies এনে ZYFlixBD channel এ auto-post করে।

## Files
- `zyflix_bot.py` — main bot
- `requirements.txt` — dependencies  
- `.github/workflows/daily_post.yml` — GitHub Actions (auto daily run)

## Setup

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Run locally
```bash
python zyflix_bot.py
```

### 3. GitHub Actions (Free Auto Daily Post)
1. GitHub এ new repository বানাও
2. এই সব files upload করো
3. Repository → Settings → Secrets → New secret:
   - (এই bot এ secrets দরকার নেই, সব already configured)
4. Actions tab এ গিয়ে enable করো
5. প্রতিদিন BD সময় সকাল ১০টায় auto post হবে ✅

## Post Format
- 🖼 Movie poster (high quality)
- ⭐ Rating + vote count
- 🎭 Genre
- 📝 Overview
- [▶️ Watch Now — ZyFlix] button → zyflix.tech
- [🎬 Official Trailer] button → YouTube
- [🤖 Bot] [🌐 Website] buttons

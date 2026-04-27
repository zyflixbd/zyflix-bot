import requests
import schedule
import time
import json
import os
import asyncio
from datetime import date
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# ─── CONFIG ───────────────────────────────────────────
TMDB_API_KEY = "4fc3e39dae386978d3b3c1ed6047a390"
BOT_TOKEN    = "8031790421:AAFNev9U8DOnpDc6TQxBBeJ7XyqIXCuzFSQ"
CHANNEL_ID   = "@ZYFlixBD"
WATCH_BASE   = "https://zyflix.tech"
POSTED_FILE  = "posted_movies.json"

# ─── POST SCHEDULE (BD TIME) ──────────────────────────
# Hollywood  → সকাল ৯টা   (5 টা)
# Bollywood  → বিকাল ৫টা  (5 টা)
HOLLYWOOD_TIME = "09:00"
BOLLYWOOD_TIME = "17:00"
MOVIES_PER_RUN = 5   # প্রতি session এ কতটা
# ──────────────────────────────────────────────────────

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG  = "https://image.tmdb.org/t/p/w500"


def load_posted() -> set:
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_posted(posted: set):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted), f)


def fetch_movies_by_language(language: str, page: int = 1) -> list:
    """
    Hollywood → original_language = en
    Bollywood → original_language = hi
    """
    url = f"{TMDB_BASE}/discover/movie"
    params = {
        "api_key":             TMDB_API_KEY,
        "language":            "en-US",
        "with_original_language": language,
        "sort_by":             "popularity.desc",
        "vote_count.gte":      100,
        "page":                page,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])


def get_genres(genre_ids: list) -> str:
    genre_map = {
        28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
        80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
        14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
        9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
        53: "Thriller", 10752: "War", 37: "Western"
    }
    names = [genre_map.get(gid, "") for gid in genre_ids[:3]]
    return " • ".join(filter(None, names)) or "N/A"


def build_caption(movie: dict, category: str) -> str:
    title    = movie.get("title", "Unknown")
    year     = movie.get("release_date", "")[:4] or "N/A"
    rating   = round(movie.get("vote_average", 0), 1)
    votes    = movie.get("vote_count", 0)
    overview = movie.get("overview", "No description available.")
    genres   = get_genres(movie.get("genre_ids", []))
    lang     = movie.get("original_language", "").upper()

    if len(overview) > 300:
        overview = overview[:297] + "…"

    if rating >= 7.5:
        stars = "⭐⭐⭐⭐⭐"
    elif rating >= 6.5:
        stars = "⭐⭐⭐⭐"
    elif rating >= 5.5:
        stars = "⭐⭐⭐"
    else:
        stars = "⭐⭐"

    # Category badge
    if category == "hollywood":
        badge = "🎥 Hollywood"
    else:
        badge = "🎞️ Bollywood"

    caption = (
        f"{badge}\n"
        f"🎬 <b>{title}</b> ({year})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{stars} <b>{rating}/10</b>  •  🗳 {votes:,} votes\n"
        f"🎭 <b>Genre:</b> {genres}\n"
        f"🌐 <b>Language:</b> {lang}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 <b>Story:</b>\n{overview}\n\n"
        f"🍿 <i>Stream for free on ZyFlix!</i>"
    )
    return caption


def build_keyboard(movie: dict) -> InlineKeyboardMarkup:
    movie_id  = movie.get("id")
    watch_url = f"{WATCH_BASE}/?type=movie&id={movie_id}"
    buttons = [
        [InlineKeyboardButton("🎬  ▶  WATCH NOW  ◀  🎬", url=watch_url)],
        [InlineKeyboardButton("🌐  ZyFlix — Free Movie Streaming", url=WATCH_BASE)],
    ]
    return InlineKeyboardMarkup(buttons)


async def post_movie(bot: Bot, movie: dict, category: str):
    poster_path = movie.get("poster_path")
    caption     = build_caption(movie, category)
    keyboard    = build_keyboard(movie)

    if poster_path:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=f"{TMDB_IMG}{poster_path}",
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    else:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    print(f"  ✅ Posted: {movie['title']} ({movie.get('release_date','')[:4]})")


async def run_session(lang_code: str, category: str):
    """
    lang_code : 'en' = Hollywood | 'hi' = Bollywood
    category  : 'hollywood' | 'bollywood'
    """
    label = "🎥 Hollywood" if category == "hollywood" else "🎞️ Bollywood"
    print(f"\n{'='*45}")
    print(f"🚀 ZyFlix Bot — {label} Session — {date.today()}")
    print(f"{'='*45}")

    bot    = Bot(token=BOT_TOKEN)
    posted = load_posted()
    count  = 0
    page   = 1

    while count < MOVIES_PER_RUN:
        movies = fetch_movies_by_language(lang_code, page=page)
        if not movies:
            break

        for movie in movies:
            if count >= MOVIES_PER_RUN:
                break

            movie_id = str(movie["id"])

            if movie_id in posted:
                print(f"  ⏭️  Already posted: {movie['title']}")
                continue

            if not movie.get("poster_path"):
                print(f"  ⚠️  No poster: {movie['title']}")
                continue

            try:
                await post_movie(bot, movie, category)
                posted.add(movie_id)
                save_posted(posted)
                count += 1

                # Posts এর মাঝে gap — spam avoid
                if count < MOVIES_PER_RUN:
                    gap = 10 * 60   # ১০ মিনিট gap
                    print(f"  ⏳ Waiting 10 min before next post...")
                    await asyncio.sleep(gap)

            except Exception as e:
                print(f"  ❌ Error [{movie['title']}]: {e}")
                await asyncio.sleep(5)

        page += 1

    print(f"\n  🎉 {label} done — Posted {count} movies.")
    print(f"{'='*45}\n")


# ─── Job wrappers ──────────────────────────────────────
def hollywood_job():
    asyncio.run(run_session("en", "hollywood"))

def bollywood_job():
    asyncio.run(run_session("hi", "bollywood"))
# ──────────────────────────────────────────────────────


if __name__ == "__main__":
    print("🤖 ZyFlix Telegram Bot Starting...")
    print(f"📢 Channel     : {CHANNEL_ID}")
    print(f"🌐 Website     : {WATCH_BASE}")
    print(f"🎥 Hollywood   : {MOVIES_PER_RUN} movies at {HOLLYWOOD_TIME} BD time")
    print(f"🎞️ Bollywood   : {MOVIES_PER_RUN} movies at {BOLLYWOOD_TIME} BD time")
    print(f"⏳ Gap between : 10 minutes per post\n")

    # Scheduler
    schedule.every().day.at(HOLLYWOOD_TIME).do(hollywood_job)
    schedule.every().day.at(BOLLYWOOD_TIME).do(bollywood_job)

    print(f"✅ Scheduler active. Waiting for scheduled times...")
    print(f"   Hollywood → {HOLLYWOOD_TIME}  |  Bollywood → {BOLLYWOOD_TIME}\n")

    # Test করতে চাইলে নিচের দুটো uncomment করো:
    # hollywood_job()
    # bollywood_job()

    while True:
        schedule.run_pending()
        time.sleep(30)

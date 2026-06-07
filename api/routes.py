"""API-ендпоінти: /search і /generate-queries."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from core.api_client import YouTubeClient
from core.scoring import build_rows, add_scores, top_keywords
from core.query_gen import generate as gen_queries
from core.ai_query_gen import generate_ai

from .schemas import (
    SearchRequest, SearchResponse, VideoResult,
    GenerateRequest, GenerateResponse,
)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search_videos(req: SearchRequest):
    """Головний ендпоінт — пошук вірусних відео."""
    try:
        client = YouTubeClient(req.api_key)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    published_after = None
    if req.days:
        published_after = (datetime.now(timezone.utc) - timedelta(days=req.days)) \
            .isoformat().replace("+00:00", "Z")

    # Пакетний пошук: збираємо ID з усіх запитів
    all_ids = []
    for q in req.queries:
        try:
            ids = client.search(
                q, req.max_per_query, req.region, published_after,
                "video", req.language, req.duration,
            )
            all_ids.extend(ids)
        except Exception:
            continue  # один невдалий запит не повинен ламати весь пошук

    uniq_ids = list(dict.fromkeys(all_ids))
    if not uniq_ids:
        return SearchResponse(total=0, videos=[], top_keywords=[])

    # Дотягуємо повні дані батчами
    try:
        videos = client.videos_details(uniq_ids)
        ch_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v]
        channels = client.channels_stats(ch_ids)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"YouTube API error: {e}")

    rows = build_rows(videos, channels)

    # Фільтри
    rows = [r for r in rows if r["views"] >= req.min_views]
    if req.max_subs > 0:
        rows = [r for r in rows if r["subscribers"] <= req.max_subs]
    if req.max_channel_videos > 0:
        rows = [r for r in rows if r["channel_video_count"] <= req.max_channel_videos]
    if req.target == "shorts":
        rows = [r for r in rows if r["is_short"]]
    elif req.target == "video":
        rows = [r for r in rows if not r["is_short"]]

    if not rows:
        return SearchResponse(total=0, videos=[], top_keywords=[])

    # Нормалізуємо ваги
    total_w = req.weight_velocity + req.weight_outreach + req.weight_engagement or 1.0
    weights = {
        "velocity": req.weight_velocity / total_w,
        "outreach": req.weight_outreach / total_w,
        "engagement": req.weight_engagement / total_w,
    }

    rows = add_scores(rows, weights)
    keywords = top_keywords(rows, top_n=20)

    return SearchResponse(
        total=len(rows),
        videos=[VideoResult(**r) for r in rows],
        top_keywords=keywords,
    )


@router.post("/generate-queries", response_model=GenerateResponse)
def generate_queries(req: GenerateRequest):
    """Генератор запитів. Спершу пробує AI (Gemini), якщо не вийшло — шаблони."""
    try:
        queries = generate_ai(req.keyword, req.count, req.language)
        if queries:
            return GenerateResponse(queries=queries)
    except Exception as e:
        print(f"AI generation failed, fallback to templates: {e}")

    # Запасний варіант — шаблонний генератор
    queries = gen_queries(req.keyword, req.count, req.language)
    return GenerateResponse(queries=queries)


@router.get("/health")
def health():
    """Перевірка, що сервер живий."""
    return {"status": "ok"}

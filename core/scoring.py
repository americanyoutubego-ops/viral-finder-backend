import re
from collections import Counter
from datetime import datetime, timezone

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    _LANGDETECT = True
except Exception:
    _LANGDETECT = False


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "is", "are", "was", "be", "this", "that", "it", "as", "by", "from",
    "how", "what", "why", "you", "your", "my", "i", "we", "they", "не", "на",
    "в", "і", "та", "що", "як", "це", "з", "до", "по", "за", "vs", "ai",
}


def _parse_duration(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _age_days(published_at):
    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    return max(delta.total_seconds() / 86400, 0.01)


def _detect_lang(title):
    if not _LANGDETECT or not title or len(title) < 10:
        return ""
    try:
        return detect(title)
    except Exception:
        return ""


def build_rows(videos, channels):
    """Перетворює сирі відповіді YouTube API на список словників з потрібними даними."""
    rows = []
    for v in videos:
        stats = v.get("statistics", {})
        snip = v.get("snippet", {})
        cd = v.get("contentDetails", {})
        ch_id = snip.get("channelId", "")
        ch = channels.get(ch_id, {})
        ch_stats = ch.get("statistics", {})

        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        subs = int(ch_stats.get("subscriberCount", 0))
        ch_video_count = int(ch_stats.get("videoCount", 0))
        age = _age_days(snip.get("publishedAt", datetime.now(timezone.utc).isoformat()))
        dur = _parse_duration(cd.get("duration", ""))

        thumbs = snip.get("thumbnails", {})
        thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
        title = snip.get("title", "")

        rows.append({
            "thumbnail": thumb,
            "title": title,
            "channel": snip.get("channelTitle", ""),
            "channel_id": ch_id,
            "channel_video_count": ch_video_count,
            "lang": _detect_lang(title),
            "video_id": v.get("id", ""),
            "link": f"https://youtube.com/watch?v={v.get('id', '')}",
            "published_at": snip.get("publishedAt", ""),
            "views": views,
            "likes": likes,
            "comments": comments,
            "subscribers": subs,
            "age_days": round(age, 1),
            "duration_s": dur,
            "is_short": 0 < dur <= 60,
            "velocity": views / age,
            "outreach": views / max(subs, 1),
            "engagement": (likes + comments) / max(views, 1),
        })
    return rows


def _pct_rank(values):
    """Percentile rank без pandas — чистий Python."""
    if not values:
        return []
    sorted_vals = sorted(values)
    if sorted_vals[0] == sorted_vals[-1]:
        return [0.0] * len(values)
    n = len(values)
    rank_map = {}
    for i, v in enumerate(sorted_vals):
        if v not in rank_map:
            rank_map[v] = (i + 1) / n
    return [rank_map[v] for v in values]


def add_scores(rows, weights):
    """Додає до кожного рядка viral_score та badge."""
    if not rows:
        return rows

    velocities = [r["velocity"] for r in rows]
    outreaches = [r["outreach"] for r in rows]
    engagements = [r["engagement"] for r in rows]

    n_vel = _pct_rank(velocities)
    n_out = _pct_rank(outreaches)
    n_eng = _pct_rank(engagements)

    for i, r in enumerate(rows):
        r["n_velocity"] = round(n_vel[i], 3)
        r["n_outreach"] = round(n_out[i], 3)
        r["n_engagement"] = round(n_eng[i], 3)
        score = (weights["velocity"] * n_vel[i]
                 + weights["outreach"] * n_out[i]
                 + weights["engagement"] * n_eng[i])
        r["viral_score"] = round(score, 3)
        r["badge"] = _pick_badge(r)

    rows.sort(key=lambda x: x["viral_score"], reverse=True)
    return rows


def _pick_badge(row):
    score = row.get("viral_score", 0)
    outreach = row.get("outreach", 0)
    age = row.get("age_days", 999)
    velocity = row.get("velocity", 0)
    subs = row.get("subscribers", 0)

    if score >= 0.85:
        return "VIRAL"
    if outreach >= 30 and subs < 50000:
        return "GEM"
    if age <= 7 and velocity >= 10000:
        return "FAST"
    if score >= 0.6:
        return "RISING"
    return ""


def top_keywords(rows, top_n=15):
    if not rows:
        return []
    words = []
    for r in rows:
        title = r.get("title", "")
        for w in re.findall(r"\w+", str(title).lower()):
            if len(w) > 2 and w not in STOPWORDS and not w.isdigit():
                words.append(w)
    common = Counter(words).most_common(top_n)
    return [{"word": w, "count": c} for w, c in common]
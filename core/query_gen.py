"""Локальний генератор пошукових запитів — без OpenAI."""
import random
from datetime import datetime

TEMPLATES_EN = [
    "{kw}", "{kw} tutorial", "{kw} for beginners", "{kw} explained",
    "best {kw}", "best {kw} {year}", "how to use {kw}",
    "{kw} tips and tricks", "{kw} review", "free {kw}",
    "{kw} vs", "top {kw} tools", "{kw} masterclass",
    "{kw} mistakes", "{kw} crash course", "{kw} guide",
    "ultimate {kw} guide", "{kw} secrets", "{kw} workflow",
    "{kw} step by step", "easy {kw}", "{kw} hacks",
    "I tried {kw}", "{kw} {year} update", "is {kw} worth it",
]

TEMPLATES_UK = [
    "{kw}", "{kw} українською", "як користуватися {kw}",
    "{kw} для початківців", "огляд {kw}", "{kw} безкоштовно",
    "топ {kw}", "{kw} {year}", "як зробити {kw}",
    "{kw} інструкція", "найкращі {kw}", "{kw} поради",
]

TEMPLATES_RU = [
    "{kw}", "{kw} обзор", "{kw} для начинающих",
    "как пользоваться {kw}", "лучшие {kw}", "{kw} {year}",
    "{kw} гайд", "{kw} бесплатно", "топ {kw}",
    "как сделать {kw}", "{kw} ошибки", "{kw} советы",
]


def generate(keyword, count=20, language="en"):
    keyword = keyword.strip()
    if not keyword:
        return []

    year = datetime.now().year
    if language == "uk":
        templates = TEMPLATES_UK + TEMPLATES_EN[:8]
    elif language == "ru":
        templates = TEMPLATES_RU + TEMPLATES_EN[:8]
    else:
        templates = TEMPLATES_EN

    queries = []
    seen = set()
    for tpl in templates:
        q = tpl.format(kw=keyword, year=year).strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            queries.append(q)

    if len(queries) > count:
        base = queries[0]
        rest = queries[1:]
        random.shuffle(rest)
        queries = [base] + rest[:count - 1]

    return queries[:count]
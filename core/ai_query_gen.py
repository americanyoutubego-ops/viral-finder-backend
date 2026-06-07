"""Генератор пошукових запитів через Google Gemini (справжній AI)."""
import os
import json
import re

from google import genai


def generate_ai(keyword, count=20, language="en"):
    """Генерує осмислені пошукові запити навколо теми через Gemini.
    Якщо ключа немає або сталась помилка — кидає виняток (обробляється вище)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не заданий на сервері")

    keyword = keyword.strip()
    if not keyword:
        return []

    lang_names = {
        "en": "English", "uk": "Ukrainian", "ru": "Russian",
        "es": "Spanish", "de": "German", "fr": "French",
        "pt": "Portuguese", "tr": "Turkish",
    }
    lang_name = lang_names.get(language, "English")

    prompt = f"""You are a YouTube SEO expert. Generate exactly {count} diverse YouTube search queries for the topic: "{keyword}".

Rules:
- Write all queries in {lang_name}.
- Make them varied: tutorials, questions, comparisons, trends, "how to", problems, beginner and advanced, current year topics.
- Each query should be something real people actually search on YouTube.
- Keep each query short (2-6 words), natural, no quotes.
- Think about what content creators in this niche make videos about.

Return ONLY a JSON array of strings, nothing else. Example format:
["query one", "query two", "query three"]"""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = (response.text or "").strip()

    # Прибираємо markdown-обгортку ```json ... ``` якщо є
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        queries = json.loads(text)
        if isinstance(queries, list):
            # лишаємо тільки рядки, прибираємо порожні
            result = [str(q).strip() for q in queries if str(q).strip()]
            return result[:count]
    except (json.JSONDecodeError, ValueError):
        pass

    # Якщо JSON не розпарсився — пробуємо витягти рядки по лініях
    lines = [line.strip().strip('",-•').strip() for line in text.split("\n")]
    result = [line for line in lines if line and len(line) > 2]
    return result[:count]

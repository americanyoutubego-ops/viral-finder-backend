"""Опис форматів даних — що приходить від користувача, що повертаємо."""
from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    """Те, що приходить від користувача при пошуку."""
    api_key: str = Field(..., description="YouTube Data API key користувача")
    queries: list[str] = Field(..., min_length=1, description="Список пошукових запитів")
    target: str = Field("all", description="all | video | shorts")
    region: str = Field("UA")
    language: Optional[str] = None
    duration: Optional[str] = None  # short | medium | long
    days: int = Field(90, ge=0, le=365)
    max_per_query: int = Field(25, ge=10, le=50)
    min_views: int = Field(1000, ge=0)
    max_subs: int = Field(0, ge=0, description="0 = без обмежень")
    max_channel_videos: int = Field(0, ge=0, description="0 = без обмежень")
    weight_velocity: float = Field(0.5, ge=0, le=1)
    weight_outreach: float = Field(0.35, ge=0, le=1)
    weight_engagement: float = Field(0.15, ge=0, le=1)


class VideoResult(BaseModel):
    """Одне відео в результатах."""
    video_id: str
    title: str
    channel: str
    channel_id: str
    channel_video_count: int
    link: str
    thumbnail: str
    lang: str
    published_at: str
    views: int
    likes: int
    comments: int
    subscribers: int
    age_days: float
    duration_s: int
    is_short: bool
    velocity: float
    outreach: float
    engagement: float
    viral_score: float
    badge: str


class SearchResponse(BaseModel):
    """Те, що повертаємо користувачу."""
    total: int
    videos: list[VideoResult]
    top_keywords: list[dict]


class GenerateRequest(BaseModel):
    keyword: str
    count: int = Field(20, ge=1, le=50)
    language: str = "en"


class GenerateResponse(BaseModel):
    queries: list[str]
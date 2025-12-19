"""
해외 미스테리 자동화 파이프라인

영어 위키백과에서 미스테리 사건 수집 → Opus 대본 각색 → 영상 생성

사용법:
    from scripts.mystery_pipeline import run_mystery_pipeline
    result = run_mystery_pipeline(sheet_id, service)
"""

from .run import run_mystery_pipeline
from .collector import collect_mystery_article, search_wikipedia_en
from .config import (
    MYSTERY_CATEGORIES,
    MYSTERY_SHEET_NAME,
    MYSTERY_TTS_VOICE,
    MYSTERY_VIDEO_LENGTH_MINUTES,
)

__all__ = [
    "run_mystery_pipeline",
    "collect_mystery_article",
    "search_wikipedia_en",
    "MYSTERY_CATEGORIES",
    "MYSTERY_SHEET_NAME",
    "MYSTERY_TTS_VOICE",
    "MYSTERY_VIDEO_LENGTH_MINUTES",
]

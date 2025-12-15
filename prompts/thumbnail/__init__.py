# -*- coding: utf-8 -*-
"""일반 영상용 웹툰 썸네일 시스템"""

from .general import (
    GENERAL_THUMBNAIL_RULES,
    CHANNEL_PRESETS,
    GEMINI_RENDER_TEMPLATE,
    determine_face_visibility,
    get_channel_preset,
    build_gemini_prompt,
    get_gpt_thumbnail_prompt,
)

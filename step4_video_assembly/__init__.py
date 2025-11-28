"""
Step 4: Video Assembly
Creatomate API를 사용한 영상 조립 모듈
"""

from .video_builder import build_video, build_step4_input
from .call_creatomate import create_video_clip, get_render_status
from .timeline_merger import merge_clips, build_timeline, calculate_total_duration

__all__ = [
    "build_video",
    "build_step4_input",
    "create_video_clip",
    "get_render_status",
    "merge_clips",
    "build_timeline",
    "calculate_total_duration"
]

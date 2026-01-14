"""
한국사 파이프라인 - 영상 렌더링 모듈 (FFmpeg 기반)

- 이미지 + 오디오 합성
- SRT → ASS 자막 변환 및 하드코딩
- 공통 렌더러 유틸리티 사용
"""

import os
from typing import Dict, Any, List

# 공통 렌더링 유틸리티
from scripts.common.renderer_utils import (
    srt_to_ass,
    render_video as _render_video,
    render_multi_image_video as _render_multi_image_video,
    mix_audio_with_bgm,
)
from scripts.common.audio_utils import get_audio_duration


# 파이프라인별 로그 접두사
LOG_PREFIX = "[HISTORY-RENDERER]"


def render_video(
    audio_path: str,
    image_path: str,
    output_path: str,
    srt_path: str = None,
    resolution: str = "1920x1080",
    fps: int = 30,
) -> Dict[str, Any]:
    """단일 이미지 + 오디오로 영상 생성"""
    return _render_video(
        audio_path=audio_path,
        image_path=image_path,
        output_path=output_path,
        srt_path=srt_path,
        resolution=resolution,
        fps=fps,
        style_preset="history",
        log_prefix=LOG_PREFIX,
    )


def render_multi_image_video(
    audio_path: str,
    image_paths: List[str],
    output_path: str,
    srt_path: str = None,
    resolution: str = "1920x1080",
    fps: int = 30,
    timestamps: List[int] = None,
) -> Dict[str, Any]:
    """여러 이미지 + 오디오로 영상 생성 (타임스탬프 기반 또는 균등 분배)"""
    return _render_multi_image_video(
        audio_path=audio_path,
        image_paths=image_paths,
        output_path=output_path,
        srt_path=srt_path,
        resolution=resolution,
        fps=fps,
        style_preset="history",
        log_prefix=LOG_PREFIX,
        use_absolute_path=True,
        timestamps=timestamps,
    )


# 기본 BGM 경로
DEFAULT_BGM_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "static", "audio", "bgm", "epic_01.mp3"
)

# mix_audio_with_bgm 함수 re-export (workers.py에서 사용)
__all__ = [
    'render_video',
    'render_multi_image_video',
    'mix_audio_with_bgm',
    'DEFAULT_BGM_PATH',
]


if __name__ == "__main__":
    print("history_pipeline/renderer.py 로드 완료")

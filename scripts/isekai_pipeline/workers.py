"""
혈영 이세계편 - Workers (실행 API)

창작 작업은 Claude가 대화에서 직접 수행.
이 모듈은 실행만 담당:
- TTS 생성 (Gemini/Google TTS)
- 이미지 생성 (Gemini Imagen)
- 영상 렌더링 (FFmpeg)
- YouTube 업로드
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config import (
    OUTPUT_BASE,
    TTS_CONFIG,
    IMAGE_STYLE,
)


# 출력 디렉토리
AUDIO_DIR = os.path.join(OUTPUT_BASE, "audio")
SUBTITLE_DIR = os.path.join(OUTPUT_BASE, "subtitles")
VIDEO_DIR = os.path.join(OUTPUT_BASE, "videos")
SCRIPT_DIR = os.path.join(OUTPUT_BASE, "scripts")
IMAGE_DIR = os.path.join(OUTPUT_BASE, "images")
BRIEF_DIR = os.path.join(OUTPUT_BASE, "briefs")


def ensure_directories():
    """출력 디렉토리 생성"""
    for d in [AUDIO_DIR, SUBTITLE_DIR, VIDEO_DIR, SCRIPT_DIR, IMAGE_DIR, BRIEF_DIR]:
        os.makedirs(d, exist_ok=True)


# =====================================================
# TTS Worker
# =====================================================

def generate_tts(
    episode: int,
    script: str,
    voice: str = None,
    speed: float = None,
) -> Dict[str, Any]:
    """
    TTS 생성 (Gemini/Google TTS)

    Args:
        episode: 에피소드 번호
        script: 대본 텍스트
        voice: 음성 (기본: config의 TTS_CONFIG)
        speed: 속도 (기본: config의 TTS_CONFIG)

    Returns:
        {
            "ok": True,
            "audio_path": "outputs/isekai/audio/ep001.mp3",
            "srt_path": "outputs/isekai/subtitles/ep001.srt",
            "duration": 3000.5
        }
    """
    ensure_directories()

    voice = voice or TTS_CONFIG.get("voice", "chirp3:Charon")
    speed = speed or TTS_CONFIG.get("speed", 0.95)

    try:
        # wuxia_pipeline의 TTS 모듈 재사용
        from scripts.wuxia_pipeline.multi_voice_tts import (
            generate_multi_voice_tts_simple,
            generate_srt_from_timeline,
        )

        episode_id = f"ep{episode:03d}"
        tts_result = generate_multi_voice_tts_simple(
            text=script,
            output_dir=AUDIO_DIR,
            episode_id=episode_id,
            voice=voice,
            speed=speed,
        )

        if tts_result.get("ok"):
            # SRT 생성
            srt_path = os.path.join(SUBTITLE_DIR, f"{episode_id}.srt")
            if tts_result.get("timeline"):
                generate_srt_from_timeline(tts_result["timeline"], srt_path)
                tts_result["srt_path"] = srt_path

            tts_result["audio_path"] = tts_result.get("merged_audio")

        return tts_result

    except ImportError:
        return {"ok": False, "error": "TTS 모듈 없음 (wuxia_pipeline 필요)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# Image Worker
# =====================================================

def generate_image(
    episode: int,
    prompt: str,
    negative_prompt: str = None,
    style: str = "realistic",
    ratio: str = "16:9",
) -> Dict[str, Any]:
    """
    이미지 생성 (Gemini Imagen)

    Args:
        episode: 에피소드 번호
        prompt: 이미지 프롬프트 (영문)
        negative_prompt: 제외할 요소
        style: 스타일 (realistic, artistic, etc.)
        ratio: 비율 (16:9, 1:1, 9:16)

    Returns:
        {
            "ok": True,
            "image_path": "outputs/isekai/images/ep001_main.png"
        }
    """
    ensure_directories()

    try:
        api_url = os.getenv(
            "IMAGE_API_URL",
            "http://localhost:5059/api/ai-tools/image-generate"
        )

        # 기본 negative prompt 추가
        full_negative = IMAGE_STYLE.get("negative_prompt", "")
        if negative_prompt:
            full_negative = f"{full_negative}, {negative_prompt}"

        response = requests.post(
            api_url,
            json={
                "prompt": prompt,
                "negative_prompt": full_negative,
                "style": style,
                "ratio": ratio,
            },
            timeout=120,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                image_url = data.get("image_url")
                image_path = os.path.join(IMAGE_DIR, f"ep{episode:03d}_main.png")

                # 이미지 다운로드
                img_response = requests.get(image_url, timeout=60)
                if img_response.status_code == 200:
                    with open(image_path, "wb") as f:
                        f.write(img_response.content)
                    return {"ok": True, "image_path": image_path}

        return {"ok": False, "error": "이미지 생성 실패"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# Video Worker
# =====================================================

def render_video(
    episode: int,
    audio_path: str,
    image_path: str,
    srt_path: str = None,
    bgm_mood: str = "calm",
) -> Dict[str, Any]:
    """
    영상 렌더링 (FFmpeg)

    Args:
        episode: 에피소드 번호
        audio_path: TTS 오디오 파일 경로
        image_path: 배경 이미지 경로
        srt_path: 자막 파일 경로 (선택)
        bgm_mood: BGM 분위기

    Returns:
        {
            "ok": True,
            "video_path": "outputs/isekai/videos/ep001.mp4",
            "duration": 3000.5
        }
    """
    ensure_directories()

    try:
        # wuxia_pipeline의 렌더러 재사용 시도
        from scripts.wuxia_pipeline.renderer import render_episode_video

        episode_id = f"ep{episode:03d}"
        video_path = os.path.join(VIDEO_DIR, f"{episode_id}.mp4")

        result = render_episode_video(
            audio_path=audio_path,
            image_path=image_path,
            srt_path=srt_path,
            output_path=video_path,
            bgm_mood=bgm_mood,
        )

        return result

    except ImportError:
        return {"ok": False, "error": "렌더러 모듈 없음 (wuxia_pipeline 필요)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# YouTube Worker
# =====================================================

def upload_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: List[str] = None,
    thumbnail_path: str = None,
    privacy_status: str = "private",
    playlist_id: str = None,
    scheduled_time: str = None,
) -> Dict[str, Any]:
    """
    YouTube 업로드

    Args:
        video_path: 영상 파일 경로
        title: 영상 제목
        description: 영상 설명
        tags: 태그 목록
        thumbnail_path: 썸네일 이미지 경로
        privacy_status: 공개 설정 (private/unlisted/public)
        playlist_id: 플레이리스트 ID
        scheduled_time: 예약 공개 시간 (ISO 8601)

    Returns:
        {
            "ok": True,
            "video_id": "abc123",
            "video_url": "https://youtube.com/watch?v=abc123"
        }
    """
    try:
        # drama_server의 YouTube 업로드 함수 사용
        from drama_server import upload_to_youtube

        result = upload_to_youtube(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags or [],
            thumbnail_path=thumbnail_path,
            privacy_status=privacy_status,
            playlist_id=playlist_id,
            scheduled_time=scheduled_time,
        )

        return result

    except ImportError:
        return {"ok": False, "error": "YouTube 모듈 없음 (drama_server 필요)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# 파일 저장 유틸리티
# =====================================================

def save_script(episode: int, title: str, script: str) -> str:
    """대본 파일 저장"""
    ensure_directories()
    script_path = os.path.join(SCRIPT_DIR, f"ep{episode:03d}_{title}.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    return script_path


def save_brief(episode: int, brief: Dict[str, Any]) -> str:
    """기획서 파일 저장"""
    ensure_directories()
    brief_path = os.path.join(BRIEF_DIR, f"ep{episode:03d}_brief.json")
    with open(brief_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    return brief_path


def save_metadata(episode: int, metadata: Dict[str, Any]) -> str:
    """메타데이터 파일 저장"""
    ensure_directories()
    meta_path = os.path.join(BRIEF_DIR, f"ep{episode:03d}_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return meta_path

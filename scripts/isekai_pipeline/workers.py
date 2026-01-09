"""
혈영 이세계편 - Workers (실행 API)

창작 작업은 Claude가 대화에서 직접 수행.
이 모듈은 실행만 담당:
- TTS 생성 (Gemini TTS)
- 이미지 생성 (Gemini Imagen)
- 영상 렌더링 (FFmpeg)
- YouTube 업로드

사용법:
    from scripts.isekai_pipeline.workers import execute_episode

    result = execute_episode(
        episode=1,
        title="이방인",
        script="대본...",
        image_prompt="무림 검객이 이세계 숲에서...",
        metadata={"title": "...", "description": "...", "tags": [...]},
        generate_video=True,
        upload=False,
    )
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

# 자체 모듈 사용
from .tts import generate_tts as _generate_tts, generate_srt
from .renderer import render_video as _render_video


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
    TTS 생성 (Gemini TTS)

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
            "duration": 900.5
        }
    """
    ensure_directories()

    voice = voice or TTS_CONFIG.get("voice", "Charon")
    episode_id = f"ep{episode:03d}"

    try:
        # 자체 TTS 모듈 사용
        # tts.py의 generate_tts 시그니처:
        # generate_tts(episode_id, script, output_dir, voice, speed)
        result = _generate_tts(
            episode_id=episode_id,
            script=script,
            output_dir=AUDIO_DIR,
            voice=voice,
            speed=speed or 1.0,
        )

        return result

    except Exception as e:
        return {"ok": False, "error": str(e)}


# =====================================================
# Image Worker
# =====================================================

def _generate_image_via_image_module(prompt: str, ratio: str = "16:9") -> Dict[str, Any]:
    """image 패키지를 통한 이미지 생성 (OpenRouter → Gemini)"""
    import base64

    # 비율 → size 문자열 변환
    size_map = {
        '16:9': "1280x720",
        '9:16': "720x1280",
        '1:1': "1024x1024",
        '4:3': "1024x768"
    }
    size = size_map.get(ratio, "1280x720")

    try:
        # image 패키지 사용 (OpenRouter 경유 Gemini)
        from image import generate_image as image_generate, generate_image_base64, GEMINI_FLASH

        # 먼저 generate_image 시도 (URL 반환)
        result = image_generate(prompt=prompt, size=size, model=GEMINI_FLASH)

        if result.get("ok") and result.get("image_url"):
            # URL에서 이미지 다운로드
            image_url = result["image_url"]
            if image_url.startswith("/"):
                # 로컬 파일 경로
                local_path = f"/home/user/my_page_v2{image_url}"
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        image_data = f.read()
                    return {"ok": True, "image_data": image_data}
            else:
                # HTTP URL
                resp = requests.get(image_url, timeout=30)
                if resp.status_code == 200:
                    return {"ok": True, "image_data": resp.content}

            return {"ok": False, "error": f"이미지 다운로드 실패: {image_url}"}

        # fallback: generate_image_base64
        width, height = map(int, size.split("x"))
        image_b64 = generate_image_base64(prompt=prompt, width=width, height=height, model=GEMINI_FLASH)

        if image_b64:
            image_data = base64.b64decode(image_b64)
            return {"ok": True, "image_data": image_data}

        return {"ok": False, "error": result.get("error", "이미지 생성 실패")}

    except ImportError as e:
        return {"ok": False, "error": f"image 모듈 import 실패: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def generate_image(
    episode: int,
    prompt: str,
    scene_index: int = 0,
    negative_prompt: str = None,
    style: str = "realistic",
    ratio: str = "16:9",
) -> Dict[str, Any]:
    """
    이미지 생성 (Gemini Imagen 직접 호출)

    Args:
        episode: 에피소드 번호
        prompt: 이미지 프롬프트 (영문)
        scene_index: 씬 인덱스 (0 = 메인/썸네일)
        negative_prompt: 제외할 요소
        style: 스타일 (realistic, artistic, etc.)
        ratio: 비율 (16:9, 1:1, 9:16)

    Returns:
        {
            "ok": True,
            "image_path": "outputs/isekai/images/ep001_scene_01.png"
        }
    """
    ensure_directories()

    # 기본 negative prompt 추가
    full_negative = IMAGE_STYLE.get("negative_prompt", "")
    if negative_prompt:
        full_negative = f"{full_negative}, {negative_prompt}"

    # 이세계 스타일 추가
    base_prompt = IMAGE_STYLE.get("base_prompt", "")
    full_prompt = f"{base_prompt}, {prompt}" if base_prompt else prompt

    # 스타일 suffix 추가
    style_prompts = {
        'realistic': 'photorealistic, high detail, professional photography',
        'webtoon': 'Korean webtoon style, manhwa art style, clean lines, vibrant colors',
        'cinematic': 'cinematic lighting, movie scene, dramatic atmosphere, 4K',
        'illustration': 'digital illustration, artistic, colorful, detailed artwork',
    }
    style_suffix = style_prompts.get(style, '')
    if style_suffix:
        full_prompt = f"{full_prompt}, {style_suffix}"

    # negative prompt를 프롬프트에 추가 (Imagen은 negative prompt 미지원)
    if full_negative:
        full_prompt = f"{full_prompt}. Avoid: {full_negative}"

    print(f"[ISEKAI-IMAGE] 생성 중: scene_{scene_index}")

    result = _generate_image_via_image_module(full_prompt, ratio)

    if not result.get("ok"):
        return result

    # 파일명 생성
    if scene_index == 0:
        filename = f"ep{episode:03d}_thumbnail.png"
    else:
        filename = f"ep{episode:03d}_scene_{scene_index:02d}.png"

    image_path = os.path.join(IMAGE_DIR, filename)

    # 이미지 저장
    with open(image_path, "wb") as f:
        f.write(result["image_data"])

    print(f"[ISEKAI-IMAGE] 저장: {image_path}")
    return {"ok": True, "image_path": image_path}


def generate_images_batch(
    episode: int,
    prompts: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    여러 이미지 일괄 생성

    Args:
        episode: 에피소드 번호
        prompts: [{"prompt": "...", "scene_index": 1}, ...]

    Returns:
        {
            "ok": True,
            "images": [{"scene_index": 1, "path": "..."}, ...],
            "failed": []
        }
    """
    results = {"ok": True, "images": [], "failed": []}

    for item in prompts:
        prompt = item.get("prompt", "")
        scene_index = item.get("scene_index", 0)

        result = generate_image(
            episode=episode,
            prompt=prompt,
            scene_index=scene_index,
        )

        if result.get("ok"):
            results["images"].append({
                "scene_index": scene_index,
                "path": result["image_path"],
            })
        else:
            results["failed"].append({
                "scene_index": scene_index,
                "error": result.get("error"),
            })

    if results["failed"]:
        results["ok"] = len(results["images"]) > 0

    return results


# =====================================================
# Video Worker
# =====================================================

def render_video(
    episode: int,
    audio_path: str,
    image_path: str,
    srt_path: str = None,
    bgm_mood: str = "calm",
    bgm_volume: float = 0.10,
    scene_timeline: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    영상 렌더링 (FFmpeg) + BGM 믹싱

    Args:
        episode: 에피소드 번호
        audio_path: TTS 오디오 파일 경로
        image_path: 배경 이미지 경로
        srt_path: 자막 파일 경로 (선택)
        bgm_mood: 단일 BGM 분위기 (scene_timeline 없을 때 사용)
        bgm_volume: BGM 볼륨 (0.0~1.0, 기본 0.10 = 10%)
        scene_timeline: 씬별 타임라인 (TTS generate_tts에서 반환)
            [{"name": "...", "bgm": "nostalgic", "start": 0.0, "end": 120.0}]

    Returns:
        {
            "ok": True,
            "video_path": "outputs/isekai/videos/ep001.mp4",
            "duration": 900.5
        }
    """
    ensure_directories()

    try:
        episode_id = f"ep{episode:03d}"
        video_path = os.path.join(VIDEO_DIR, f"{episode_id}.mp4")

        # 1단계: 기본 영상 렌더링 (이미지 + TTS)
        result = _render_video(
            audio_path=audio_path,
            image_path=image_path,
            output_path=video_path,
            srt_path=srt_path,
        )

        if not result.get("ok"):
            return result

        # 2단계: BGM 믹싱
        if scene_timeline and len(scene_timeline) > 1:
            # 씬별 BGM 믹싱
            bgm_result = _mix_scene_bgm(video_path, scene_timeline, bgm_volume)
            if bgm_result.get("ok"):
                print(f"[ISEKAI-VIDEO] 씬별 BGM 믹싱 완료: {len(scene_timeline)}개 씬")
            else:
                print(f"[ISEKAI-VIDEO] 씬별 BGM 실패: {bgm_result.get('error')}, 단일 BGM으로 폴백")
                # 폴백: 단일 BGM
                if bgm_mood:
                    _mix_bgm(video_path, bgm_mood, bgm_volume)
        elif bgm_mood:
            # 단일 BGM 믹싱
            bgm_result = _mix_bgm(video_path, bgm_mood, bgm_volume)
            if bgm_result.get("ok"):
                print(f"[ISEKAI-VIDEO] BGM 믹싱 완료: {bgm_mood}")
            else:
                print(f"[ISEKAI-VIDEO] BGM 믹싱 실패: {bgm_result.get('error', 'unknown')}, BGM 없이 진행")

        return result

    except Exception as e:
        return {"ok": False, "error": str(e)}


def _mix_bgm(video_path: str, bgm_mood: str, bgm_volume: float = 0.10) -> Dict[str, Any]:
    """
    영상에 BGM 믹싱

    Args:
        video_path: 영상 파일 경로
        bgm_mood: BGM 분위기
        bgm_volume: BGM 볼륨

    Returns:
        {"ok": True} 또는 {"ok": False, "error": "..."}
    """
    try:
        # drama_server의 BGM 함수 사용
        from drama_server import _get_bgm_file, _mix_bgm_with_video

        bgm_file = _get_bgm_file(bgm_mood)
        if not bgm_file:
            return {"ok": False, "error": f"BGM 파일 없음: {bgm_mood}"}

        # 임시 출력 파일
        bgm_output_path = video_path.replace(".mp4", "_bgm.mp4")

        success = _mix_bgm_with_video(video_path, bgm_file, bgm_output_path, bgm_volume)

        if success and os.path.exists(bgm_output_path):
            try:
                # 원본 교체
                os.replace(bgm_output_path, video_path)
                return {"ok": True}
            except OSError as e:
                # 교체 실패 시 임시 파일 정리
                if os.path.exists(bgm_output_path):
                    os.remove(bgm_output_path)
                return {"ok": False, "error": f"파일 교체 실패: {e}"}
        else:
            return {"ok": False, "error": "BGM 믹싱 실패"}

    except ImportError as e:
        return {"ok": False, "error": f"drama_server import 실패: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _mix_scene_bgm(
    video_path: str,
    scene_timeline: List[Dict[str, Any]],
    bgm_volume: float = 0.10
) -> Dict[str, Any]:
    """
    씬별로 다른 BGM을 믹싱

    Args:
        video_path: 영상 파일 경로
        scene_timeline: 씬 타임라인
            [{"name": "...", "bgm": "nostalgic", "start": 0.0, "end": 120.0}]
        bgm_volume: BGM 볼륨

    Returns:
        {"ok": True} 또는 {"ok": False, "error": "..."}
    """
    try:
        import subprocess
        import tempfile
        from drama_server import _get_bgm_file

        # 씬별 BGM 파일 수집
        scene_bgms = []
        for scene in scene_timeline:
            bgm_mood = scene.get("bgm", "calm")
            bgm_file = _get_bgm_file(bgm_mood)
            if not bgm_file:
                # 폴백: calm
                bgm_file = _get_bgm_file("calm")
            scene_bgms.append({
                "file": bgm_file,
                "start": scene["start"],
                "end": scene["end"],
                "mood": bgm_mood,
            })

        if not scene_bgms:
            return {"ok": False, "error": "BGM 파일 없음"}

        # FFmpeg 복잡 필터로 씬별 BGM 믹싱
        # 각 BGM을 해당 구간에만 재생하도록 설정
        filter_parts = []
        input_args = ["-i", video_path]

        for i, bgm in enumerate(scene_bgms):
            input_args.extend(["-i", bgm["file"]])
            start = bgm["start"]
            duration = bgm["end"] - bgm["start"]

            # BGM을 해당 구간에 맞게 자르고 페이드 적용
            # 페이드 인 2초, 페이드 아웃 3초
            fade_in = min(2.0, duration * 0.1)
            fade_out = min(3.0, duration * 0.1)
            fade_out_start = max(0, duration - fade_out)

            filter_parts.append(
                f"[{i+1}:a]atrim=0:{duration},asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out},"
                f"volume={bgm_volume},adelay={int(start*1000)}|{int(start*1000)}[bgm{i}]"
            )

        # 모든 BGM 믹스
        bgm_mix_inputs = "".join(f"[bgm{i}]" for i in range(len(scene_bgms)))
        filter_parts.append(
            f"{bgm_mix_inputs}amix=inputs={len(scene_bgms)}:duration=longest[bgm_mixed]"
        )

        # 원본 오디오와 BGM 믹스
        filter_parts.append(
            "[0:a][bgm_mixed]amix=inputs=2:duration=first:weights=1 0.5[aout]"
        )

        filter_complex = ";".join(filter_parts)

        # 임시 출력 파일
        output_path = video_path.replace(".mp4", "_scene_bgm.mp4")

        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode == 0 and os.path.exists(output_path):
            os.replace(output_path, video_path)
            print(f"[ISEKAI-VIDEO] 씬별 BGM 믹싱 완료")
            for bgm in scene_bgms:
                print(f"  - {bgm['start']:.1f}s~{bgm['end']:.1f}s: {bgm['mood']}")
            return {"ok": True}
        else:
            error_msg = result.stderr[:500] if result.stderr else "unknown"
            return {"ok": False, "error": f"FFmpeg 실패: {error_msg}"}

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
    channel_id: str = None,
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
        channel_id: YouTube 채널 ID (없으면 config에서 가져옴)

    Returns:
        {
            "ok": True,
            "video_id": "abc123",
            "video_url": "https://youtube.com/watch?v=abc123"
        }
    """
    try:
        from drama_server import upload_to_youtube
        from .config import SERIES_INFO

        # channel_id가 없으면 config에서 가져옴
        yt_channel_id = channel_id or SERIES_INFO.get("youtube_channel_id", "")
        yt_playlist_id = playlist_id or SERIES_INFO.get("playlist_id", "")

        if not yt_channel_id:
            return {"ok": False, "error": "채널 ID가 없습니다. ISEKAI_CHANNEL_ID 환경변수를 설정하세요."}

        result = upload_to_youtube(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags or [],
            channel_id=yt_channel_id,
            thumbnail_path=thumbnail_path,
            privacy_status=privacy_status,
            playlist_id=yt_playlist_id if yt_playlist_id else None,
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
    print(f"[ISEKAI] 대본 저장: {script_path}")
    return script_path


def save_brief(episode: int, brief: Dict[str, Any]) -> str:
    """기획서 파일 저장"""
    ensure_directories()
    brief_path = os.path.join(BRIEF_DIR, f"ep{episode:03d}_brief.json")
    with open(brief_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    print(f"[ISEKAI] 기획서 저장: {brief_path}")
    return brief_path


def save_metadata(episode: int, metadata: Dict[str, Any]) -> str:
    """메타데이터 파일 저장"""
    ensure_directories()
    meta_path = os.path.join(BRIEF_DIR, f"ep{episode:03d}_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"[ISEKAI] 메타데이터 저장: {meta_path}")
    return meta_path


# =====================================================
# 에피소드 실행 (통합)
# =====================================================

def execute_episode(
    episode: int,
    title: str,
    script: str,
    image_prompts: List[Dict[str, str]] = None,
    metadata: Dict[str, Any] = None,
    brief: Dict[str, Any] = None,
    bgm_mood: str = "epic",
    bgm_volume: float = 0.10,
    generate_video: bool = False,
    upload: bool = False,
    privacy_status: str = "private",
) -> Dict[str, Any]:
    """
    에피소드 실행 (Workers 호출)

    Claude가 대화에서 생성한 창작물을 받아서 실제 파일 생성

    Args:
        episode: 에피소드 번호 (1~60)
        title: 에피소드 제목
        script: 대본 (12,000~15,000자)
        image_prompts: 이미지 프롬프트 목록 [{"prompt": "...", "scene_index": 1}, ...]
        metadata: YouTube 메타데이터 (title, description, tags)
        brief: 기획서 (선택)
        bgm_mood: BGM 분위기 (epic, tense, calm, etc.)
        bgm_volume: BGM 볼륨 (0.0~1.0, 기본 0.10 = 10%)
        generate_video: 영상 렌더링 여부
        upload: YouTube 업로드 여부
        privacy_status: 공개 설정

    Returns:
        {
            "ok": True,
            "episode": 1,
            "title": "이방인",
            "script_path": "...",
            "audio_path": "...",
            "image_paths": [...],
            "video_path": "...",
            "youtube_url": "..."
        }
    """
    print(f"\n{'='*60}")
    print(f"[ISEKAI] EP{episode:03d} '{title}' 실행 시작")
    print(f"{'='*60}")

    result = {
        "ok": False,
        "episode": episode,
        "title": title,
    }

    # 1. 대본 저장
    print(f"\n[ISEKAI] 1. 대본 저장...")
    script_path = save_script(episode, title, script)
    result["script_path"] = script_path
    print(f"    ✓ {len(script):,}자 저장 완료")

    # 2. 기획서 저장 (선택)
    if brief:
        print(f"\n[ISEKAI] 2. 기획서 저장...")
        brief_path = save_brief(episode, brief)
        result["brief_path"] = brief_path

    # 3. 메타데이터 저장
    if metadata:
        print(f"\n[ISEKAI] 3. 메타데이터 저장...")
        meta_path = save_metadata(episode, metadata)
        result["metadata_path"] = meta_path

    # 4. TTS 생성
    print(f"\n[ISEKAI] 4. TTS 생성 중...")
    tts_result = generate_tts(episode, script)
    if not tts_result.get("ok"):
        result["error"] = f"TTS 실패: {tts_result.get('error')}"
        print(f"    ✗ TTS 실패: {result['error']}")
        return result

    result["audio_path"] = tts_result.get("audio_path")
    result["srt_path"] = tts_result.get("srt_path")
    result["duration"] = tts_result.get("duration")
    print(f"    ✓ TTS 완료: {result.get('duration', 0):.1f}초")

    # 5. 이미지 생성
    print(f"\n[ISEKAI] 5. 이미지 생성 중...")
    if image_prompts:
        img_result = generate_images_batch(episode, image_prompts)
        result["image_paths"] = [img["path"] for img in img_result.get("images", [])]
        print(f"    ✓ {len(result['image_paths'])}개 이미지 생성")
        if img_result.get("failed"):
            print(f"    ⚠ {len(img_result['failed'])}개 실패")
    else:
        result["image_paths"] = []
        print(f"    - 이미지 프롬프트 없음 (스킵)")

    # 6. 영상 렌더링 (선택)
    if generate_video and result.get("image_paths"):
        print(f"\n[ISEKAI] 6. 영상 렌더링 중...")
        video_result = render_video(
            episode=episode,
            audio_path=result["audio_path"],
            image_path=result["image_paths"][0],  # 첫 번째 이미지 사용
            srt_path=result.get("srt_path"),
            bgm_mood=bgm_mood,
            bgm_volume=bgm_volume,
        )
        if video_result.get("ok"):
            result["video_path"] = video_result.get("video_path")
            print(f"    ✓ 영상 생성 완료: {result['video_path']}")
        else:
            print(f"    ✗ 영상 생성 실패: {video_result.get('error')}")

    # 7. YouTube 업로드 (선택)
    if upload and result.get("video_path") and metadata:
        print(f"\n[ISEKAI] 7. YouTube 업로드 중...")
        yt_result = upload_youtube(
            video_path=result["video_path"],
            title=metadata.get("title", f"혈영 이세계편 EP{episode:03d}"),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            thumbnail_path=result["image_paths"][0] if result.get("image_paths") else None,
            privacy_status=privacy_status,
        )
        if yt_result.get("ok"):
            result["youtube_url"] = yt_result.get("video_url")
            print(f"    ✓ 업로드 완료: {result['youtube_url']}")
        else:
            print(f"    ✗ 업로드 실패: {yt_result.get('error')}")

    result["ok"] = True
    print(f"\n{'='*60}")
    print(f"[ISEKAI] EP{episode:03d} '{title}' 실행 완료")
    print(f"{'='*60}")

    return result

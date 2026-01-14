"""
한국사 파이프라인 - 렌더링 Skill

/history-render 커맨드에서 호출
TTS 실제 길이 기반으로 이미지 타임스탬프 자동 계산
"""

import os
import json
import importlib
from typing import Dict, Any, List, Optional
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from .workers import (
    generate_tts,
    generate_images_batch,
    render_video,
    save_script,
    save_metadata,
    ensure_directories,
    AUDIO_DIR,
    SUBTITLE_DIR,
    OUTPUT_BASE,
)
from scripts.common.audio_utils import get_audio_duration


def calculate_image_timestamps(duration_sec: float) -> List[int]:
    """
    TTS 실제 길이 기반으로 이미지 타임스탬프 계산

    규칙:
    - 0~1분: 10초마다 (6장)
    - 1~5분: 30초마다 (8장)
    - 5~10분: 40초마다 (8장)
    - 10분~끝: 60초마다

    Returns:
        타임스탬프 목록 (초 단위)
    """
    timestamps = []

    # 0~1분: 10초마다
    t = 0
    while t < min(60, duration_sec):
        timestamps.append(t)
        t += 10

    # 1~5분: 30초마다
    t = 60
    while t < min(300, duration_sec):
        timestamps.append(t)
        t += 30

    # 5~10분: 40초마다
    t = 300
    while t < min(600, duration_sec):
        timestamps.append(t)
        t += 40

    # 10분~끝: 60초마다
    t = 600
    while t < duration_sec:
        timestamps.append(t)
        t += 60

    return sorted(set(timestamps))


def generate_image_prompts_from_script(
    script: str,
    timestamps: List[int],
    title: str,
    episode_info: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    대본과 타임스탬프를 기반으로 이미지 프롬프트 생성

    현재는 기본 프롬프트 사용, 추후 GPT 연동 가능
    """
    # 대본을 파트별로 분리 (---로 구분)
    parts = script.split("---")
    total_chars = len(script)

    prompts = []

    for i, ts in enumerate(timestamps):
        # 타임스탬프 위치에 해당하는 대본 부분 추정
        char_position = int((ts / max(timestamps[-1], 1)) * total_chars) if timestamps else 0

        # 기본 프롬프트 (스타일 통일)
        base_style = "Korean webtoon style illustration, warm colors, Studio Ghibli meets modern illustration, 16:9"

        if i == 0:
            # 썸네일/인트로
            prompt = f"{base_style}, {title}, dramatic opening scene, historical Korean setting"
        elif ts < 60:
            # 초반 훅
            prompt = f"{base_style}, {title}, engaging introduction, historical atmosphere"
        elif ts < 300:
            # 배경 설명
            prompt = f"{base_style}, historical background, Korean dynasty scene, informative visual"
        elif ts < 600:
            # 본론
            prompt = f"{base_style}, main narrative scene, historical drama, key moment"
        else:
            # 클라이맥스/마무리
            prompt = f"{base_style}, climactic scene, emotional moment, historical conclusion"

        prompts.append({
            "timestamp_sec": ts,
            "timestamp_display": f"{ts // 60}:{ts % 60:02d}",
            "prompt": prompt,
            "scene_index": i,
        })

    return prompts


def load_episode_module(episode_id: str) -> Optional[Any]:
    """에피소드 모듈 동적 로드"""
    # ep021 → ep021_gwangjong 등의 파일 찾기
    episodes_dir = os.path.join(os.path.dirname(__file__), "episodes")

    for filename in os.listdir(episodes_dir):
        if filename.startswith(episode_id) and filename.endswith(".py"):
            if "image_prompts" in filename:
                continue  # image_prompts 파일 제외

            module_name = filename[:-3]  # .py 제거
            try:
                module = importlib.import_module(f".episodes.{module_name}", package="scripts.history_pipeline")
                return module
            except Exception as e:
                print(f"[RENDER-SKILL] 모듈 로드 실패: {module_name} - {e}")

    return None


def load_image_prompts_module(episode_id: str) -> Optional[Any]:
    """이미지 프롬프트 모듈 로드 (있는 경우)"""
    try:
        module = importlib.import_module(f".episodes.{episode_id}_image_prompts", package="scripts.history_pipeline")
        return module
    except Exception:
        return None


def render_episode(
    episode_id: str,
    skip_tts: bool = False,
    skip_images: bool = False,
    use_existing_prompts: bool = True,
) -> Dict[str, Any]:
    """
    에피소드 렌더링 실행

    Args:
        episode_id: 에피소드 ID (예: "ep021")
        skip_tts: 기존 TTS 재사용
        skip_images: 기존 이미지 재사용
        use_existing_prompts: 기존 image_prompts.py 사용 (False면 자동 생성)

    Returns:
        실행 결과
    """
    print(f"\n{'='*60}")
    print(f"[RENDER-SKILL] {episode_id} 렌더링 시작")
    print(f"{'='*60}")

    ensure_directories()

    result = {
        "ok": False,
        "episode_id": episode_id,
        "started_at": datetime.now().isoformat(),
    }

    # 1. 에피소드 모듈 로드
    print(f"\n[STEP 1] 에피소드 모듈 로드...")
    module = load_episode_module(episode_id)
    if not module:
        result["error"] = f"에피소드 모듈을 찾을 수 없습니다: {episode_id}"
        return result

    script = getattr(module, "SCRIPT", "")
    episode_info = getattr(module, "EPISODE_INFO", {})
    metadata = getattr(module, "METADATA", {})
    scene_moods_raw = getattr(module, "SCENE_MOODS", None)  # 씬별 BGM 무드
    title = episode_info.get("title", metadata.get("title", episode_id))

    print(f"    제목: {title}")
    print(f"    대본: {len(script):,}자")
    result["title"] = title

    # 2. TTS 생성 또는 기존 파일 사용
    print(f"\n[STEP 2] TTS 처리...")
    audio_path = os.path.join(AUDIO_DIR, f"{episode_id}.mp3")
    srt_path = os.path.join(SUBTITLE_DIR, f"{episode_id}.srt")

    if skip_tts and os.path.exists(audio_path):
        print(f"    기존 TTS 재사용: {audio_path}")
        duration = get_audio_duration(audio_path)
    else:
        print(f"    TTS 생성 중...")
        tts_result = generate_tts(episode_id, script)
        if not tts_result.get("ok"):
            result["error"] = f"TTS 실패: {tts_result.get('error')}"
            return result
        audio_path = tts_result.get("audio_path")
        srt_path = tts_result.get("srt_path")
        duration = tts_result.get("duration", 0)

    print(f"    TTS 길이: {duration:.1f}초 ({duration/60:.1f}분)")
    result["audio_path"] = audio_path
    result["srt_path"] = srt_path
    result["duration"] = duration

    # 3. 이미지 타임스탬프 계산
    print(f"\n[STEP 3] 이미지 타임스탬프 계산...")
    timestamps = calculate_image_timestamps(duration)
    print(f"    TTS 실제 길이 기반: {len(timestamps)}개 타임스탬프")

    # 3-1. 씬별 BGM 무드 계산 (SCENE_MOODS가 있는 경우)
    scene_moods = None
    if scene_moods_raw:
        # 대본 섹션 분리 (---로 구분)
        sections = script.split("---")
        num_sections = len(sections)
        section_duration = duration / num_sections if num_sections > 0 else duration

        scene_moods = []
        for i, mood in enumerate(scene_moods_raw):
            if i >= num_sections:
                break
            start = i * section_duration
            end = (i + 1) * section_duration
            scene_moods.append({
                "start": start,
                "end": end,
                "mood": mood,
            })
        print(f"    씬별 BGM: {len(scene_moods)}개 세그먼트")

    # 4. 이미지 프롬프트 준비
    print(f"\n[STEP 4] 이미지 프롬프트 준비...")

    if use_existing_prompts:
        prompts_module = load_image_prompts_module(episode_id)
        if prompts_module and hasattr(prompts_module, "IMAGE_PROMPTS"):
            raw_prompts = prompts_module.IMAGE_PROMPTS
            print(f"    기존 프롬프트 파일 사용: {len(raw_prompts)}개")

            # 타임스탬프 재매핑 (실제 TTS 길이에 맞춤)
            image_prompts = []
            for i, ts in enumerate(timestamps):
                if i < len(raw_prompts):
                    prompt_data = raw_prompts[i]
                    image_prompts.append({
                        "timestamp_sec": ts,
                        "prompt": prompt_data.get("prompt", ""),
                        "scene_index": i,
                    })
                else:
                    # 프롬프트가 부족하면 마지막 것 재사용
                    image_prompts.append({
                        "timestamp_sec": ts,
                        "prompt": raw_prompts[-1].get("prompt", "") if raw_prompts else "",
                        "scene_index": i,
                    })
        else:
            print(f"    기존 프롬프트 없음, 자동 생성...")
            image_prompts = generate_image_prompts_from_script(script, timestamps, title, episode_info)
    else:
        print(f"    프롬프트 자동 생성...")
        image_prompts = generate_image_prompts_from_script(script, timestamps, title, episode_info)

    print(f"    최종 이미지 프롬프트: {len(image_prompts)}개")

    # 5. 이미지 생성
    print(f"\n[STEP 5] 이미지 생성...")
    if skip_images:
        # 기존 이미지 경로 수집
        from .workers import IMAGE_DIR
        image_paths = []
        for i in range(len(image_prompts)):
            if i == 0:
                path = os.path.join(IMAGE_DIR, f"{episode_id}_thumbnail.png")
            else:
                path = os.path.join(IMAGE_DIR, f"{episode_id}_scene_{i:02d}.png")
            if os.path.exists(path):
                image_paths.append(path)
        print(f"    기존 이미지 재사용: {len(image_paths)}개")
    else:
        img_result = generate_images_batch(episode_id, image_prompts)
        image_paths = [img["path"] for img in img_result.get("images", [])]
        print(f"    생성 완료: {len(image_paths)}개")
        if img_result.get("failed"):
            print(f"    실패: {len(img_result['failed'])}개")

    result["image_paths"] = image_paths

    # 6. 영상 렌더링
    print(f"\n[STEP 6] 영상 렌더링...")
    video_result = render_video(
        episode_id=episode_id,
        audio_path=audio_path,
        image_paths=image_paths,
        srt_path=srt_path,
        bgm_mood="epic",  # scene_moods가 없을 때 기본값
        voice_volume=6.0,  # TTS 볼륨 6배
        bgm_volume=0.10,
        timestamps=timestamps,  # 타임스탬프 기반 이미지 배치
        scene_moods=scene_moods,  # 씬별 BGM (있는 경우)
    )

    if not video_result.get("ok"):
        result["error"] = f"렌더링 실패: {video_result.get('error')}"
        return result

    result["video_path"] = video_result.get("video_path")
    print(f"    영상 저장: {result['video_path']}")

    # 7. 상태 업데이트
    print(f"\n[STEP 7] 상태 업데이트...")
    status_dir = os.path.join(OUTPUT_BASE, "status")
    os.makedirs(status_dir, exist_ok=True)
    status_path = os.path.join(status_dir, f"{episode_id}_status.json")

    status = {
        "episode_id": episode_id,
        "title": title,
        "status": "completed",
        "started_at": result["started_at"],
        "completed_at": datetime.now().isoformat(),
        "duration_sec": duration,
        "image_count": len(image_paths),
        "output_files": {
            "script": f"outputs/history/scripts/{episode_id}_{title}.txt",
            "audio": audio_path,
            "srt": srt_path,
            "video": result.get("video_path"),
        }
    }

    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"    상태 저장: {status_path}")

    result["ok"] = True
    result["completed_at"] = datetime.now().isoformat()

    print(f"\n{'='*60}")
    print(f"[RENDER-SKILL] {episode_id} 완료!")
    print(f"{'='*60}")

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ep_id = sys.argv[1]
        result = render_episode(ep_id, skip_tts=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("사용법: python render_skill.py ep021")

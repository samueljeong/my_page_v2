#!/usr/bin/env python3
"""
에피소드 파일에서 영상 생성 파이프라인 직접 실행

사용법:
    python run_episode.py 21                    # EP021 실행 (영상만)
    python run_episode.py 21 --upload           # EP021 실행 + YouTube 업로드
    python run_episode.py 21 --no-video         # TTS + 이미지만 (영상 렌더링 스킵)
"""

import os
import sys
import argparse
import importlib.util

# 프로젝트 루트를 path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# .env 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))


def load_episode_module(episode_num: int, suffix: str = None):
    """에피소드 모듈 동적 로드"""
    import glob
    episode_id = f"ep{episode_num:03d}"
    episodes_dir = os.path.join(os.path.dirname(__file__), "episodes")

    if suffix:
        pattern = os.path.join(episodes_dir, f"{episode_id}_{suffix}.py")
        files = glob.glob(pattern)
        if files:
            spec = importlib.util.spec_from_file_location(f"{episode_id}_{suffix}", files[0])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    else:
        # 메인 파일 찾기 (image_prompts, data 제외)
        pattern = os.path.join(episodes_dir, f"{episode_id}_*.py")
        files = glob.glob(pattern)
        for f in files:
            if "image_prompts" not in f and "data" not in f:
                spec = importlib.util.spec_from_file_location(f"{episode_id}_main", f)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        return None


def run_episode(episode_num: int, generate_video: bool = True, upload: bool = False,
                privacy_status: str = "private"):
    """에피소드 실행"""
    from scripts.history_pipeline.workers import execute_episode

    print(f"\n{'='*60}")
    print(f"EP{episode_num:03d} 파이프라인 시작")
    print(f"{'='*60}")

    # 메인 모듈 로드
    main_module = load_episode_module(episode_num)
    if not main_module:
        print(f"ERROR: ep{episode_num:03d} 에피소드 파일을 찾을 수 없습니다")
        return None

    # 이미지 프롬프트 모듈 로드
    img_module = load_episode_module(episode_num, "image_prompts")

    # 데이터 추출
    episode_info = getattr(main_module, 'EPISODE_INFO', {})
    script = getattr(main_module, 'SCRIPT', '')
    metadata = getattr(main_module, 'METADATA', {})
    brief = getattr(main_module, 'BRIEF', None)
    image_prompts = getattr(img_module, 'IMAGE_PROMPTS', []) if img_module else []

    episode_id = f"ep{episode_num:03d}"
    title = episode_info.get('title', f'한국사 {episode_num}화')

    print(f"\n에피소드: {episode_id}")
    print(f"제목: {title}")
    print(f"대본: {len(script):,}자")
    print(f"이미지 프롬프트: {len(image_prompts)}개")
    print(f"영상 생성: {generate_video}")
    print(f"업로드: {upload}")

    if not script:
        print("ERROR: 대본(SCRIPT)이 없습니다")
        return None

    # 실행
    result = execute_episode(
        episode_id=episode_id,
        title=title,
        script=script,
        image_prompts=image_prompts,
        metadata=metadata,
        brief=brief,
        generate_video=generate_video,
        upload=upload,
        privacy_status=privacy_status,
    )

    print(f"\n{'='*60}")
    if result.get("ok"):
        print("SUCCESS")
        print(f"  음성: {result.get('audio_path')}")
        print(f"  영상: {result.get('video_path')}")
        if result.get('youtube_url'):
            print(f"  YouTube: {result.get('youtube_url')}")
    else:
        print(f"FAILED: {result.get('error')}")
    print(f"{'='*60}\n")

    return result


def main():
    parser = argparse.ArgumentParser(description='한국사 에피소드 영상 생성')
    parser.add_argument('episode', type=int, help='에피소드 번호 (예: 21)')
    parser.add_argument('--upload', action='store_true', help='YouTube 업로드')
    parser.add_argument('--no-video', action='store_true', help='영상 렌더링 스킵')
    parser.add_argument('--public', action='store_true', help='공개 상태로 업로드')

    args = parser.parse_args()

    privacy_status = "public" if args.public else "private"
    generate_video = not args.no_video

    result = run_episode(
        episode_num=args.episode,
        generate_video=generate_video,
        upload=args.upload,
        privacy_status=privacy_status,
    )

    sys.exit(0 if result and result.get("ok") else 1)


if __name__ == "__main__":
    main()

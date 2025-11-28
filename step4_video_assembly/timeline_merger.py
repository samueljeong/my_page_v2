"""
Timeline Merger for Step 4
개별 클립들을 타임라인에 병합하여 최종 영상 생성
"""

from typing import Dict, Any, List, Optional
import os


# 기본 트랜지션 설정
DEFAULT_FADE_DURATION = 0.5  # 페이드 전환 시간(초)


def merge_clips(
    clips: List[Dict[str, Any]],
    output_filename: str,
    fade_duration: float = DEFAULT_FADE_DURATION,
    background_music_path: Optional[str] = None
) -> Optional[str]:
    """
    개별 클립들을 하나의 영상으로 병합

    Args:
        clips: 클립 정보 리스트 [{"clip_path": str, "duration": float}, ...]
        output_filename: 출력 파일명
        fade_duration: 클립 간 페이드 전환 시간(초)
        background_music_path: 배경음악 파일 경로 (선택사항)

    Returns:
        생성된 파일 경로 또는 None (실패 시)
    """
    if not clips:
        print("[ERROR] No clips to merge")
        return None

    # 타임라인 구성
    timeline = build_timeline(clips, fade_duration)

    # 총 길이 계산
    total_duration = calculate_total_duration(clips, fade_duration)

    print(f"[MERGE] Merging {len(clips)} clips")
    print(f"[MERGE] Total duration: {total_duration:.1f}s")
    print(f"[MERGE] Fade duration: {fade_duration}s")
    print(f"[MERGE] Output: {output_filename}")

    if background_music_path:
        print(f"[MERGE] BGM: {background_music_path}")

    # TODO: 실제 병합 구현 (FFmpeg 또는 Creatomate API)
    # ffmpeg -i clip1.mp4 -i clip2.mp4 ... -filter_complex "[0:v][1:v]xfade=..." output.mp4

    # 임시: 파일 경로만 반환
    return output_filename


def build_timeline(
    clips: List[Dict[str, Any]],
    fade_duration: float = DEFAULT_FADE_DURATION
) -> List[Dict[str, Any]]:
    """
    클립들의 타임라인 구성

    Args:
        clips: 클립 정보 리스트
        fade_duration: 페이드 전환 시간(초)

    Returns:
        타임라인 정보 리스트
    """
    timeline = []
    current_time = 0.0

    for idx, clip in enumerate(clips):
        clip_path = clip.get("clip_path", "")
        duration = clip.get("duration", 0.0)

        entry = {
            "index": idx + 1,
            "clip_path": clip_path,
            "start_time": current_time,
            "end_time": current_time + duration,
            "duration": duration
        }

        # 마지막 클립이 아니면 페이드 전환 정보 추가
        if idx < len(clips) - 1:
            entry["transition"] = {
                "type": "fade",
                "duration": fade_duration,
                "start_at": current_time + duration - fade_duration
            }

        timeline.append(entry)

        # 다음 클립 시작 시간 (페이드 겹침 고려)
        if idx < len(clips) - 1:
            current_time += duration - fade_duration
        else:
            current_time += duration

    return timeline


def calculate_total_duration(
    clips: List[Dict[str, Any]],
    fade_duration: float = DEFAULT_FADE_DURATION
) -> float:
    """
    전체 영상 길이 계산 (페이드 겹침 고려)

    Args:
        clips: 클립 정보 리스트
        fade_duration: 페이드 전환 시간(초)

    Returns:
        총 길이(초)
    """
    if not clips:
        return 0.0

    total = sum(clip.get("duration", 0.0) for clip in clips)

    # 페이드 겹침만큼 감소 (클립 수 - 1)
    overlap_count = len(clips) - 1
    total -= fade_duration * overlap_count

    return max(0.0, total)


if __name__ == "__main__":
    # 테스트
    test_clips = [
        {"clip_path": "output/clip1.mp4", "duration": 24.5},
        {"clip_path": "output/clip2.mp4", "duration": 30.0},
        {"clip_path": "output/clip3.mp4", "duration": 20.0}
    ]

    timeline = build_timeline(test_clips)
    print("=== Timeline ===")
    for entry in timeline:
        print(f"  Clip {entry['index']}: {entry['start_time']:.1f}s - {entry['end_time']:.1f}s")
        if "transition" in entry:
            print(f"    Transition: {entry['transition']}")

    total = calculate_total_duration(test_clips)
    print(f"\nTotal duration: {total:.1f}s")

    result = merge_clips(test_clips, "output/final_video.mp4")
    print(f"\nResult: {result}")

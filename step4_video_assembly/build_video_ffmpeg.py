"""
FFmpeg-based Video Builder for Step 4
Creatomate 대신 FFmpeg를 사용한 무료 영상 조립

Requirements:
    - FFmpeg 설치 필요 (apt-get install ffmpeg 또는 brew install ffmpeg)
    - 실제 이미지 파일 (outputs/images/scene1.png 등)
    - 실제 오디오 파일 (outputs/audio/scene1.mp3 등)
"""

import os
import subprocess
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional


def run_ffmpeg(cmd: List[str]) -> subprocess.CompletedProcess:
    """
    FFmpeg 명령어 실행

    Args:
        cmd: FFmpeg 명령어 리스트

    Returns:
        subprocess.CompletedProcess

    Raises:
        RuntimeError: FFmpeg 실행 실패 시
    """
    print("[FFMPEG]", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("[ERROR] FFmpeg failed:")
        print(result.stderr.decode())
        raise RuntimeError("FFmpeg error")
    return result


def check_ffmpeg_installed() -> bool:
    """FFmpeg 설치 여부 확인"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def generate_scene_clip(
    image_path: str,
    audio_path: str,
    duration: float,
    output_path: str,
    resolution: str = "1080p"
) -> Optional[str]:
    """
    하나의 씬(part 영상)을 제작

    Args:
        image_path: 장면 이미지 경로
        audio_path: 장면 오디오 경로
        duration: 클립 길이 (초)
        output_path: 출력 파일 경로
        resolution: 해상도 (720p, 1080p)

    Returns:
        생성된 파일 경로 또는 None
    """
    # 해상도 설정
    scale_map = {
        "720p": "1280:720",
        "1080p": "1920:1080",
        "4k": "3840:2160"
    }
    scale = scale_map.get(resolution, "1920:1080")

    # 파일 존재 확인
    if not os.path.exists(image_path):
        print(f"[WARNING] Image not found: {image_path}")
        return None
    if not os.path.exists(audio_path):
        print(f"[WARNING] Audio not found: {audio_path}")
        return None

    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",  # 덮어쓰기
        "-loop", "1",  # 이미지 반복
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    try:
        run_ffmpeg(cmd)
        print(f"[FFMPEG] Created clip: {output_path}")
        return output_path
    except RuntimeError:
        return None


def concat_videos(parts: List[str], output_path: str) -> Optional[str]:
    """
    여러 part 영상을 concat하여 최종 영상 생성

    Args:
        parts: 클립 파일 경로 리스트
        output_path: 최종 출력 파일 경로

    Returns:
        생성된 파일 경로 또는 None
    """
    if not parts:
        print("[ERROR] No parts to concatenate")
        return None

    # concat 리스트 파일 생성
    list_path = str(Path(output_path).parent / f"concat_{uuid.uuid4().hex}.txt")

    with open(list_path, "w") as f:
        for p in parts:
            # 절대 경로로 변환
            abs_path = os.path.abspath(p)
            f.write(f"file '{abs_path}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]

    try:
        run_ffmpeg(cmd)
        os.remove(list_path)  # 임시 파일 삭제
        print(f"[FFMPEG] Final video saved: {output_path}")
        return output_path
    except RuntimeError:
        if os.path.exists(list_path):
            os.remove(list_path)
        return None


def build_video_ffmpeg(step4_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    FFmpeg 기반 영상 제작 (기존 video_builder.build_video 대체)

    Args:
        step4_input: Step4 입력 JSON (cuts 배열 포함)

    Returns:
        Step4 출력 JSON
    """
    # FFmpeg 설치 확인
    if not check_ffmpeg_installed():
        print("[ERROR] FFmpeg is not installed!")
        print("  Install with: apt-get install ffmpeg (Linux) or brew install ffmpeg (Mac)")
        return {
            "step": "step4_video_result",
            "title": step4_input.get("title", "Untitled"),
            "video_filename": None,
            "duration_seconds": 0,
            "error": "FFmpeg not installed"
        }

    title = step4_input.get("title", "Untitled")
    cuts = step4_input.get("cuts", [])
    resolution = step4_input.get("output_resolution", "1080p")

    print(f"\n=== [FFmpeg] Building video: {title} ===")
    print(f"[FFmpeg] Cuts: {len(cuts)}, Resolution: {resolution}")

    if not cuts:
        print("[ERROR] No cuts provided")
        return {
            "step": "step4_video_result",
            "title": title,
            "video_filename": None,
            "duration_seconds": 0,
            "error": "No cuts provided"
        }

    # 출력 디렉토리
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # 각 씬별 클립 생성
    part_files = []
    total_duration = 0.0

    for i, cut in enumerate(cuts):
        cut_id = cut.get("cut_id", i + 1)
        image_path = cut.get("image_path", "")
        audio_path = cut.get("audio_path", "")
        duration = cut.get("duration_seconds", 10.0)

        part_path = os.path.join(output_dir, f"part_scene_{cut_id}.mp4")

        print(f"\n[Scene {cut_id}] Creating clip...")
        print(f"  Image: {image_path}")
        print(f"  Audio: {audio_path}")
        print(f"  Duration: {duration}s")

        result = generate_scene_clip(
            image_path=image_path,
            audio_path=audio_path,
            duration=duration,
            output_path=part_path,
            resolution=resolution
        )

        if result:
            part_files.append(result)
            total_duration += duration
        else:
            print(f"[WARNING] Failed to create clip for scene {cut_id}")

    if not part_files:
        print("[ERROR] No clips were generated")
        return {
            "step": "step4_video_result",
            "title": title,
            "video_filename": None,
            "duration_seconds": 0,
            "error": "No clips generated - check image/audio files"
        }

    # 최종 영상 concat
    sanitized_title = _sanitize_filename(title)
    final_output = os.path.join(output_dir, f"{sanitized_title}.mp4")

    print(f"\n[FFmpeg] Concatenating {len(part_files)} clips...")
    final_video = concat_videos(part_files, final_output)

    # 임시 파트 파일 정리 (선택적)
    # for part in part_files:
    #     if os.path.exists(part):
    #         os.remove(part)

    return {
        "step": "step4_video_result",
        "title": title,
        "video_filename": final_video,
        "duration_seconds": round(total_duration, 1),
        "clips_count": len(part_files),
        "resolution": resolution
    }


def build_video_from_outputs(
    step2_output_path: str,
    step3_output_path: str,
    output_video_path: str,
    images_dir: str = "outputs/images",
    audio_dir: str = "outputs/audio"
) -> Dict[str, Any]:
    """
    Step2/Step3 output 파일을 직접 읽어서 영상 생성
    (main.py 외부에서 독립적으로 호출 가능)

    Args:
        step2_output_path: step2_output.json 경로
        step3_output_path: step3_output.json 경로
        output_video_path: 최종 영상 출력 경로
        images_dir: 이미지 파일 디렉토리
        audio_dir: 오디오 파일 디렉토리

    Returns:
        결과 딕셔너리
    """
    print("=== [FFmpeg] Building video from output files ===")

    # JSON 로드
    with open(step2_output_path, "r", encoding="utf-8") as f:
        step2 = json.load(f)

    with open(step3_output_path, "r", encoding="utf-8") as f:
        step3 = json.load(f)

    title = step3.get("title", step2.get("title", "Untitled"))
    scenes = step2.get("scenes_for_image", [])
    audio_files = step3.get("audio_files", [])

    # cuts 배열 구성
    cuts = []
    for i, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", f"scene{i+1}")

        # 해당 씬의 오디오 정보 찾기
        audio_info = next(
            (a for a in audio_files if a.get("scene_id") == scene_id),
            {}
        )

        # 이미지 경로 (실제 파일이 있어야 함)
        image_path = os.path.join(images_dir, f"{scene_id}.png")
        if not os.path.exists(image_path):
            image_path = os.path.join(images_dir, f"{scene_id}.jpg")

        # 오디오 경로
        audio_path = audio_info.get("audio_filename", "")
        if audio_path and not os.path.isabs(audio_path):
            audio_path = os.path.join(os.path.dirname(step3_output_path), "..", audio_path)

        cuts.append({
            "cut_id": i + 1,
            "image_path": image_path,
            "audio_path": audio_path,
            "duration_seconds": audio_info.get("duration_seconds", 10.0)
        })

    # Step4 입력 구성
    step4_input = {
        "title": title,
        "cuts": cuts,
        "output_resolution": "1080p",
        "fps": 30
    }

    return build_video_ffmpeg(step4_input)


def _sanitize_filename(title: str) -> str:
    """파일명으로 사용할 수 없는 문자 제거"""
    import re
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
    sanitized = sanitized.replace(' ', '_')
    return sanitized[:50]


if __name__ == "__main__":
    # FFmpeg 설치 확인
    if check_ffmpeg_installed():
        print("FFmpeg is installed")
    else:
        print("FFmpeg is NOT installed")
        print("Install with:")
        print("  Linux: apt-get install ffmpeg")
        print("  Mac: brew install ffmpeg")

    # 테스트 (실제 파일이 있을 때만 동작)
    # result = build_video_from_outputs(
    #     step2_output_path="outputs/step2_output.json",
    #     step3_output_path="outputs/step3_output.json",
    #     output_video_path="outputs/final_video.mp4"
    # )
    # print(json.dumps(result, ensure_ascii=False, indent=2))

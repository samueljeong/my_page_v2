"""
렌더링 유틸리티 모듈

공통 영상 렌더링 함수들:
- srt_to_ass: SRT를 ASS 자막 형식으로 변환
- render_video: 단일 이미지 + 오디오 영상 생성
- render_multi_image_video: 다중 이미지 + 오디오 영상 생성
- mix_audio_with_bgm: 음성과 BGM 믹싱
"""

import os
import re
import subprocess
import tempfile
import shutil
from typing import Dict, Any, List

# 공통 오디오 유틸리티
from scripts.common.audio_utils import get_audio_duration


# 파이프라인별 자막 스타일 프리셋
SUBTITLE_STYLES = {
    "history": {
        "font_name": "NotoSansKR-Bold",
        "font_size": 80,
        "outline": 3,
        "shadow": 1,
        "margin_v": 120,
    },
    "isekai": {
        "font_name": "NotoSansKR-Bold",
        "font_size": 40,
        "outline": 1,
        "shadow": 0,
        "margin_v": 50,
    },
    "wuxia": {
        "font_name": "NotoSansKR-Bold",
        "font_size": 40,
        "outline": 1,
        "shadow": 0,
        "margin_v": 50,
    },
    "default": {
        "font_name": "NotoSansKR-Bold",
        "font_size": 60,
        "outline": 2,
        "shadow": 1,
        "margin_v": 80,
    },
}


def srt_to_ass(
    srt_content: str,
    font_name: str = None,
    font_size: int = None,
    outline: int = None,
    shadow: int = None,
    margin_v: int = None,
    style_preset: str = None,
) -> str:
    """
    SRT를 ASS 형식으로 변환

    Args:
        srt_content: SRT 자막 내용
        font_name: 폰트 이름 (기본: NotoSansKR-Bold)
        font_size: 폰트 크기 (기본: 60)
        outline: 외곽선 두께 (기본: 2)
        shadow: 그림자 (기본: 1)
        margin_v: 세로 마진 (기본: 80)
        style_preset: 스타일 프리셋 ("history", "isekai", "wuxia", "default")

    Returns:
        ASS 형식의 자막 문자열
    """
    # 스타일 프리셋 적용
    style = SUBTITLE_STYLES.get(style_preset, SUBTITLE_STYLES["default"])

    font_name = font_name or style["font_name"]
    font_size = font_size or style["font_size"]
    outline = outline if outline is not None else style["outline"]
    shadow = shadow if shadow is not None else style["shadow"]
    margin_v = margin_v or style["margin_v"]

    def srt_to_ass_time(srt_time: str) -> str:
        """SRT 타임스탬프를 ASS 형식으로 변환"""
        hours, minutes, seconds_ms = srt_time.split(':')
        seconds, milliseconds = seconds_ms.split(',')
        centiseconds = int(milliseconds) // 10
        return f"{int(hours)}:{minutes}:{seconds}.{centiseconds:02d}"

    ass_header = f"""[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&HFFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,4,{outline},{shadow},2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    ass_events = []
    srt_normalized = srt_content.replace('\r\n', '\n').strip()
    srt_blocks = re.split(r'\n\s*\n', srt_normalized)

    for block in srt_blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_match = re.match(
                r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
                lines[1]
            )
            if time_match:
                start_time = srt_to_ass_time(time_match.group(1))
                end_time = srt_to_ass_time(time_match.group(2))
                text = '\\N'.join(lines[2:])
                ass_events.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")

    return ass_header + '\n'.join(ass_events)


def render_video(
    audio_path: str,
    image_path: str,
    output_path: str,
    srt_path: str = None,
    resolution: str = "1920x1080",
    fps: int = 30,
    style_preset: str = "default",
    log_prefix: str = "[RENDERER]",
) -> Dict[str, Any]:
    """
    단일 이미지 + 오디오로 영상 생성

    Args:
        audio_path: TTS 오디오 파일 경로
        image_path: 배경 이미지 경로
        output_path: 출력 영상 경로
        srt_path: SRT 자막 파일 경로 (선택)
        resolution: 해상도 (기본: 1920x1080)
        fps: 프레임레이트 (기본: 30)
        style_preset: 자막 스타일 프리셋
        log_prefix: 로그 접두사

    Returns:
        {"ok": True, "video_path": "...", "duration": 900.5}
    """
    try:
        # FFmpeg 확인
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return {"ok": False, "error": "FFmpeg가 설치되어 있지 않습니다."}

        # 오디오 길이 확인
        duration = get_audio_duration(audio_path)
        print(f"{log_prefix} 오디오 길이: {duration:.1f}초")

        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            width, height = resolution.split('x')

            # 기본 FFmpeg 필터
            vf_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"

            # 자막 처리
            if srt_path and os.path.exists(srt_path):
                print(f"{log_prefix} 자막 파일: {srt_path}")
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()

                # SRT → ASS 변환
                ass_content = srt_to_ass(srt_content, style_preset=style_preset)
                ass_path = os.path.join(temp_dir, "subtitle.ass")
                with open(ass_path, 'w', encoding='utf-8') as f:
                    f.write(ass_content)

                # ASS 필터 추가
                escaped_ass_path = ass_path.replace('\\', '\\\\').replace(':', '\\:')
                vf_filter = f"{vf_filter},ass={escaped_ass_path}"

            # FFmpeg 명령어 구성
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', image_path,
                '-i', audio_path,
                '-vf', vf_filter,
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                '-c:a', 'aac', '-b:a', '128k',
                '-r', str(fps),
                '-shortest',
                '-pix_fmt', 'yuv420p',
                '-threads', '2',
                output_path
            ]

            print(f"{log_prefix} FFmpeg 실행 중...")
            process = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=1800
            )

            if process.returncode != 0:
                error_msg = process.stderr.decode('utf-8', errors='ignore')[:500]
                print(f"{log_prefix} FFmpeg 오류: {error_msg}")
                return {"ok": False, "error": f"FFmpeg 오류: {error_msg[:200]}"}

            # 결과 확인
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"{log_prefix} 완료: {output_path} ({file_size / 1024 / 1024:.1f}MB)")
                return {
                    "ok": True,
                    "video_path": output_path,
                    "duration": duration,
                }
            else:
                return {"ok": False, "error": "출력 파일이 생성되지 않았습니다."}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "FFmpeg 타임아웃 (30분 초과)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def render_multi_image_video(
    audio_path: str,
    image_paths: List[str],
    output_path: str,
    srt_path: str = None,
    resolution: str = "1920x1080",
    fps: int = 30,
    style_preset: str = "default",
    log_prefix: str = "[RENDERER]",
    use_absolute_path: bool = True,
    timestamps: List[int] = None,
) -> Dict[str, Any]:
    """
    여러 이미지 + 오디오로 영상 생성

    2단계 렌더링 방식:
    1. 이미지 + 오디오로 영상 생성 (자막 없이)
    2. 생성된 영상에 자막 추가

    이렇게 하면 concat demuxer의 타임스탬프 문제가 해결됨

    Args:
        audio_path: TTS 오디오 파일 경로
        image_paths: 배경 이미지 경로 목록
        output_path: 출력 영상 경로
        srt_path: SRT 자막 파일 경로 (선택)
        resolution: 해상도
        fps: 프레임레이트
        style_preset: 자막 스타일 프리셋
        log_prefix: 로그 접두사
        use_absolute_path: 이미지 경로를 절대 경로로 변환 (기본: True)
        timestamps: 이미지별 시작 시간 (초) - None이면 균등 분배

    Returns:
        {"ok": True, "video_path": "...", "duration": 900.5}
    """
    if not image_paths:
        return {"ok": False, "error": "이미지가 없습니다."}

    if len(image_paths) == 1:
        return render_video(
            audio_path=audio_path,
            image_path=image_paths[0],
            output_path=output_path,
            srt_path=srt_path,
            resolution=resolution,
            fps=fps,
            style_preset=style_preset,
            log_prefix=log_prefix,
        )

    try:
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return {"ok": False, "error": "FFmpeg가 설치되어 있지 않습니다."}

        # 오디오 길이 확인
        duration = get_audio_duration(audio_path)

        # 이미지별 duration 계산
        if timestamps and len(timestamps) == len(image_paths):
            # 타임스탬프 기반 배치
            image_durations = []
            for i in range(len(timestamps)):
                if i < len(timestamps) - 1:
                    img_dur = timestamps[i + 1] - timestamps[i]
                else:
                    img_dur = duration - timestamps[i]
                image_durations.append(max(img_dur, 0.1))  # 최소 0.1초
            print(f"{log_prefix} 오디오: {duration:.1f}초, 타임스탬프 기반 배치 ({len(image_paths)}개)")
        else:
            # 균등 분배
            image_duration = duration / len(image_paths)
            image_durations = [image_duration] * len(image_paths)
            print(f"{log_prefix} 오디오: {duration:.1f}초, 이미지당: {image_duration:.1f}초")

        with tempfile.TemporaryDirectory() as temp_dir:
            width, height = resolution.split('x')

            # 이미지 리스트 파일 생성
            list_path = os.path.join(temp_dir, "images.txt")
            with open(list_path, 'w') as f:
                for i, img_path in enumerate(image_paths):
                    path = os.path.abspath(img_path) if use_absolute_path else img_path
                    f.write(f"file '{path}'\n")
                    f.write(f"duration {image_durations[i]}\n")
                # 마지막 이미지 한번 더 (FFmpeg concat 요구사항)
                last_path = os.path.abspath(image_paths[-1]) if use_absolute_path else image_paths[-1]
                f.write(f"file '{last_path}'\n")

            # 기본 필터 (자막 없이)
            vf_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"

            # ===== 1단계: 영상 생성 (자막 없이) =====
            if srt_path and os.path.exists(srt_path):
                # 자막이 있으면 2단계 렌더링
                temp_video_path = os.path.join(temp_dir, "temp_video.mp4")
            else:
                # 자막 없으면 바로 최종 경로에
                temp_video_path = output_path

            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0', '-i', list_path,
                '-i', audio_path,
                '-t', str(duration),
                '-vf', vf_filter,
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                '-c:a', 'aac', '-b:a', '128k',
                '-r', str(fps),
                '-pix_fmt', 'yuv420p',
                '-threads', '2',
                temp_video_path
            ]

            print(f"{log_prefix} [1단계] 영상 생성 중... ({len(image_paths)}개 이미지)")

            process = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=1800
            )

            if process.returncode != 0:
                error_msg = process.stderr.decode('utf-8', errors='ignore')
                print(f"{log_prefix} FFmpeg 오류:\n{error_msg[:500]}")
                return {"ok": False, "error": f"FFmpeg 오류: {error_msg[:500]}"}

            # ===== 2단계: 자막 추가 =====
            if srt_path and os.path.exists(srt_path):
                print(f"{log_prefix} [2단계] 자막 추가 중...")

                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()

                ass_content = srt_to_ass(srt_content, style_preset=style_preset)
                ass_path = os.path.join(temp_dir, "subtitle.ass")
                with open(ass_path, 'w', encoding='utf-8') as f:
                    f.write(ass_content)

                escaped_ass_path = ass_path.replace('\\', '\\\\').replace(':', '\\:')
                sub_filter = f"ass={escaped_ass_path}"

                # 자막 추가 FFmpeg 명령어
                ffmpeg_sub_cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_video_path,
                    '-vf', sub_filter,
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                    '-c:a', 'copy',  # 오디오는 그대로 복사
                    '-threads', '2',
                    output_path
                ]

                process = subprocess.run(
                    ffmpeg_sub_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=1800
                )

                if process.returncode != 0:
                    error_msg = process.stderr.decode('utf-8', errors='ignore')
                    print(f"{log_prefix} 자막 추가 오류:\n{error_msg[:500]}")
                    return {"ok": False, "error": f"자막 추가 오류: {error_msg[:500]}"}

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"{log_prefix} 완료: {output_path} ({file_size / 1024 / 1024:.1f}MB)")
                return {
                    "ok": True,
                    "video_path": output_path,
                    "duration": duration,
                }
            else:
                return {"ok": False, "error": "출력 파일이 생성되지 않았습니다."}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "FFmpeg 타임아웃"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def mix_audio_with_multi_bgm(
    voice_path: str,
    bgm_segments: List[Dict[str, Any]],
    output_path: str,
    bgm_volume: float = 0.15,
    voice_volume: float = 1.0,
    crossfade_duration: float = 2.0,
    log_prefix: str = "[RENDERER]",
) -> Dict[str, Any]:
    """
    음성과 여러 BGM 세그먼트 믹싱 (씬별 BGM 전환)

    Args:
        voice_path: 음성 파일 경로
        bgm_segments: BGM 세그먼트 리스트
            [{"start": 0, "end": 60, "path": "epic_01.mp3"}, ...]
        output_path: 출력 파일 경로
        bgm_volume: BGM 볼륨 (0.0 ~ 1.0)
        voice_volume: 음성 볼륨 증폭
        crossfade_duration: BGM 전환 시 크로스페이드 길이 (초)
        log_prefix: 로그 접두사

    Returns:
        {"ok": True, "audio_path": "..."}
    """
    if not bgm_segments:
        return {"ok": False, "error": "BGM 세그먼트가 없습니다."}

    # 세그먼트가 1개면 단일 BGM 믹싱으로 폴백
    if len(bgm_segments) == 1:
        return mix_audio_with_bgm(
            voice_path=voice_path,
            bgm_path=bgm_segments[0]["path"],
            output_path=output_path,
            bgm_volume=bgm_volume,
            voice_volume=voice_volume,
            log_prefix=log_prefix,
        )

    try:
        voice_duration = get_audio_duration(voice_path)

        # FFmpeg 입력 파일 목록 생성
        inputs = ['-i', voice_path]  # 0번: 음성
        for i, seg in enumerate(bgm_segments):
            inputs.extend(['-stream_loop', '-1', '-i', seg["path"]])  # 1번부터: BGM들

        # 복잡한 필터 생성
        filter_parts = []
        bgm_labels = []

        for i, seg in enumerate(bgm_segments):
            input_idx = i + 1  # 0번은 음성
            start = seg["start"]
            end = seg["end"]
            duration = end - start

            # 각 BGM 세그먼트 트림 및 볼륨 조절
            label = f"bgm{i}"
            # atrim으로 시작부터 필요한 길이만큼 자르고, adelay로 시작 위치 지정
            delay_ms = int(start * 1000)

            if i == len(bgm_segments) - 1:
                # 마지막 세그먼트: 페이드 아웃 추가
                filter_parts.append(
                    f"[{input_idx}:a]atrim=0:{duration},volume={bgm_volume},"
                    f"afade=t=in:d={crossfade_duration},"
                    f"afade=t=out:st={duration-3}:d=3,"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            elif i == 0:
                # 첫 세그먼트: 페이드 아웃만
                filter_parts.append(
                    f"[{input_idx}:a]atrim=0:{duration},volume={bgm_volume},"
                    f"afade=t=out:st={duration-crossfade_duration}:d={crossfade_duration},"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            else:
                # 중간 세그먼트: 페이드 인/아웃 둘 다
                filter_parts.append(
                    f"[{input_idx}:a]atrim=0:{duration},volume={bgm_volume},"
                    f"afade=t=in:d={crossfade_duration},"
                    f"afade=t=out:st={duration-crossfade_duration}:d={crossfade_duration},"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            bgm_labels.append(f"[{label}]")

        # 음성 볼륨 조절
        filter_parts.append(f"[0:a]volume={voice_volume}[voice]")

        # 모든 BGM 믹싱
        bgm_mix_input = "".join(bgm_labels)
        filter_parts.append(f"{bgm_mix_input}amix=inputs={len(bgm_segments)}:normalize=0[bgm_mixed]")

        # 음성과 BGM 최종 믹싱
        filter_parts.append(f"[voice][bgm_mixed]amix=inputs=2:duration=first:normalize=0[out]")

        filter_complex = ";".join(filter_parts)

        ffmpeg_cmd = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-c:a', 'libmp3lame', '-b:a', '192k',
            '-t', str(voice_duration),
            output_path
        ]

        print(f"{log_prefix} 멀티 BGM 믹싱 중... ({len(bgm_segments)}개 세그먼트)")

        process = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=600
        )

        if process.returncode != 0:
            error_msg = process.stderr.decode('utf-8', errors='ignore')[:500]
            print(f"{log_prefix} 멀티 BGM 믹싱 오류: {error_msg}")
            # 실패 시 첫 번째 BGM으로 폴백
            print(f"{log_prefix} 단일 BGM으로 폴백...")
            return mix_audio_with_bgm(
                voice_path=voice_path,
                bgm_path=bgm_segments[0]["path"],
                output_path=output_path,
                bgm_volume=bgm_volume,
                voice_volume=voice_volume,
                log_prefix=log_prefix,
            )

        if os.path.exists(output_path):
            print(f"{log_prefix} 멀티 BGM 믹싱 완료")
            return {"ok": True, "audio_path": output_path}
        else:
            return {"ok": False, "error": "출력 파일 없음"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def mix_audio_with_bgm(
    voice_path: str,
    bgm_path: str,
    output_path: str,
    bgm_volume: float = 0.15,
    voice_volume: float = 1.0,
    log_prefix: str = "[RENDERER]",
) -> Dict[str, Any]:
    """
    음성과 BGM 믹싱

    Args:
        voice_path: 음성 파일 경로
        bgm_path: BGM 파일 경로
        output_path: 출력 파일 경로
        bgm_volume: BGM 볼륨 (0.0 ~ 1.0, 기본 0.15)
        voice_volume: 음성 볼륨 증폭 (1.0 = 원본, 1.5 = 1.5배)
        log_prefix: 로그 접두사

    Returns:
        {"ok": True, "audio_path": "..."}
    """
    try:
        # 음성 길이 확인
        voice_duration = get_audio_duration(voice_path)

        # FFmpeg로 믹싱 (음성 볼륨 증폭 + BGM 루프 + 페이드 아웃)
        # amix는 자동으로 볼륨을 낮추므로 normalize=0으로 비활성화
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', voice_path,
            '-stream_loop', '-1', '-i', bgm_path,
            '-filter_complex',
            f'[0:a]volume={voice_volume}[voice];'
            f'[1:a]volume={bgm_volume},afade=t=out:st={voice_duration-3}:d=3[bgm];'
            f'[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[out]',
            '-map', '[out]',
            '-c:a', 'libmp3lame', '-b:a', '192k',
            '-t', str(voice_duration),
            output_path
        ]

        print(f"{log_prefix} BGM 믹싱 중... (voice={voice_volume}x, bgm={bgm_volume*100:.0f}%)")

        process = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=300
        )

        if process.returncode != 0:
            error_msg = process.stderr.decode('utf-8', errors='ignore')[:300]
            return {"ok": False, "error": f"BGM 믹싱 오류: {error_msg}"}

        if os.path.exists(output_path):
            print(f"{log_prefix} BGM 믹싱 완료: {output_path}")
            return {"ok": True, "audio_path": output_path}
        else:
            return {"ok": False, "error": "믹싱 출력 파일 없음"}

    except Exception as e:
        return {"ok": False, "error": str(e)}

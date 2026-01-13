"""
오디오 유틸리티 모듈

공통 오디오 처리 함수들:
- get_audio_duration: 오디오 파일 길이 측정
- merge_audio_files: 여러 오디오 파일 병합
- split_into_sentences: 텍스트를 문장 단위로 분할
- generate_srt: 타임라인으로 SRT 파일 생성
- convert_wav_to_mp3: WAV/PCM을 MP3로 변환
"""

import os
import re
import subprocess
import tempfile
from typing import List, Tuple


def get_audio_duration(audio_path: str) -> float:
    """
    오디오 파일의 재생 시간(초) 반환 - WAV/MP3 모두 지원

    시도 순서:
    1. ffprobe (가장 정확, 모든 포맷)
    2. wave 모듈 (WAV 전용)
    3. mutagen (MP3 전용)
    4. 파일 크기 추정 (폴백)
    """
    if not os.path.exists(audio_path):
        return 0.0

    # 1. ffprobe 먼저 시도 (가장 정확, 모든 포맷 지원)
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True, text=True, timeout=30
        )
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0.0
        if duration > 0:
            return duration
    except Exception:
        pass

    # 2. WAV 파일 직접 파싱
    if audio_path.lower().endswith('.wav'):
        try:
            import wave
            with wave.open(audio_path, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                if rate > 0:
                    return frames / rate
        except Exception:
            pass

    # 3. mutagen으로 MP3 시도
    if audio_path.lower().endswith('.mp3'):
        try:
            from mutagen.mp3 import MP3
            audio = MP3(audio_path)
            return audio.info.length
        except Exception:
            pass

    # 4. 파일 크기로 추정 (폴백)
    try:
        file_size = os.path.getsize(audio_path)
        if file_size > 0:
            if audio_path.lower().endswith('.wav'):
                # WAV: 24kHz mono 16-bit = 48,000 bytes/sec
                return file_size / 48000.0
            else:
                # MP3: 128kbps = 16,000 bytes/sec
                return file_size / 16000.0
    except Exception:
        pass

    return 0.0


def merge_audio_files(audio_paths: List[str], output_path: str) -> bool:
    """
    여러 오디오 파일을 하나로 합침 - WAV/MP3 모두 지원

    시도 순서:
    1. pydub (가장 안정적)
    2. ffmpeg concat
    3. 바이너리 병합 (MP3만)
    """
    if not audio_paths:
        return False

    if len(audio_paths) == 1:
        src = audio_paths[0]
        # WAV to MP3 변환 필요 시
        if src.lower().endswith('.wav') and output_path.lower().endswith('.mp3'):
            try:
                subprocess.run(
                    ['ffmpeg', '-y', '-i', src, '-c:a', 'libmp3lame', '-b:a', '128k', output_path],
                    capture_output=True, timeout=120
                )
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception:
                pass
        import shutil
        shutil.copy(src, output_path)
        return True

    # 파일 포맷 확인
    has_wav = any(p.lower().endswith('.wav') for p in audio_paths)

    # 1. pydub 시도 (WAV/MP3 모두 지원)
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for path in audio_paths:
            if path.lower().endswith('.wav'):
                audio = AudioSegment.from_wav(path)
            else:
                audio = AudioSegment.from_mp3(path)
            combined += audio
        combined.export(output_path, format="mp3", bitrate="128k")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
    except Exception:
        pass

    # 2. ffmpeg 시도 (포맷 자동 감지)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")
            list_path = f.name

        subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_path,
             '-c:a', 'libmp3lame', '-b:a', '128k', output_path],
            capture_output=True, timeout=600
        )
        os.unlink(list_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
    except Exception:
        pass

    # 3. 바이너리 병합 (MP3만, WAV 혼합 시 불가)
    if not has_wav:
        try:
            with open(output_path, 'wb') as outfile:
                for path in audio_paths:
                    with open(path, 'rb') as infile:
                        outfile.write(infile.read())
            return os.path.exists(output_path)
        except Exception:
            pass

    return False


def split_into_sentences(text: str) -> List[str]:
    """텍스트를 문장 단위로 분할"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def generate_srt(timeline: List[Tuple[float, float, str]], output_path: str) -> bool:
    """
    타임라인으로 SRT 파일 생성

    Args:
        timeline: [(start_sec, end_sec, text), ...] 리스트
        output_path: 출력 SRT 파일 경로

    Returns:
        성공 여부
    """
    def format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, (start, end, text) in enumerate(timeline, 1):
                f.write(f"{i}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text}\n\n")
        return True
    except Exception:
        return False


def sec_to_srt_time(sec: float) -> str:
    """초를 SRT 타임코드로 변환 (HH:MM:SS,mmm)"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def convert_wav_to_mp3(wav_data: bytes, output_path: str) -> bool:
    """
    WAV 또는 PCM 데이터를 MP3 파일로 변환

    Args:
        wav_data: WAV 파일 데이터 또는 raw PCM 데이터
        output_path: 출력 MP3 파일 경로

    Returns:
        성공 여부
    """
    # WAV 헤더 확인 (RIFF로 시작)
    if wav_data[:4] == b'RIFF':
        # 표준 WAV 파일
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_file.write(wav_data)
                wav_path = wav_file.name

            result = subprocess.run(
                ['ffmpeg', '-y', '-i', wav_path, '-codec:a', 'libmp3lame', '-b:a', '128k', output_path],
                capture_output=True, timeout=60
            )

            os.unlink(wav_path)
            return os.path.exists(output_path)
        except Exception:
            return False
    else:
        # Raw PCM 데이터 (Gemini TTS 등)
        return convert_pcm_to_mp3(wav_data, output_path)


def convert_pcm_to_mp3(pcm_data: bytes, output_path: str, sample_rate: int = 24000) -> bool:
    """
    Raw PCM 데이터를 MP3 파일로 변환

    Args:
        pcm_data: Raw PCM 데이터 (16-bit signed little-endian, mono)
        output_path: 출력 MP3 파일 경로
        sample_rate: 샘플레이트 (기본 24kHz)

    Returns:
        성공 여부
    """
    pcm_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as pcm_file:
            pcm_file.write(pcm_data)
            pcm_path = pcm_file.name

        # raw PCM → MP3 변환
        result = subprocess.run(
            ['ffmpeg', '-y',
             '-f', 's16le',           # 16-bit signed little-endian
             '-ar', str(sample_rate), # sample rate
             '-ac', '1',              # mono
             '-i', pcm_path,
             '-codec:a', 'libmp3lame',
             '-b:a', '128k',
             output_path],
            capture_output=True, timeout=60, text=True
        )

        if pcm_path and os.path.exists(pcm_path):
            os.unlink(pcm_path)

        return result.returncode == 0 and os.path.exists(output_path)
    except Exception:
        if pcm_path and os.path.exists(pcm_path):
            os.unlink(pcm_path)
        return False

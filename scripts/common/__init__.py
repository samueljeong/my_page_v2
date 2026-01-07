"""
공통 모듈 패키지
모든 파이프라인에서 공유하는 기능들

- tts: TTS 생성 (Gemini, Chirp3, Google Cloud)
- youtube: YouTube 업로드
- image: 이미지 생성

사용법:
    from scripts.common.tts import generate_chirp3_tts, is_chirp3_voice
    from scripts.common.youtube import upload_video
"""

__version__ = '1.0.0'

# TTS 모듈
from .tts import (
    generate_gemini_tts,
    generate_chirp3_tts,
    is_gemini_voice,
    is_chirp3_voice,
    parse_gemini_voice,
    parse_chirp3_voice,
    preprocess_tts_text,
    preprocess_tts_extended,
    convert_gemini_wav_to_mp3,
)

__all__ = [
    # TTS
    'generate_gemini_tts',
    'generate_chirp3_tts',
    'is_gemini_voice',
    'is_chirp3_voice',
    'parse_gemini_voice',
    'parse_chirp3_voice',
    'preprocess_tts_text',
    'preprocess_tts_extended',
    'convert_gemini_wav_to_mp3',
]

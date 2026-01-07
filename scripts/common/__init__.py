"""
scripts/common - 파이프라인 공통 모듈

모든 파이프라인에서 공유하는 기본 클래스와 유틸리티를 제공합니다.

- tts: TTS 생성 (Gemini, Chirp3, Google Cloud)
- base_agent: 에이전트 기본 클래스
- srt_utils: SRT 자막 유틸리티

사용법:
    from scripts.common.tts import generate_chirp3_tts, is_chirp3_voice
    from scripts.common.base_agent import BaseAgent, AgentResult
"""

__version__ = '1.0.0'

# Base Agent 모듈
from .base_agent import (
    AgentStatus,
    AgentResult,
    BaseAgent,
    BudgetManager,
)

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
    # Base Agent
    "AgentStatus",
    "AgentResult",
    "BaseAgent",
    "BudgetManager",
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

# -*- coding: utf-8 -*-
"""
언어별 설정 모듈

사용법:
    from lang import get_config, detect_language

    # 언어 감지
    lang = detect_language("안녕하세요")  # 'ko'

    # 설정 가져오기
    config = get_config('ko')
    print(config.FONTS)
    print(config.SUBTITLE_MAX_CHARS)
"""

import re
from typing import Optional

# 언어별 설정 모듈 import
from . import ko
# from . import ja  # TODO: 일본어 설정 파일 생성 후 활성화
# from . import en  # TODO: 영어 설정 파일 생성 후 활성화


# 지원 언어 목록
SUPPORTED_LANGUAGES = {
    'ko': ko,
    # 'ja': ja,  # TODO
    # 'en': en,  # TODO
}


def detect_language(text: str) -> str:
    """
    텍스트의 주요 언어를 감지

    일본어 뉴스/비즈니스 대본은 한자(漢字) 비율이 높고 히라가나/가타카나가 적음.
    따라서 한글이 없고 히라가나/가타카나가 1개 이상 있으면 일본어로 판단.

    Args:
        text: 분석할 텍스트

    Returns:
        언어 코드 ('ko', 'ja', 'en')
    """
    if not text:
        return 'en'

    # 한글 감지
    korean_chars = len(re.findall(r'[가-힣]', text))
    # 일본어 감지 (히라가나 + 가타카나)
    japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))

    # 한국어 우선 (한글이 있으면 한국어)
    if korean_chars > 0:
        return 'ko'
    # 일본어: 히라가나/가타카나가 1개 이상 있으면 일본어
    elif japanese_chars > 0:
        return 'ja'

    return 'en'


def get_config(lang_code: str):
    """
    언어 코드에 해당하는 설정 모듈 반환

    Args:
        lang_code: 언어 코드 ('ko', 'ja', 'en')

    Returns:
        언어 설정 모듈 (없으면 한국어 기본값)
    """
    return SUPPORTED_LANGUAGES.get(lang_code, ko)


def get_fonts(lang_code: str) -> list:
    """언어별 폰트 목록 반환"""
    config = get_config(lang_code)
    return getattr(config, 'FONTS', ko.FONTS)


def get_subtitle_max_chars(lang_code: str) -> int:
    """언어별 자막 최대 글자 수 반환"""
    config = get_config(lang_code)
    return getattr(config, 'SUBTITLE_MAX_CHARS', ko.SUBTITLE_MAX_CHARS)


def get_tts_voice(lang_code: str, gender: str = 'male') -> str:
    """언어별 TTS 음성 반환"""
    config = get_config(lang_code)
    voices = getattr(config, 'TTS_VOICES', ko.TTS_VOICES)
    return voices.get(gender, voices.get('male'))


def get_ass_style(lang_code: str) -> str:
    """언어별 ASS 자막 스타일 문자열 반환"""
    config = get_config(lang_code)
    if hasattr(config, 'get_ass_style_string'):
        return config.get_ass_style_string()
    return ko.get_ass_style_string()

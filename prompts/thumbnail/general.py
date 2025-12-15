# -*- coding: utf-8 -*-
"""
일반 영상용 웹툰 썸네일 시스템 (뉴스 외)
- 지식(knowledge), 건강(health), 기독교(christian), 역사(history) 채널 공통
- GPT: 텍스트/톤 결정
- Gemini: 렌더링만 (판단 금지)
"""

from typing import Dict, List, Optional, Tuple
import re

# =============================================================================
# 1. GPT용 썸네일 텍스트/톤 결정 가이드
# =============================================================================

GENERAL_THUMBNAIL_RULES = """
## ⚠️ 일반 영상 썸네일 규칙 (뉴스 외)

### 0. 채널 공통 선언 (필수)
- 이 썸네일은 속보/뉴스가 아니다
- 목적은 "지금 일어난 일"이 아니라 "이 영상을 보면 무엇을 이해하게 되는가"
- 스타일은 웹툰(만화) 기반
- 과장된 감정은 허용하되, 주제 신뢰도를 해치지 않는 선에서 제한

### 1. 일반 영상 썸네일의 본질

| 구분 | 뉴스 | 일반 영상 |
|------|------|----------|
| 목적 | 상황 전달 | 가치/이해 약속 |
| 감정 | 억제 | 적절히 허용 |
| 텍스트 | 상황 명사 | 의미·혜택 요약 |
| 클릭 이유 | 정보 확인 | 궁금증 + 얻을 것 |

👉 일반 영상 썸네일은 "이 영상을 보면 내 생각이 정리될 것 같다"는 느낌을 줘야 한다

### 2. 공통 썸네일 텍스트 규칙

**2-1. 텍스트 길이**
- 7-14자 권장, 최대 18자
- 1줄 또는 2줄 (2줄일 경우 각 줄 4-9자)

**2-2. 메시지 구조**
- 원인 / 기준 / 이유 / 깨달음 / 핵심 포인트 중 1개만
- 질문형 가능하지만, 너무 직접적인 질문 금지
  - ❌ "왜 이럴까?"
  - ⭕ "이유가 있었다"

**2-3. 허용 / 금지 표현**

허용 단어:
- 이유, 기준, 원리, 방식, 흐름, 선택, 시점, 순간, 구조

금지 단어:
- 충격, 소름, 대박, 미쳤다, 난리
- 뉴스용 단어(속보, 전격, 긴급)
- 너무 추상적인 말(이것, 그거, 진실)

### 3. 채널별 썸네일 제작 규칙

#### 📘 knowledge (지식 채널)
- 목적: "아, 이건 알아두면 도움 되겠다"
- 텍스트 타입: 이유형 / 원리형 / 구조형 / 정리형
- 추천 문구: 진짜 이유, 핵심 원리, 이렇게 작동한다, 한 번에 정리, 생각의 구조
- 이미지 톤: 깨달음/생각 중 표정

#### 🩺 health (건강 채널)
- 목적: "이건 내 얘기일 수도 있겠다"
- 텍스트 타입: 신호형 / 기준형 / 습관형 / 변화형
- 추천 문구: 몸의 신호, 바꿔야 할 습관, 이 기준부터, 나이 들수록, 무심코 하는 행동
- 이미지 톤: 걱정/공감/안타까움 (과도한 공포 금지)

#### ✝️ christian (기독교 채널)
- 목적: "이건 내 신앙을 돌아보게 하겠다"
- 텍스트 타입: 메시지형 / 기준형 / 묵상형
- 추천 문구: 믿음의 기준, 하나님이 보시는 것, 다시 붙잡을 말씀, 돌아봐야 할 마음, 기다림의 의미
- 이미지 톤: 차분함 / 따뜻함 / 깊은 고민 (과장된 감정 절대 금지)

#### 🏺 history (역사 채널)
- 목적: "이 순간이 모든 걸 갈랐구나"
- 텍스트 타입: 결정형 / 전환점형 / 배경형
- 추천 문구: 결정적 순간, 흐름이 바뀐 이유, 선택의 결과, 숨은 배경, 갈림길
- 이미지 톤: 긴장감 / 무게감 (드라마틱하되 과장 ❌)

### 4. 제목 + 썸네일 매칭 규칙
- 썸네일: 핵심 메시지 한 조각
- 제목: 구체적 설명
- 예시:
  - 썸네일: "진짜 이유"
  - 제목: "우리는 왜 같은 선택을 반복할까"

### 5. OUTPUT 구조

```json
{
  "thumbnail_text": {
    "line1": "메인 텍스트 (최대 10자)",
    "line2": "서브 텍스트 (선택, 최대 8자)"
  },
  "tone": "curious|empathetic|reflective|serious",
  "image_hint": "thinking|realization|concern|calm",
  "text_position": "left|right",
  "face": true|false,
  "validation": {
    "char_count": number,
    "single_message": true,
    "not_sensational": true
  }
}
```
"""


# =============================================================================
# 2. 채널별 렌더링 프리셋
# =============================================================================

CHANNEL_PRESETS = {
    "knowledge": {
        "channel_type": "knowledge",
        "style": "clean webtoon",
        "mood": "curious",
        "expression": "realization",
        "emotion_level": "restrained",
        "background": "simple gradient, light",
        "effects": "subtle emphasis lines",
        "character_size": "35-45%",
        "color_tone": "neutral to bright",
        "notes": "focus on clarity and insight, no drama",
        "default_face": False,
    },
    "health": {
        "channel_type": "health",
        "style": "soft webtoon",
        "mood": "empathetic",
        "expression": "concern",
        "emotion_level": "low",
        "background": "soft neutral background",
        "effects": "minimal",
        "character_size": "40-50%",
        "color_tone": "warm and calm",
        "notes": "avoid fear, focus on relatable concern",
        "default_face": True,
    },
    "christian": {
        "channel_type": "christian",
        "style": "warm webtoon",
        "mood": "reflective",
        "expression": "calm",
        "emotion_level": "very low",
        "background": "soft light, minimal",
        "effects": "none or very subtle",
        "character_size": "30-40%",
        "color_tone": "warm and gentle",
        "notes": "no exaggeration, reverent tone",
        "default_face": True,
    },
    "history": {
        "channel_type": "history",
        "style": "dramatic webtoon",
        "mood": "serious",
        "expression": "thinking",
        "emotion_level": "medium",
        "background": "historical or symbolic, minimal",
        "effects": "subtle dramatic lines",
        "character_size": "35-45%",
        "color_tone": "muted, heavy",
        "notes": "dramatic but not sensational",
        "default_face": False,
    },
}


# =============================================================================
# 3. Face 결정 로직
# =============================================================================

# Face=TRUE 키워드 (내면/인식/마음/기준 암시)
FACE_TRUE_KEYWORDS = [
    "이유", "기준", "돌아봄", "깨달음", "선택", "마음", "신호",
    "믿음", "생각", "판단", "묵상", "마음가짐", "결심", "깨닫",
    "돌아보", "느끼", "공감", "안타까", "걱정"
]

# Face=FALSE 키워드 (구조/정보 중심)
FACE_FALSE_KEYWORDS = [
    "원리", "구조", "흐름", "단계", "정리", "비교", "배경",
    "시스템", "제도", "통계", "패턴", "과정", "방식", "방법",
    "차트", "데이터", "역사적", "사건"
]

# 사고 유도형 제목 패턴
THOUGHT_PROVOKING_PATTERNS = [
    r"왜\s",
    r"어떻게\s",
    r"우리는\s",
    r"무엇이\s",
    r"어디서\s",
    r"언제\s",
]


def determine_face_visibility(
    channel_type: str,
    thumbnail_text: str,
    title: str,
    script_keywords: Optional[List[str]] = None
) -> Tuple[bool, float, str]:
    """
    Face=true/false 자동 결정

    Args:
        channel_type: knowledge, health, christian, history
        thumbnail_text: 썸네일 텍스트 (line1 + line2)
        title: 영상 제목
        script_keywords: 대본에서 추출된 키워드 목록

    Returns:
        (face: bool, score: float, reason: str)
    """
    score = 0.0
    reasons = []

    # 1. 채널 타입 가중치
    if channel_type in ["health", "christian"]:
        score += 1.0
        reasons.append(f"채널({channel_type})+1")
    elif channel_type in ["knowledge", "history"]:
        score += 0.5
        reasons.append(f"채널({channel_type})+0.5")

    # 2. 썸네일 텍스트 신호 분석
    text_combined = (thumbnail_text or "") + " " + (title or "")
    text_combined = text_combined.lower()

    # Face=TRUE 키워드 체크
    for keyword in FACE_TRUE_KEYWORDS:
        if keyword in text_combined:
            score += 1.0
            reasons.append(f"키워드({keyword})+1")
            break  # 하나만 카운트

    # 3. 사고 유도형 제목 체크
    for pattern in THOUGHT_PROVOKING_PATTERNS:
        if re.search(pattern, title or ""):
            score += 1.0
            reasons.append("사고유도형 제목+1")
            break

    # 4. 스크립트 키워드 분석
    if script_keywords:
        inner_count = sum(1 for kw in script_keywords if any(
            face_kw in kw for face_kw in FACE_TRUE_KEYWORDS
        ))
        if inner_count >= 2:
            score += 0.5
            reasons.append("스크립트 내면 키워드+0.5")

    # 5. Face=FALSE 강제 조건 체크
    force_false = False
    for keyword in FACE_FALSE_KEYWORDS:
        if keyword in text_combined:
            force_false = True
            reasons.append(f"구조/추상 키워드({keyword}) → force false")
            break

    # 최종 결정
    if force_false:
        return (False, score, " | ".join(reasons))
    elif score >= 2.0:
        return (True, score, " | ".join(reasons))
    else:
        # 기본값 사용
        preset = CHANNEL_PRESETS.get(channel_type, {})
        default_face = preset.get("default_face", False)
        reasons.append(f"기본값({channel_type}={default_face})")
        return (default_face, score, " | ".join(reasons))


def get_channel_preset(channel_type: str) -> Dict:
    """채널 프리셋 조회"""
    return CHANNEL_PRESETS.get(channel_type, CHANNEL_PRESETS["knowledge"])


# =============================================================================
# 4. Gemini 렌더링 템플릿
# =============================================================================

GEMINI_RENDER_TEMPLATE = """You are an image renderer.
Your role is to VISUALIZE the given specification exactly.
Do NOT interpret meaning.
Do NOT change or add text.
Do NOT add emotional exaggeration.

TASK:
Render a YouTube thumbnail in WEBTOON (comic-style illustration) format
for a general (non-news) video.
The goal is to visually support understanding, reflection, or insight,
not urgency or breaking news.

THUMBNAIL TEXT (EXACT — do not modify):
Line 1: "{line1}"
Line 2: "{line2}"

LAYOUT:
- Text position: {text_position}
- Max text lines: {max_lines}
- Text alignment: vertical center on chosen side
- Character placement: opposite side of text
- Safe margins: keep text fully readable on mobile screens

CHARACTER:
- Style: {style}
- Face visible: {face}
- Expression: {expression}
- Emotion level: {emotion_level}
- Character occupies {character_size} of frame

CHANNEL TONE HINT:
- {channel_type}: {notes}

BACKGROUND:
- {background}
- Mood: {mood}

VISUAL EFFECTS:
- {effects}
- Effects must NOT overpower text readability
- No flashy light bursts
- No symbols, emojis, or stickers

RESTRICTIONS:
- Do NOT invent any new text
- Do NOT change wording or tone
- Do NOT add symbols, emojis, or captions
- Do NOT add news-style urgency
- Do NOT add sensational elements
- No screaming, no panic, no extreme expressions
"""


def build_gemini_prompt(
    channel_type: str,
    line1: str,
    line2: str = "",
    text_position: str = "right",
    face: bool = True,
    custom_expression: Optional[str] = None,
) -> str:
    """
    Gemini 이미지 생성용 프롬프트 빌드

    Args:
        channel_type: knowledge, health, christian, history
        line1: 썸네일 텍스트 1줄
        line2: 썸네일 텍스트 2줄 (선택)
        text_position: left 또는 right
        face: 얼굴 표시 여부
        custom_expression: 커스텀 표정 (없으면 프리셋 사용)

    Returns:
        Gemini에 전달할 완성된 프롬프트
    """
    preset = get_channel_preset(channel_type)

    max_lines = 2 if line2 else 1
    expression = custom_expression or preset.get("expression", "thinking")

    prompt = GEMINI_RENDER_TEMPLATE.format(
        line1=line1,
        line2=line2 or "(none)",
        text_position=text_position,
        max_lines=max_lines,
        style=preset.get("style", "clean webtoon"),
        face="true" if face else "false",
        expression=expression,
        emotion_level=preset.get("emotion_level", "restrained"),
        character_size=preset.get("character_size", "35-45%"),
        channel_type=channel_type,
        notes=preset.get("notes", ""),
        background=preset.get("background", "simple gradient"),
        mood=preset.get("mood", "neutral"),
        effects=preset.get("effects", "minimal"),
    )

    return prompt


# =============================================================================
# 5. GPT 프롬프트 생성
# =============================================================================

GPT_THUMBNAIL_SYSTEM_PROMPT = """You are a YouTube thumbnail generator for general (non-news) videos.
Visual style is WEBTOON.

Channel categories:
knowledge, health, christian, history

Rules:
- Thumbnail text length: 7-14 Korean characters (max 18).
- Prefer 1 line; max 2 lines.
- One core message only (reason, principle, signal, message).
- Emotional expression allowed but must not reduce credibility.
- No sensational words or news-only terms.
- Text must promise value or understanding, not urgency.

Forbidden words:
충격, 대박, 소름, 미쳤다, 난리, 속보, 전격, 긴급, 이것, 그거, 진실

Channel-specific guidelines:

📘 KNOWLEDGE:
- Purpose: "아, 이건 알아두면 도움 되겠다"
- Text types: 이유형, 원리형, 구조형, 정리형
- Examples: 진짜 이유, 핵심 원리, 이렇게 작동한다, 한 번에 정리

🩺 HEALTH:
- Purpose: "이건 내 얘기일 수도 있겠다"
- Text types: 신호형, 기준형, 습관형, 변화형
- Examples: 몸의 신호, 바꿔야 할 습관, 이 기준부터, 나이 들수록

✝️ CHRISTIAN:
- Purpose: "이건 내 신앙을 돌아보게 하겠다"
- Text types: 메시지형, 기준형, 묵상형
- Examples: 믿음의 기준, 하나님이 보시는 것, 다시 붙잡을 말씀

🏺 HISTORY:
- Purpose: "이 순간이 모든 걸 갈랐구나"
- Text types: 결정형, 전환점형, 배경형
- Examples: 결정적 순간, 흐름이 바뀐 이유, 선택의 결과

OUTPUT JSON ONLY:
{
  "thumbnail_text": {
    "line1": "string (max 10 chars)",
    "line2": "string or empty (max 8 chars)"
  },
  "tone": "curious|empathetic|reflective|serious",
  "image_hint": "thinking|realization|concern|calm",
  "text_position": "left|right",
  "validation": {
    "char_count": number,
    "single_message": true,
    "not_sensational": true
  }
}
"""


def get_gpt_thumbnail_prompt(
    channel_type: str,
    title: str,
    script_keywords: List[str],
    include_rules: bool = True
) -> str:
    """
    GPT에 전달할 썸네일 생성 프롬프트

    Args:
        channel_type: 채널 타입
        title: 영상 제목
        script_keywords: 대본 키워드
        include_rules: 전체 규칙 포함 여부

    Returns:
        GPT 시스템 프롬프트
    """
    if include_rules:
        return GPT_THUMBNAIL_SYSTEM_PROMPT + "\n\n" + GENERAL_THUMBNAIL_RULES
    return GPT_THUMBNAIL_SYSTEM_PROMPT


# =============================================================================
# 6. 유틸리티 함수
# =============================================================================

def validate_thumbnail_text(line1: str, line2: str = "") -> Dict:
    """썸네일 텍스트 검증"""
    total_chars = len(line1) + len(line2)

    # 금지어 체크
    forbidden = ["충격", "대박", "소름", "미쳤다", "난리", "속보", "전격", "긴급"]
    text_combined = line1 + line2
    found_forbidden = [w for w in forbidden if w in text_combined]

    return {
        "char_count": total_chars,
        "is_valid_length": 7 <= total_chars <= 18,
        "single_message": True,  # GPT가 보장
        "not_sensational": len(found_forbidden) == 0,
        "forbidden_words_found": found_forbidden,
    }


def get_expression_for_tone(tone: str) -> str:
    """톤에 맞는 표정 반환"""
    tone_to_expression = {
        "curious": "thinking",
        "empathetic": "concern",
        "reflective": "calm",
        "serious": "thinking",
    }
    return tone_to_expression.get(tone, "thinking")

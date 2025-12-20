"""
commentary.py
성경 주석 조회 및 분석 모듈

기능:
- 외부 API를 통한 주석 조회 (가능한 경우)
- GPT 기반 주석 스타일 분석 생성 (fallback)
- 다양한 주석 스타일 지원 (Matthew Henry, Calvin, Gill's 등)
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Any
from functools import lru_cache

# 지원하는 주석 스타일
COMMENTARY_STYLES = {
    "matthew_henry": {
        "name": "Matthew Henry",
        "name_ko": "매튜 헨리",
        "description": "실용적 적용 중심의 경건한 주석",
        "focus": ["practical_application", "devotional", "spiritual_insight"],
        "era": "17-18세기 청교도"
    },
    "john_gill": {
        "name": "John Gill",
        "name_ko": "존 길",
        "description": "원어와 역사적 배경에 충실한 학술적 주석",
        "focus": ["original_languages", "historical_context", "doctrinal"],
        "era": "18세기 침례교"
    },
    "john_calvin": {
        "name": "John Calvin",
        "name_ko": "존 칼빈",
        "description": "개혁주의 신학에 기반한 체계적 주석",
        "focus": ["reformed_theology", "systematic", "christological"],
        "era": "16세기 종교개혁"
    },
    "adam_clarke": {
        "name": "Adam Clarke",
        "name_ko": "아담 클락",
        "description": "감리교 전통의 원어 분석 주석",
        "focus": ["original_languages", "methodist", "scholarly"],
        "era": "18-19세기 감리교"
    },
    "spurgeon": {
        "name": "Charles Spurgeon",
        "name_ko": "찰스 스펄전",
        "description": "설교적 통찰과 그리스도 중심 해석",
        "focus": ["christological", "homiletical", "evangelistic"],
        "era": "19세기 침례교"
    }
}


class CommentaryService:
    """주석 조회 및 생성 서비스"""

    def __init__(self, openai_client=None):
        """
        Args:
            openai_client: OpenAI 클라이언트 (GPT 기반 주석 생성용)
        """
        self._client = openai_client
        self._cache: Dict[str, Dict] = {}

    def set_client(self, client):
        """OpenAI 클라이언트 설정"""
        self._client = client

    def get_commentary(
        self,
        reference: str,
        verse_text: str = "",
        styles: List[str] = None,
        use_gpt: bool = True
    ) -> Dict[str, Any]:
        """
        성경 구절에 대한 주석 조회

        Args:
            reference: "요한복음 3:16"
            verse_text: 구절 본문 (GPT 분석용)
            styles: 조회할 주석 스타일 목록 (기본: matthew_henry, john_gill)
            use_gpt: GPT 기반 분석 사용 여부

        Returns:
            {
                "reference": "요한복음 3:16",
                "commentaries": [
                    {
                        "style": "matthew_henry",
                        "author": "Matthew Henry",
                        "content": "...",
                        "source": "gpt"  # 또는 "api"
                    },
                    ...
                ],
                "summary": "종합 요약"
            }
        """
        if styles is None:
            styles = ["matthew_henry", "john_gill"]

        # 캐시 확인
        cache_key = self._get_cache_key(reference, styles)
        if cache_key in self._cache:
            print(f"[COMMENTARY] Cache hit: {reference}")
            return self._cache[cache_key]

        commentaries = []

        for style in styles:
            if style not in COMMENTARY_STYLES:
                print(f"[COMMENTARY] Unknown style: {style}")
                continue

            # 외부 API 시도 (향후 구현)
            api_result = self._try_external_api(reference, style)
            if api_result:
                commentaries.append({
                    "style": style,
                    "author": COMMENTARY_STYLES[style]["name"],
                    "author_ko": COMMENTARY_STYLES[style]["name_ko"],
                    "content": api_result,
                    "source": "api"
                })
            elif use_gpt and self._client:
                # GPT 기반 주석 스타일 분석
                gpt_result = self._generate_gpt_commentary(reference, verse_text, style)
                if gpt_result:
                    commentaries.append({
                        "style": style,
                        "author": COMMENTARY_STYLES[style]["name"],
                        "author_ko": COMMENTARY_STYLES[style]["name_ko"],
                        "content": gpt_result,
                        "source": "gpt"
                    })

        result = {
            "reference": reference,
            "commentaries": commentaries,
            "summary": self._generate_summary(commentaries) if len(commentaries) > 1 else ""
        }

        # 캐시 저장
        self._cache[cache_key] = result
        return result

    def _try_external_api(self, reference: str, style: str) -> Optional[str]:
        """
        외부 API에서 주석 조회 시도

        현재 무료 API가 제한적이므로 None 반환
        향후 API 연동 시 이 메서드를 확장
        """
        # TODO: 외부 API 연동 (BibleHub, Context API 등)
        return None

    def _generate_gpt_commentary(
        self,
        reference: str,
        verse_text: str,
        style: str
    ) -> Optional[str]:
        """
        GPT를 사용하여 주석 스타일 분석 생성
        """
        if not self._client:
            return None

        style_info = COMMENTARY_STYLES.get(style, {})
        style_name = style_info.get("name", style)
        style_desc = style_info.get("description", "")
        style_focus = style_info.get("focus", [])
        style_era = style_info.get("era", "")

        system_prompt = f"""당신은 {style_name}({style_era}) 스타일의 성경 주석가입니다.

{style_name}의 특징:
- {style_desc}
- 주요 관점: {', '.join(style_focus)}

주석 작성 지침:
1. {style_name}의 해석 스타일과 신학적 관점을 반영하세요
2. 원어(헬라어/히브리어) 분석이 해당 스타일에 맞다면 포함하세요
3. 역사적, 문화적 배경을 적절히 설명하세요
4. 영적 통찰과 적용점을 제시하세요
5. 3-5문장으로 간결하게 작성하세요
6. 한글로 작성하세요"""

        user_prompt = f"""다음 성경 구절을 {style_name} 스타일로 주석해주세요.

본문: {reference}
{f'내용: {verse_text}' if verse_text else ''}

위 구절에 대한 {style_name} 스타일의 주석을 작성해주세요."""

        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()
            print(f"[COMMENTARY] GPT generated {style_name} commentary for {reference}")
            return content
        except Exception as e:
            print(f"[COMMENTARY] GPT error for {style}: {e}")
            return None

    def _generate_summary(self, commentaries: List[Dict]) -> str:
        """여러 주석의 종합 요약 생성"""
        if not commentaries or not self._client:
            return ""

        # 간단한 요약 (GPT 호출 없이)
        authors = [c.get("author_ko", c.get("author", "")) for c in commentaries]
        return f"위 주석은 {', '.join(authors)}의 관점을 종합한 것입니다."

    def _get_cache_key(self, reference: str, styles: List[str]) -> str:
        """캐시 키 생성"""
        key_str = f"{reference}|{'|'.join(sorted(styles))}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_available_styles(self) -> Dict[str, Dict]:
        """사용 가능한 주석 스타일 목록 반환"""
        return COMMENTARY_STYLES


# 싱글톤 인스턴스
_commentary_service: Optional[CommentaryService] = None


def get_commentary_service() -> CommentaryService:
    """CommentaryService 싱글톤 인스턴스 반환"""
    global _commentary_service
    if _commentary_service is None:
        _commentary_service = CommentaryService()
    return _commentary_service


def init_commentary_service(openai_client):
    """OpenAI 클라이언트로 서비스 초기화"""
    service = get_commentary_service()
    service.set_client(openai_client)
    return service


# 편의 함수
def get_verse_commentary(
    reference: str,
    verse_text: str = "",
    styles: List[str] = None
) -> Dict[str, Any]:
    """
    성경 구절 주석 조회 (편의 함수)

    Args:
        reference: "요한복음 3:16"
        verse_text: 구절 본문
        styles: 주석 스타일 목록

    Returns:
        주석 결과 딕셔너리
    """
    service = get_commentary_service()
    return service.get_commentary(reference, verse_text, styles)


def format_commentary_for_prompt(commentary_result: Dict) -> str:
    """
    주석 결과를 Step1 프롬프트용 텍스트로 포맷팅

    Args:
        commentary_result: get_verse_commentary() 결과

    Returns:
        포맷팅된 텍스트 문자열
    """
    if not commentary_result or not commentary_result.get("commentaries"):
        return ""

    lines = []
    lines.append("【 주석 참고 자료 】")
    lines.append(f"본문: {commentary_result.get('reference', '')}")
    lines.append("")

    for comm in commentary_result.get("commentaries", []):
        author = comm.get("author_ko", comm.get("author", ""))
        style = comm.get("style", "")
        content = comm.get("content", "")
        source = comm.get("source", "")

        style_info = COMMENTARY_STYLES.get(style, {})
        era = style_info.get("era", "")

        lines.append(f"▶ {author} ({era})")
        lines.append(content)
        lines.append("")

    summary = commentary_result.get("summary", "")
    if summary:
        lines.append(f"※ {summary}")

    return "\n".join(lines)

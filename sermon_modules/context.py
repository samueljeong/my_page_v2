"""
context.py
시대 컨텍스트 조회 모듈 - 설교 적용점을 현실적으로 만들기 위한 현재 이슈/트렌드 수집

기능:
- Google News RSS로 카테고리별 뉴스 수집 (정치, 경제, 사회, 국제)
- 주요 사회 지표/통계 제공
- 설교 주제와 관련된 시사점 추출
"""

import os
import re
import json
import hashlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import lru_cache
from html import unescape

# 뉴스 카테고리별 RSS URL (Google News 한국 - 토픽 기반)
# 토픽 ID 기반 URL 사용 (한글 인코딩 문제 없음)
NEWS_FEEDS = {
    "economy": {
        "name": "경제",
        # Google News Korea - 비즈니스 토픽
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "keywords": ["경제", "금리", "물가", "부동산", "주식", "환율", "일자리", "취업"]
    },
    "politics": {
        "name": "정치",
        # Google News Korea - 정치 토픽
        "url": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtdHZLQUFQAQ?hl=ko&gl=KR&ceid=KR:ko",
        "keywords": ["정치", "국회", "대통령", "선거", "정책", "법안"]
    },
    "society": {
        "name": "사회",
        # Google News Korea - 사회 토픽
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "keywords": ["사회", "교육", "복지", "안전", "환경", "건강", "가족"]
    },
    "world": {
        "name": "국제",
        # Google News Korea - 국제 토픽
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "keywords": ["국제", "미국", "중국", "전쟁", "외교", "무역"]
    },
    "culture": {
        "name": "문화",
        # Google News Korea - 엔터테인먼트 토픽
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "keywords": ["문화", "트렌드", "MZ세대", "라이프스타일", "여행"]
    }
}

# 청중 유형별 관심 카테고리
AUDIENCE_INTERESTS = {
    "청년": {
        "categories": ["economy", "society", "culture"],
        "focus_keywords": ["취업", "일자리", "주거", "결혼", "MZ세대", "청년정책", "대출", "자취"],
        "concerns": ["취업난", "주거 불안", "결혼 기피", "경제적 독립", "미래 불확실성"]
    },
    "장년": {
        "categories": ["economy", "politics", "society"],
        "focus_keywords": ["부동산", "노후", "연금", "건강", "자녀교육", "중년", "퇴직"],
        "concerns": ["노후 준비", "자녀 교육비", "건강 관리", "부모 부양", "직장 안정성"]
    },
    "노년": {
        "categories": ["society", "politics", "economy"],
        "focus_keywords": ["연금", "요양", "건강보험", "노인복지", "치매", "독거노인"],
        "concerns": ["건강 악화", "경제적 불안", "외로움", "디지털 소외", "가족 관계"]
    },
    "가정": {
        "categories": ["society", "economy", "culture"],
        "focus_keywords": ["교육", "육아", "저출산", "가정", "부부", "자녀"],
        "concerns": ["자녀 교육", "가정 경제", "부부 관계", "일-가정 양립", "세대 갈등"]
    },
    "전체": {
        "categories": ["economy", "politics", "society", "world"],
        "focus_keywords": [],
        "concerns": ["경제 불안", "사회 갈등", "미래 불확실성", "관계 단절"]
    }
}

# 한국 사회 주요 지표 (정기적으로 업데이트 필요)
SOCIAL_INDICATORS = {
    "economy": {
        "기준금리": "3.0%",
        "물가상승률": "2.7%",
        "실업률": "2.8%",
        "청년실업률": "6.5%",
        "가계부채": "1,900조원",
        "updated": "2024-12"
    },
    "society": {
        "출산율": "0.72명",
        "고령화율": "19.2%",
        "1인가구": "34.5%",
        "자살률": "OECD 1위",
        "우울증": "성인 5명 중 1명",
        "updated": "2024-12"
    },
    "youth": {
        "청년 주거비 부담": "월수입 30% 이상",
        "평균 초혼 연령": "남 34세, 여 32세",
        "청년 부채": "평균 4,200만원",
        "취업 준비 기간": "평균 11개월",
        "updated": "2024-12"
    }
}


class ContextService:
    """시대 컨텍스트 조회 서비스"""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = 3600  # 1시간 캐시

    def get_current_context(
        self,
        audience_type: str = "전체",
        categories: List[str] = None,
        max_news_per_category: int = 3
    ) -> Dict[str, Any]:
        """
        현재 시대 컨텍스트 조회

        Args:
            audience_type: 청중 유형 (청년, 장년, 노년, 가정, 전체)
            categories: 조회할 카테고리 목록 (없으면 청중 유형에 따라 자동 선택)
            max_news_per_category: 카테고리당 최대 뉴스 수

        Returns:
            {
                "audience": "청년",
                "news": {"economy": [...], "society": [...]},
                "indicators": {...},
                "concerns": [...],
                "generated_at": "2024-12-20T10:00:00"
            }
        """
        # 캐시 확인
        cache_key = self._get_cache_key(audience_type, categories)
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # 청중 유형에 따른 카테고리 결정
        audience_info = AUDIENCE_INTERESTS.get(audience_type, AUDIENCE_INTERESTS["전체"])
        if categories is None:
            categories = audience_info["categories"]

        # 뉴스 수집
        news_data = {}
        for cat in categories:
            if cat in NEWS_FEEDS:
                news_data[cat] = self._fetch_news(
                    cat,
                    audience_info.get("focus_keywords", []),
                    max_news_per_category
                )

        # 결과 구성
        result = {
            "audience": audience_type,
            "news": news_data,
            "indicators": self._get_relevant_indicators(audience_type),
            "concerns": audience_info.get("concerns", []),
            "focus_keywords": audience_info.get("focus_keywords", []),
            "generated_at": datetime.now().isoformat()
        }

        # 캐시 저장
        self._set_cached(cache_key, result)
        return result

    def _fetch_news(
        self,
        category: str,
        focus_keywords: List[str],
        max_items: int
    ) -> List[Dict]:
        """Google News RSS에서 뉴스 가져오기"""
        feed_info = NEWS_FEEDS.get(category)
        if not feed_info:
            return []

        try:
            url = feed_info["url"]
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read().decode('utf-8')

            # XML 파싱
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')

            news_list = []
            for item in items[:max_items * 2]:  # 여유있게 가져와서 필터링
                title = item.find('title')
                pub_date = item.find('pubDate')
                link = item.find('link')

                if title is not None:
                    title_text = unescape(title.text or "")
                    # 키워드 관련도 체크
                    relevance = self._calculate_relevance(title_text, focus_keywords)

                    news_list.append({
                        "title": title_text,
                        "link": link.text if link is not None else "",
                        "published": pub_date.text if pub_date is not None else "",
                        "relevance": relevance
                    })

            # 관련도 순으로 정렬 후 상위 N개
            news_list.sort(key=lambda x: x["relevance"], reverse=True)
            return news_list[:max_items]

        except Exception as e:
            print(f"[CONTEXT] Failed to fetch {category} news: {e}")
            return []

    def _calculate_relevance(self, title: str, keywords: List[str]) -> int:
        """제목과 키워드의 관련도 계산"""
        if not keywords:
            return 0
        score = 0
        for kw in keywords:
            if kw in title:
                score += 1
        return score

    def _get_relevant_indicators(self, audience_type: str) -> Dict[str, Any]:
        """청중 유형에 맞는 사회 지표 반환"""
        indicators = {}

        if audience_type in ["청년", "전체"]:
            indicators["youth"] = SOCIAL_INDICATORS.get("youth", {})

        if audience_type in ["장년", "노년", "전체"]:
            indicators["economy"] = SOCIAL_INDICATORS.get("economy", {})

        if audience_type in ["가정", "전체"]:
            indicators["society"] = SOCIAL_INDICATORS.get("society", {})

        return indicators

    def _get_cache_key(self, audience_type: str, categories: List[str] = None) -> str:
        """캐시 키 생성"""
        cat_str = "|".join(sorted(categories)) if categories else "auto"
        today = datetime.now().strftime("%Y-%m-%d-%H")  # 시간단위 캐시
        return hashlib.md5(f"{audience_type}|{cat_str}|{today}".encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[Dict]:
        """캐시에서 조회"""
        if key in self._cache:
            cached = self._cache[key]
            cached_time = datetime.fromisoformat(cached.get("generated_at", "2000-01-01"))
            if datetime.now() - cached_time < timedelta(seconds=self._cache_ttl):
                print(f"[CONTEXT] Cache hit")
                return cached
        return None

    def _set_cached(self, key: str, data: Dict):
        """캐시에 저장"""
        self._cache[key] = data


# 싱글톤 인스턴스
_context_service: Optional[ContextService] = None


def get_context_service() -> ContextService:
    """ContextService 싱글톤 인스턴스 반환"""
    global _context_service
    if _context_service is None:
        _context_service = ContextService()
    return _context_service


# 편의 함수
def get_current_context(
    audience_type: str = "전체",
    categories: List[str] = None
) -> Dict[str, Any]:
    """
    현재 시대 컨텍스트 조회 (편의 함수)

    Args:
        audience_type: 청중 유형 (청년, 장년, 노년, 가정, 전체)
        categories: 카테고리 목록

    Returns:
        컨텍스트 결과 딕셔너리
    """
    service = get_context_service()
    return service.get_current_context(audience_type, categories)


def format_context_for_prompt(context_result: Dict, sermon_topic: str = "") -> str:
    """
    컨텍스트 결과를 Step2 프롬프트용 텍스트로 포맷팅

    Args:
        context_result: get_current_context() 결과
        sermon_topic: 설교 주제 (관련 뉴스 강조용)

    Returns:
        포맷팅된 텍스트 문자열
    """
    if not context_result:
        return ""

    lines = []
    audience = context_result.get("audience", "전체")
    lines.append("【 현재 시대 컨텍스트 - 설교 구조에 반영하세요 】")
    lines.append(f"청중 유형: {audience}")
    lines.append("")

    # 주요 뉴스 이슈
    news = context_result.get("news", {})
    if news:
        lines.append("▶ 주요 시사 이슈")
        for cat, items in news.items():
            cat_name = NEWS_FEEDS.get(cat, {}).get("name", cat)
            if items:
                lines.append(f"  [{cat_name}]")
                for item in items[:2]:  # 카테고리당 2개
                    title = item.get("title", "")
                    # 제목이 너무 길면 자르기
                    if len(title) > 50:
                        title = title[:50] + "..."
                    lines.append(f"  • {title}")
        lines.append("")

    # 사회 지표
    indicators = context_result.get("indicators", {})
    if indicators:
        lines.append("▶ 관련 사회 지표")
        for cat, data in indicators.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    if key != "updated":
                        lines.append(f"  • {key}: {value}")
        lines.append("")

    # 청중의 주요 관심사
    concerns = context_result.get("concerns", [])
    if concerns:
        lines.append("▶ 청중의 주요 관심사/고민")
        for concern in concerns:
            lines.append(f"  • {concern}")
        lines.append("")

    # ═══════════════════════════════════════════════════════
    # Step2 구조 작성 가이드 (Step3에서 활용)
    # ═══════════════════════════════════════════════════════
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("【 설교 구조에 반드시 반영할 사항 】")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    lines.append("1. 【도입부/서론 - 아이스브레이킹】")
    lines.append("   위 시사 이슈 중 하나를 선택하여 청중의 관심을 끄는 도입부를 구성하세요.")
    lines.append("   예시: \"요즘 뉴스를 보면 [시사 이슈]가 화두입니다. 오늘 말씀에서 해답을 찾아봅시다.\"")
    lines.append("")

    lines.append("2. 【대지별 예화 제안】")
    lines.append("   각 대지(포인트)마다 위 시대적 맥락과 연결되는 예화를 제안하세요:")
    if concerns:
        for i, concern in enumerate(concerns[:3], 1):
            lines.append(f"   - 대지{i} 예화 힌트: \"{concern}\"과 연결")
    lines.append("")

    lines.append("3. 【적용/결론】")
    lines.append("   청중의 실제 고민(위 관심사)에 대한 구체적 해결책을 제시하세요.")
    lines.append("   추상적 권면이 아닌, 오늘 바로 실천할 수 있는 적용점을 포함하세요.")
    lines.append("")

    lines.append("※ 위 내용은 Step3 설교문 작성 시 도입부/예화/적용에 직접 활용됩니다.")

    return "\n".join(lines)


def get_audience_types() -> List[str]:
    """사용 가능한 청중 유형 목록 반환"""
    return list(AUDIENCE_INTERESTS.keys())


# ═══════════════════════════════════════════════════════════════
# 예화 검증 시스템 - 논란성 필터 및 연관성 검증
# ═══════════════════════════════════════════════════════════════

# 논란성 키워드 (예화에서 제외해야 할 주제)
CONTROVERSIAL_KEYWORDS = [
    # 정치적 논란
    "탄핵", "여야 대립", "정치 공방", "극우", "극좌", "이념 갈등",
    "보수 진보", "정치 성향", "친일", "친북", "종북",
    # 종교적 논란
    "이단", "사이비", "타 종교 비난", "종교 분쟁",
    # 사회적 논란
    "혐오", "차별", "인종", "성별 갈등", "페미", "남혐", "여혐",
    "성소수자", "동성애", "낙태",  # 교회 내 민감한 주제
    # 개인 논란
    "스캔들", "불륜", "성범죄", "마약",
    # 지역/세대 갈등
    "지역 갈등", "세대 갈등", "영남 호남", "꼰대", "MZ 비난",
]

# 예화로 적합한 주제 카테고리
SAFE_ILLUSTRATION_TOPICS = [
    "가족", "우정", "성장", "도전", "희망", "용서", "사랑",
    "섬김", "나눔", "감사", "인내", "믿음", "치유", "회복",
    "기적", "변화", "헌신", "겸손", "평화", "화해", "위로"
]


class IllustrationValidator:
    """예화 검증 서비스"""

    def __init__(self, openai_client=None):
        self._client = openai_client

    def set_client(self, client):
        """OpenAI 클라이언트 설정"""
        self._client = client

    def is_controversial(self, text: str) -> bool:
        """논란성 키워드 포함 여부 확인"""
        text_lower = text.lower()
        for keyword in CONTROVERSIAL_KEYWORDS:
            if keyword in text_lower or keyword.lower() in text_lower:
                return True
        return False

    def filter_news_for_illustration(self, news_list: List[Dict]) -> List[Dict]:
        """뉴스 목록에서 예화에 적합한 것만 필터링"""
        filtered = []
        for news in news_list:
            title = news.get("title", "")
            if not self.is_controversial(title):
                filtered.append(news)
        return filtered

    def validate_illustration(
        self,
        illustration: str,
        sermon_topic: str,
        bible_verse: str = ""
    ) -> Dict[str, Any]:
        """
        예화의 적합성 검증 (GPT 사용)

        Args:
            illustration: 예화 내용
            sermon_topic: 설교 주제/제목
            bible_verse: 성경 구절 (선택)

        Returns:
            {
                "is_valid": True/False,
                "relevance_score": 0-100,
                "is_controversial": True/False,
                "suggestion": "개선 제안 (필요시)",
                "reason": "판단 근거"
            }
        """
        # 1. 논란성 키워드 체크
        if self.is_controversial(illustration):
            return {
                "is_valid": False,
                "relevance_score": 0,
                "is_controversial": True,
                "suggestion": "논란의 여지가 있는 내용이 포함되어 있습니다. 다른 예화를 선택하세요.",
                "reason": "논란성 키워드 감지"
            }

        # 2. GPT 기반 심층 검증 (클라이언트 있을 때만)
        if self._client:
            return self._gpt_validate(illustration, sermon_topic, bible_verse)

        # GPT 없으면 기본 통과
        return {
            "is_valid": True,
            "relevance_score": 70,  # 기본 점수
            "is_controversial": False,
            "suggestion": "",
            "reason": "기본 검증 통과 (GPT 검증 미사용)"
        }

    def _gpt_validate(
        self,
        illustration: str,
        sermon_topic: str,
        bible_verse: str
    ) -> Dict[str, Any]:
        """GPT를 사용한 예화 검증"""
        try:
            system_prompt = """당신은 설교 예화 검증 전문가입니다.
예화가 설교에 적합한지 다음 기준으로 평가하세요:

1. 연관성 (0-100점): 설교 주제/성경 구절과 얼마나 연결되는가?
2. 논란성: 정치적, 종교적, 사회적으로 논란이 될 수 있는 내용인가?
3. 적절성: 교회 강단에서 사용하기에 적절한가?

JSON 형식으로 응답하세요:
{
    "is_valid": true/false,
    "relevance_score": 0-100,
    "is_controversial": true/false,
    "suggestion": "개선 제안 (필요시)",
    "reason": "판단 근거"
}"""

            user_prompt = f"""다음 예화를 검증해주세요:

【설교 주제】
{sermon_topic}

【성경 구절】
{bible_verse if bible_verse else "(없음)"}

【검증할 예화】
{illustration}

위 예화가 이 설교에 적합한지 평가해주세요."""

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            result_text = response.choices[0].message.content.strip()

            # JSON 파싱
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                result_text = "\n".join(lines)

            return json.loads(result_text)

        except Exception as e:
            print(f"[ILLUSTRATION] GPT 검증 실패: {e}")
            return {
                "is_valid": True,
                "relevance_score": 70,
                "is_controversial": False,
                "suggestion": "",
                "reason": f"GPT 검증 실패 - 기본 통과: {str(e)}"
            }

    def suggest_illustrations(
        self,
        sermon_topic: str,
        bible_verse: str,
        audience_type: str = "전체",
        count: int = 3
    ) -> List[Dict[str, str]]:
        """
        설교 주제에 맞는 예화 제안 (GPT 사용)

        Args:
            sermon_topic: 설교 주제/제목
            bible_verse: 성경 구절
            audience_type: 청중 유형
            count: 제안할 예화 수

        Returns:
            [{"title": "예화 제목", "content": "예화 내용", "connection": "설교와의 연결점"}, ...]
        """
        if not self._client:
            return []

        audience_info = AUDIENCE_INTERESTS.get(audience_type, AUDIENCE_INTERESTS["전체"])
        concerns = audience_info.get("concerns", [])

        try:
            system_prompt = f"""당신은 설교 예화 전문가입니다.
주어진 설교 주제와 성경 구절에 맞는 예화를 제안하세요.

【예화 작성 원칙】
1. 논란의 여지가 없는 안전한 주제만 사용
2. 정치, 종교 논쟁, 사회적 갈등 주제 절대 금지
3. 청중({audience_type})의 관심사와 연결: {', '.join(concerns[:3])}
4. 실제 일어났거나 일어날 법한 현실적인 이야기
5. 감동적이고 교훈적인 내용

JSON 배열 형식으로 응답하세요:
[
    {{"title": "예화 제목", "content": "예화 내용 (3-5문장)", "connection": "설교 메시지와의 연결점"}}
]"""

            user_prompt = f"""다음 설교에 적합한 예화 {count}개를 제안해주세요:

【설교 주제】
{sermon_topic}

【성경 구절】
{bible_verse}

【청중】
{audience_type}

논란의 여지가 없고, 설교 메시지와 자연스럽게 연결되는 예화를 제안해주세요."""

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content.strip()

            # JSON 파싱
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                result_text = "\n".join(lines)

            illustrations = json.loads(result_text)
            print(f"[ILLUSTRATION] {len(illustrations)}개 예화 제안 생성")
            return illustrations

        except Exception as e:
            print(f"[ILLUSTRATION] 예화 제안 생성 실패: {e}")
            return []


# 싱글톤 인스턴스
_illustration_validator: Optional[IllustrationValidator] = None


def get_illustration_validator() -> IllustrationValidator:
    """IllustrationValidator 싱글톤 인스턴스 반환"""
    global _illustration_validator
    if _illustration_validator is None:
        _illustration_validator = IllustrationValidator()
    return _illustration_validator


def init_context_service(openai_client):
    """OpenAI 클라이언트로 서비스 초기화"""
    validator = get_illustration_validator()
    validator.set_client(openai_client)
    return validator


# 편의 함수
def validate_illustration(
    illustration: str,
    sermon_topic: str,
    bible_verse: str = ""
) -> Dict[str, Any]:
    """예화 적합성 검증 (편의 함수)"""
    validator = get_illustration_validator()
    return validator.validate_illustration(illustration, sermon_topic, bible_verse)


def suggest_illustrations(
    sermon_topic: str,
    bible_verse: str,
    audience_type: str = "전체",
    count: int = 3
) -> List[Dict[str, str]]:
    """설교 주제에 맞는 예화 제안 (편의 함수)"""
    validator = get_illustration_validator()
    return validator.suggest_illustrations(sermon_topic, bible_verse, audience_type, count)

"""
혈영 이세계편 - YouTube Agent (유튜브 메타데이터 에이전트)

## 성격 및 역할
10년 경력 웹소설/판타지 유튜브 SEO 전문가.
회귀물, 이세계물 시청자의 클릭을 유도하는 제목, 설명, 태그를 생성.

## 철학
- "클릭되지 않으면 의미가 없다" - CTR 최적화 우선
- 웹소설 독자 감성을 자극하는 키워드 활용
- 무협+판타지 하이브리드 장르 특성 활용

## 책임
- SEO 최적화된 YouTube 제목 생성 (3가지 스타일)
- 검색 친화적인 설명 작성
- 관련 태그 생성 (최대 500자)
- 썸네일 텍스트 제안

## 제목 스타일
1. hook: 훅 강조 (~의 정체, 드디어 ~가)
2. action: 액션/전투 강조 (~전투, ~격돌, ~각성)
3. series: 시리즈 강조 ([혈영 이세계편] 제N화)

## SEO 원칙
- 제목: 핵심 키워드 앞배치, 50자 이내
- 설명: 첫 2줄에 핵심 정보, 해시태그 포함
- 태그: 장르 → 시리즈 → 에피소드 순서
"""

import re
import time
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentResult, AgentStatus, EpisodeContext


# =====================================================
# 이세계편 제목 템플릿
# =====================================================

TITLE_TEMPLATES = {
    "hook": [
        "{keyword}의 정체가 밝혀지다",
        "드디어 {keyword}",
        "{keyword}, 그 충격적인 진실",
        "모두가 놀란 {keyword}",
        "{keyword}의 반전",
    ],
    "action": [
        "{keyword} 격돌",
        "{keyword} 각성",
        "{keyword} 전투",
        "{keyword} vs {opponent}",
        "최강의 {keyword}",
    ],
    "series": [
        "[혈영 이세계편] 제{ep}화 | {keyword}",
        "혈영 이세계편 {ep}화 - {keyword}",
        "[이세계 무협] 제{ep}화 {keyword}",
    ],
}

# =====================================================
# 파트별 키워드
# =====================================================

PART_KEYWORDS = {
    1: {  # 이방인 (1-10화)
        "themes": ["전이", "각성", "적응", "마나"],
        "characters": ["무영", "카이든", "라이트닝"],
        "keywords": ["이세계", "무림 검객", "마나 각성", "자유도시"],
    },
    2: {  # 검은 별 (11-20화)
        "themes": ["성장", "수련", "소드마스터"],
        "characters": ["무영", "에이라", "볼드릭"],
        "keywords": ["심법", "오러", "소드마스터", "검은 별"],
    },
    3: {  # 용의 친구 (21-30화)
        "themes": ["명성", "동맹", "드래곤"],
        "characters": ["무영", "이그니스", "이그니스 공주", "레인"],
        "keywords": ["드래곤", "용의 친구", "제국", "마왕"],
    },
    4: {  # 대륙의 그림자 (31-40화)
        "themes": ["정치", "음모", "충돌"],
        "characters": ["무영", "혈마", "에이라"],
        "keywords": ["혈마", "마왕군", "전쟁", "엘프"],
    },
    5: {  # 전쟁의 서막 (41-50화)
        "themes": ["연합", "전쟁", "희생"],
        "characters": ["무영", "카이든", "에이라", "이그니스"],
        "keywords": ["연합군", "대전쟁", "9서클", "소드마스터"],
    },
    6: {  # 혈영, 다시 (51-60화)
        "themes": ["결전", "귀환", "완결"],
        "characters": ["무영", "혈마", "설하"],
        "keywords": ["마왕성", "최종 결전", "그랜드 소드마스터", "귀환"],
    },
}

# =====================================================
# 인기 태그
# =====================================================

POPULAR_TAGS = [
    # 장르
    "이세계", "무협", "판타지", "웹소설",
    "회귀물", "먼치킨", "사이다", "성장물",
    # 플랫폼
    "유튜브소설", "웹소설읽어주기", "소설낭독",
    "ASMR소설", "소설TTS", "AI낭독",
    # 시리즈
    "혈영", "혈영이세계편", "무협소설", "판타지소설",
]


class YouTubeAgent(BaseAgent):
    """유튜브 메타데이터 에이전트 (혈영 이세계편 전용)"""

    def __init__(self):
        super().__init__("YouTubeAgent")

        # SEO 설정
        self.max_title_length = 100  # YouTube 최대
        self.optimal_title_length = 50  # 권장
        self.max_description_length = 5000
        self.max_tags_length = 500

        # 시리즈 정보
        self.series_name = "혈영 이세계편"
        self.total_episodes = 60

    async def execute(self, context: EpisodeContext, **kwargs) -> AgentResult:
        """
        YouTube 메타데이터 생성

        Args:
            context: 에피소드 컨텍스트 (script 필수)
            **kwargs:
                style: 제목 스타일 (hook/action/series)
                custom_keywords: 추가 키워드 목록

        Returns:
            AgentResult with YouTube metadata
        """
        self.set_status(AgentStatus.RUNNING)
        start_time = time.time()

        style = kwargs.get("style", "series")
        custom_keywords = kwargs.get("custom_keywords", [])

        context.add_log(
            self.name,
            "메타데이터 생성 시작",
            "running",
            f"스타일: {style}"
        )

        try:
            # 대본 확인
            if not context.script:
                raise ValueError("대본(script)이 없습니다. ScriptAgent를 먼저 실행하세요.")

            script = context.script

            # 파트 정보
            part_num = self._get_part_number(context.episode_number)
            part_info = PART_KEYWORDS.get(part_num, PART_KEYWORDS[1])

            # 키워드 추출
            keywords = self._extract_keywords(script, context, part_info, custom_keywords)

            # 제목 생성 (3가지 스타일)
            titles = self._generate_titles(context, keywords, part_info)

            # 설명 생성
            description = self._generate_description(context, keywords, part_info)

            # 태그 생성
            tags = self._generate_tags(context, keywords, part_info)

            # 썸네일 텍스트 제안
            thumbnail_texts = self._generate_thumbnail_texts(context, keywords)

            # 타임스탬프 제안
            timestamps = self._suggest_timestamps(script, context)

            duration = time.time() - start_time

            context.add_log(
                self.name,
                "메타데이터 생성 완료",
                "success",
                f"제목 3개, 태그 {len(tags)}개"
            )
            self.set_status(AgentStatus.SUCCESS)

            return AgentResult(
                success=True,
                data={
                    "titles": titles,
                    "description": description,
                    "tags": tags,
                    "thumbnail_texts": thumbnail_texts,
                    "timestamps": timestamps,
                    "keywords": keywords,
                    "selected_style": style,
                    "part": part_num,
                },
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            context.add_log(self.name, "메타데이터 생성 실패", "error", error_msg)
            self.set_status(AgentStatus.FAILED)

            return AgentResult(
                success=False,
                error=error_msg,
                duration=duration,
            )

    def _get_part_number(self, episode: int) -> int:
        """에피소드 번호로 파트 번호 계산"""
        if episode <= 0:
            return 1
        return min(6, (episode - 1) // 10 + 1)

    def _extract_keywords(
        self,
        script: str,
        context: EpisodeContext,
        part_info: Dict,
        custom_keywords: List[str]
    ) -> Dict[str, Any]:
        """대본에서 키워드 추출"""

        keywords = {
            "primary": "",  # 메인 키워드
            "secondary": [],  # 서브 키워드
            "characters": [],  # 등장 캐릭터
            "custom": custom_keywords,
        }

        # 1. 제목에서 메인 키워드
        if context.title:
            keywords["primary"] = context.title

        # 2. 파트별 캐릭터 매칭
        for char in part_info.get("characters", []):
            if char in script:
                keywords["characters"].append(char)

        # 3. 파트별 키워드 매칭
        for kw in part_info.get("keywords", []):
            if kw in script and kw not in keywords["secondary"]:
                keywords["secondary"].append(kw)

        # 4. 대본에서 자주 등장하는 이름 추출
        # 주요 캐릭터 이름 패턴
        main_chars = ["무영", "에이라", "카이든", "이그니스", "혈마", "볼드릭", "레인", "설하"]
        for char in main_chars:
            if char in script and char not in keywords["characters"]:
                count = script.count(char)
                if count >= 3:  # 3회 이상 등장
                    keywords["characters"].append(char)

        # 5. 액션 키워드 추출
        action_keywords = ["전투", "각성", "격돌", "검", "마나", "오러", "소드마스터"]
        for kw in action_keywords:
            if kw in script and kw not in keywords["secondary"]:
                keywords["secondary"].append(kw)

        # 중복 제거
        keywords["characters"] = list(dict.fromkeys(keywords["characters"]))[:5]
        keywords["secondary"] = list(dict.fromkeys(keywords["secondary"]))[:10]

        return keywords

    def _generate_titles(
        self,
        context: EpisodeContext,
        keywords: Dict[str, Any],
        part_info: Dict
    ) -> Dict[str, str]:
        """3가지 스타일의 제목 생성"""

        titles = {}
        primary = keywords["primary"] or context.title or "새로운 시작"
        ep_num = context.episode_number or 1

        # 1. Hook 스타일 (호기심 유발)
        hook_templates = TITLE_TEMPLATES["hook"]
        titles["hook"] = hook_templates[0].format(keyword=primary)

        # 주요 캐릭터가 있으면 반영
        if keywords["characters"]:
            main_char = keywords["characters"][0]
            titles["hook"] = f"{main_char}, {primary}"

        # 2. Action 스타일 (액션 강조)
        if keywords["secondary"]:
            action_kw = keywords["secondary"][0]
            titles["action"] = f"{primary} - {action_kw}"
        else:
            titles["action"] = f"무영의 {primary}"

        # 적 캐릭터가 있으면 vs 형식
        if "혈마" in keywords["characters"]:
            titles["action"] = f"무영 vs 혈마 - {primary}"

        # 3. Series 스타일 (시리즈 강조)
        titles["series"] = f"[혈영 이세계편] 제{ep_num}화 | {primary}"

        # 길이 조정
        for style, title in titles.items():
            if len(title) > self.optimal_title_length:
                if style == "series":
                    titles[style] = f"혈영 이세계편 {ep_num}화 - {primary[:15]}"
                else:
                    titles[style] = title[:self.optimal_title_length - 3] + "..."

        return titles

    def _generate_description(
        self,
        context: EpisodeContext,
        keywords: Dict[str, Any],
        part_info: Dict
    ) -> str:
        """SEO 최적화된 설명 생성"""

        primary = keywords["primary"] or context.title
        ep_num = context.episode_number or 1
        part_num = self._get_part_number(ep_num)

        # 파트 제목
        part_titles = {
            1: "이방인", 2: "검은 별", 3: "용의 친구",
            4: "대륙의 그림자", 5: "전쟁의 서막", 6: "혈영, 다시"
        }
        part_title = part_titles.get(part_num, "")

        # 첫 2줄: 핵심 정보 (검색 결과에 표시됨)
        intro = f"🗡️ 혈영 이세계편 제{ep_num}화 - {primary}\n"
        intro += f"무림 최강 검객이 이세계에서 펼치는 새로운 전설!"

        # 파트 정보
        part_line = f"\n\n📖 {part_num}부: {part_title}"

        # 등장인물
        chars = keywords.get("characters", [])
        char_line = ""
        if chars:
            char_line = f"\n\n👥 등장인물: {', '.join(chars[:4])}"

        # 해시태그
        hashtags = [
            "#혈영이세계편", "#이세계무협", "#웹소설",
            "#무협판타지", "#소설낭독", f"#{ep_num}화"
        ]
        # 캐릭터 해시태그
        for char in chars[:2]:
            hashtags.append(f"#{char}")
        hashtag_line = "\n\n" + " ".join(hashtags)

        # 구독 유도
        cta = "\n\n🔔 구독과 좋아요로 무영의 여정을 함께해주세요!"

        # 타임스탬프 플레이스홀더
        timestamps = "\n\n⏰ 타임스탬프\n00:00 오프닝\n(영상 업로드 후 추가)"

        # 시리즈 정보
        series_info = f"\n\n📺 혈영 이세계편 ({ep_num}/60화)"

        description = f"{intro}{part_line}{char_line}{hashtag_line}{cta}{timestamps}{series_info}"

        # 길이 제한
        if len(description) > self.max_description_length:
            description = description[:self.max_description_length - 3] + "..."

        return description

    def _generate_tags(
        self,
        context: EpisodeContext,
        keywords: Dict[str, Any],
        part_info: Dict
    ) -> List[str]:
        """SEO 태그 생성 (장르 → 시리즈 → 에피소드 순)"""

        tags = []

        # 1. 시리즈 태그 (최우선)
        tags.append("혈영이세계편")
        tags.append("혈영")
        tags.append("이세계무협")

        # 2. 장르 태그
        tags.append("이세계")
        tags.append("무협")
        tags.append("판타지")
        tags.append("웹소설")

        # 3. 에피소드 키워드
        primary = keywords["primary"]
        if primary:
            tags.append(primary.replace(" ", ""))

        # 4. 캐릭터 태그
        for char in keywords.get("characters", [])[:3]:
            if char not in tags:
                tags.append(char)

        # 5. 파트별 키워드
        for kw in part_info.get("keywords", [])[:3]:
            if kw not in tags:
                tags.append(kw.replace(" ", ""))

        # 6. 커스텀 키워드
        for kw in keywords.get("custom", []):
            if kw not in tags:
                tags.append(kw)

        # 7. 인기 태그 추가
        for tag in POPULAR_TAGS:
            if tag not in tags and len(",".join(tags)) < self.max_tags_length - 20:
                tags.append(tag)

        return tags

    def _generate_thumbnail_texts(
        self,
        context: EpisodeContext,
        keywords: Dict[str, Any]
    ) -> List[str]:
        """썸네일 텍스트 제안"""

        primary = keywords["primary"] or context.title or "새로운 시작"
        ep_num = context.episode_number or 1

        suggestions = []

        # 1. 에피소드 번호
        suggestions.append(f"제{ep_num}화")

        # 2. 짧은 키워드
        if len(primary) <= 6:
            suggestions.append(primary)
        else:
            suggestions.append(primary[:6])

        # 3. 캐릭터 기반
        chars = keywords.get("characters", [])
        if chars:
            main_char = chars[0]
            if main_char == "무영":
                suggestions.append("무영 각성")
            elif main_char == "혈마":
                suggestions.append("혈마 등장")
            else:
                suggestions.append(f"{main_char}")

        # 4. 훅 텍스트
        hook_texts = [
            "드디어...",
            "충격 반전",
            "각성",
            "최강",
            "vs 혈마",
        ]
        suggestions.extend(hook_texts[:2])

        return suggestions[:5]

    def _suggest_timestamps(
        self,
        script: str,
        context: EpisodeContext
    ) -> List[Dict[str, str]]:
        """타임스탬프 제안 (5막 구조 기준)"""

        # 대본 길이 기준 예상 시간 (910자 ≈ 1분)
        script_length = len(script)
        estimated_duration = script_length / 910  # 분

        timestamps = []

        # 5막 구조 기반 타임스탬프
        # 오프닝(15%) → 전개(22%) → 클라이맥스(28%) → 해결(20%) → 엔딩(15%)
        structure = [
            (0.00, "오프닝"),
            (0.15, "전개"),
            (0.37, "클라이맥스"),
            (0.65, "해결"),
            (0.85, "엔딩"),
        ]

        for ratio, label in structure:
            time_min = estimated_duration * ratio
            mm = int(time_min)
            ss = int((time_min - mm) * 60)
            time_str = f"{mm:02d}:{ss:02d}"
            timestamps.append({"time": time_str, "label": label})

        return timestamps


# =====================================================
# 동기 실행 래퍼
# =====================================================

def generate_youtube_metadata(
    context: EpisodeContext,
    style: str = "series"
) -> Dict[str, Any]:
    """
    YouTube 메타데이터 생성 (동기 버전)

    Args:
        context: 에피소드 컨텍스트 (script 필수)
        style: 제목 스타일 (hook/action/series)

    Returns:
        YouTube 메타데이터
    """
    import asyncio

    agent = YouTubeAgent()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        agent.execute(context, style=style)
    )

    if result.success:
        return result.data
    else:
        raise Exception(result.error)


def quick_metadata(
    title: str,
    episode: int = 1,
    script: str = "",
    style: str = "series"
) -> Dict[str, Any]:
    """
    간단 메타데이터 생성 (컨텍스트 없이)

    Args:
        title: 에피소드 제목
        episode: 에피소드 번호
        script: 대본 (선택)
        style: 제목 스타일

    Returns:
        {titles, description, tags, thumbnail_texts}
    """
    agent = YouTubeAgent()

    # 파트 계산
    part = min(6, (episode - 1) // 10 + 1) if episode > 0 else 1

    # 임시 컨텍스트 생성
    context = EpisodeContext(
        episode_id=f"ep{episode:03d}",
        episode_number=episode,
        era_name="",  # 이세계편에서는 사용 안함
        era_episode=0,
        title=title,
        topic="",
        part=part,
    )
    context.script = script or f"혈영 이세계편 {episode}화 - {title}"

    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(agent.execute(context, style=style))

    if result.success:
        return result.data
    else:
        raise Exception(result.error)

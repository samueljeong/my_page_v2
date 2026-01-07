"""
혈영 이세계편 - Planner Agent (기획 에이전트)

## 성격 및 역할
40년간 웹소설/게임 시나리오를 기획해온 스토리 아키텍트.
"치밀한 계획 없이 좋은 이야기는 없다"는 철학을 가진 전문가.

## 전문 분야
- 장편 판타지/무협 소설 구조 설계
- 캐릭터 아크(성장 곡선) 설계
- 시리즈 바이블 기반 일관성 유지
- 클리프행어와 훅 설계

## 철학
- "스토리는 건축이다" - 견고한 구조 위에 감정을 쌓는다
- "독자의 감정을 설계한다" - 긴장과 해소의 리듬
- "모든 씬에는 목적이 있다" - 불필요한 장면은 없다
- "예측 가능하면서 놀라운" - 복선과 반전의 균형

## 책임
- 에피소드 5막 구조 설계 (오프닝/전개/클라이맥스/해결/엔딩)
- 감정 아크(Emotional Arc) 설계
- 캐릭터 등장/퇴장 타이밍 조율
- Series Bible 준수 검증
- 다음화 클리프행어(훅) 설계
- 하위 에이전트(대본, 검수, 이미지)에게 명확한 방향 제시

## 참조하는 스토리텔링 이론
1. Dan Harmon's Story Circle (8단계)
2. Save the Cat (Blake Snyder)
3. Seven Point Story Structure
4. 기승전결의 동양적 해석
5. 무협소설 특유의 파워 스케일링

## 하위 에이전트 관리
- ScriptAgent: 씬별 목표와 감정톤 명시
- ReviewAgent: 검수 기준과 허용 범위 사전 공유
- ImageAgent: 핵심 시각 요소와 분위기 설정
"""

import time
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentResult, AgentStatus, EpisodeContext


# 5막 구조 템플릿 (14,000자 기준)
FIVE_ACT_STRUCTURE = [
    {
        "act": 1,
        "name": "오프닝",
        "target_chars": 2100,
        "emotional_beat": "호기심 + 몰입",
        "purpose": "훅으로 독자를 사로잡고, 에피소드의 핵심 갈등을 암시",
        "structure_tips": [
            "첫 문장으로 긴장감 또는 미스터리 제시",
            "주인공의 현재 상태/목표 명확히",
            "이전화 연결점 자연스럽게 삽입",
            "핵심 질문 던지기 (이번 화에서 답해야 할)",
        ],
        "dan_harmon_stage": "1. 익숙한 상황 (Comfort Zone)",
    },
    {
        "act": 2,
        "name": "전개",
        "target_chars": 3100,
        "emotional_beat": "기대감 + 긴장 고조",
        "purpose": "갈등 심화, 장애물 제시, 주인공의 선택 강요",
        "structure_tips": [
            "첫 번째 전환점(Plot Point 1) 배치",
            "주인공이 넘어야 할 장애물 명확히",
            "조력자나 적대자 등장/행동",
            "독자가 '어떻게 해결할까?' 궁금해하게",
        ],
        "dan_harmon_stage": "3-4. 미지의 세계 진입 & 적응",
    },
    {
        "act": 3,
        "name": "클라이맥스",
        "target_chars": 3900,
        "emotional_beat": "극도의 긴장 → 카타르시스",
        "purpose": "핵심 대결/결정적 순간, 주인공의 진정한 선택",
        "structure_tips": [
            "이 에피소드의 '가장 강렬한 순간'",
            "전투 씬이라면 가장 위험한 순간",
            "감정적 씬이라면 가장 진실된 순간",
            "주인공이 대가를 치르거나 성장하는 계기",
            "반전이 있다면 여기서 (예상을 뒤엎는 전개)",
        ],
        "dan_harmon_stage": "5-6. 얻고자 하는 것을 찾음 & 대가 지불",
    },
    {
        "act": 4,
        "name": "해결",
        "target_chars": 2800,
        "emotional_beat": "안도감 + 여운",
        "purpose": "갈등 해소, 결과 확인, 의미 부여",
        "structure_tips": [
            "클라이맥스의 결과 정리",
            "주인공의 변화/성장 확인",
            "주변 인물들의 반응",
            "독자에게 감정적 여유 제공",
        ],
        "dan_harmon_stage": "7. 귀환 (Return)",
    },
    {
        "act": 5,
        "name": "엔딩",
        "target_chars": 2100,
        "emotional_beat": "기대감 (다음화)",
        "purpose": "에피소드 마무리 + 다음화 훅(클리프행어)",
        "structure_tips": [
            "이번 화 핵심 메시지 정리",
            "새로운 복선 또는 미스터리 암시",
            "강력한 클리프행어로 마무리",
            "\"다음에 무슨 일이?\" 궁금증 유발",
        ],
        "dan_harmon_stage": "8. 변화된 상태 (Changed)",
    },
]


# 파트별 스토리 포커스
PART_STORY_FOCUS = {
    1: {
        "name": "적응, 각성",
        "episodes": (1, 10),
        "main_theme": "이세계 적응과 능력 각성",
        "emotional_arc": "혼란 → 수용 → 첫 승리",
        "key_elements": [
            "전생의 기억과 새로운 몸의 갈등",
            "혈기창의 발견과 각성",
            "첫 번째 적과의 조우",
            "세계관 규칙 이해",
        ],
        "power_scale": "무영: F급 → D급 (각성)",
        "character_dynamics": "무영 단독 + 라이트닝 (2화~)",
    },
    2: {
        "name": "성장, 소드마스터",
        "episodes": (11, 20),
        "main_theme": "소드마스터로의 성장",
        "emotional_arc": "도전 → 좌절 → 돌파",
        "key_elements": [
            "오의 창조 과정",
            "카이든과의 라이벌리",
            "에이라 등장과 동료 관계",
            "명성 시작",
        ],
        "power_scale": "무영: D급 → B급 (소드마스터 진입)",
        "character_dynamics": "무영 + 카이든(라이벌) + 에이라(12화~)",
    },
    3: {
        "name": "이그니스, 명성",
        "episodes": (21, 30),
        "main_theme": "이그니스 왕국에서의 명성",
        "emotional_arc": "인정 → 책임 → 갈등",
        "key_elements": [
            "기사단 입단",
            "공주와의 인연",
            "첫 대규모 임무",
            "명성과 질시",
        ],
        "power_scale": "무영: B급 → A급",
        "character_dynamics": "무영 + 에이라 + 기사단원들 + 공주",
    },
    4: {
        "name": "혈마 발견, 정치",
        "episodes": (31, 40),
        "main_theme": "혈마의 흔적과 정치적 갈등",
        "emotional_arc": "의심 → 발견 → 분노",
        "key_elements": [
            "혈마의 존재 확인",
            "왕국 내부의 배신자",
            "정치적 음모",
            "동료의 위기",
        ],
        "power_scale": "무영: A급 → A+급",
        "character_dynamics": "복잡한 다자 관계 + 적과 아군의 경계 모호",
    },
    5: {
        "name": "전쟁",
        "episodes": (41, 50),
        "main_theme": "혈마 부활과 대전쟁",
        "emotional_arc": "절망 → 결의 → 희생",
        "key_elements": [
            "혈마 부활",
            "대규모 전투",
            "중요 인물의 희생",
            "무영의 진정한 각성",
        ],
        "power_scale": "무영: A+급 → S급 진입",
        "character_dynamics": "연합군 형성 + 최후의 선택들",
    },
    6: {
        "name": "최종전, 귀환",
        "episodes": (51, 60),
        "main_theme": "최종 결전과 귀환",
        "emotional_arc": "결전 → 승리 → 선택",
        "key_elements": [
            "혈마와의 최종 대결",
            "궁극의 힘 발현",
            "세계 구원",
            "귀환 여부 선택",
        ],
        "power_scale": "무영: S급 → SS급 (최종)",
        "character_dynamics": "모든 인연의 결산",
    },
}


# 캐릭터 등장 타임라인
CHARACTER_TIMELINE = {
    "무영 (주인공)": {"first_appear": 1, "type": "protagonist"},
    "라이트닝 (늑대)": {"first_appear": 2, "type": "companion"},
    "카이든 (라이벌)": {"first_appear": 5, "type": "rival"},
    "에이라 (히로인)": {"first_appear": 12, "type": "heroine"},
    "이그니스 공주": {"first_appear": 21, "type": "supporting"},
    "기사단장": {"first_appear": 22, "type": "mentor"},
    "혈마": {"first_appear": 35, "type": "antagonist", "note": "암시는 20화부터"},
}


class PlannerAgent(BaseAgent):
    """
    기획 에이전트 - 40년 경력의 스토리 아키텍트

    핵심 역량:
    - 5막 구조 설계
    - 감정 아크 설계
    - Series Bible 준수
    - 캐릭터 동선 조율
    """

    def __init__(self):
        super().__init__("PlannerAgent")

        # 스토리 설정
        self.total_episodes = 60
        self.target_length = 14000  # 목표 글자수
        self.five_act_structure = FIVE_ACT_STRUCTURE
        self.part_focus = PART_STORY_FOCUS

    async def execute(self, context: EpisodeContext, **kwargs) -> AgentResult:
        """
        에피소드 기획 실행

        Args:
            context: 에피소드 컨텍스트
            **kwargs:
                feedback: 검수 피드백 (개선 시)
                series_bible: Series Bible 텍스트

        Returns:
            AgentResult with brief data
        """
        self.set_status(AgentStatus.RUNNING)
        start_time = time.time()

        feedback = kwargs.get("feedback")
        is_improvement = feedback is not None

        context.brief_attempts += 1
        context.add_log(
            self.name,
            "기획 시작" if not is_improvement else "기획 개선",
            "running",
            f"EP{context.episode_number:03d} - 시도 {context.brief_attempts}/{context.max_attempts}"
        )

        try:
            # Series Bible 확인
            series_bible = kwargs.get("series_bible") or context.series_bible

            # 기획서 생성
            brief = self._generate_brief(context, feedback, series_bible)

            context.brief = brief
            duration = time.time() - start_time

            context.add_log(
                self.name,
                f"기획 완료: {brief['title']}",
                "success",
                f"{duration:.1f}초"
            )
            self.set_status(AgentStatus.SUCCESS)

            return AgentResult(
                success=True,
                data={"brief": brief},
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            context.add_log(self.name, "기획 실패", "error", error_msg)
            self.set_status(AgentStatus.FAILED)

            return AgentResult(
                success=False,
                error=error_msg,
                duration=duration,
            )

    def _generate_brief(
        self,
        context: EpisodeContext,
        feedback: Optional[str] = None,
        series_bible: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        에피소드 기획서 생성

        40년 경력의 스토리 아키텍트가 설계하는 기획서:
        - 5막 구조 기반
        - 감정 아크 설계
        - 캐릭터 동선
        - 다음화 훅
        """
        episode_num = context.episode_number
        part = context.part
        part_info = self.part_focus.get(part, self.part_focus[1])

        # 에피소드 위치 분석
        episode_position = self._analyze_episode_position(episode_num, part)

        # 5막 구조 커스터마이징
        scenes = self._customize_five_act_structure(context, part_info, episode_position)

        # 감정 아크 설계
        emotional_arc = self._design_emotional_arc(episode_position, part_info)

        # 캐릭터 동선
        available_characters = self._get_available_characters(episode_num)

        # 훅 생성
        opening_hook = self._generate_opening_hook(context, part_info, episode_position)
        ending_hook = self._generate_ending_hook(context, part_info, episode_position)

        # 이전/다음 에피소드 연결점
        connection_points = self._design_connection_points(context)

        brief = {
            # 기본 정보
            "episode_id": context.episode_id,
            "episode_number": episode_num,
            "part": part,
            "part_name": part_info["name"],
            "title": context.title if context.title else f"EP{episode_num:03d}",

            # 스토리 위치
            "episode_position": episode_position,
            "position_in_part": episode_position["position_in_part"],
            "overall_progress": f"{episode_num}/60 ({episode_num/60*100:.0f}%)",

            # 핵심 기획
            "hook": opening_hook,
            "scenes": scenes,
            "emotional_arc": emotional_arc,
            "ending_hook": ending_hook,

            # 캐릭터
            "available_characters": available_characters,
            "recommended_focus": self._recommend_character_focus(episode_num, available_characters),

            # 연결성
            "connection_points": connection_points,

            # 메타 정보
            "target_length": self.target_length,
            "tone": self._determine_tone(part, episode_position),
            "power_scale": part_info.get("power_scale", ""),

            # 하위 에이전트 가이드
            "script_guide": self._generate_script_guide(scenes, emotional_arc),
            "image_guide": self._generate_image_guide(scenes, part, episode_position),
            "review_criteria": self._generate_review_criteria(part_info, episode_position),

            # 피드백 반영
            "feedback_applied": feedback,
        }

        return brief

    def _analyze_episode_position(
        self,
        episode_num: int,
        part: int
    ) -> Dict[str, Any]:
        """에피소드 위치 분석 (시리즈 내 맥락)"""
        part_info = self.part_focus.get(part, self.part_focus[1])
        part_start, part_end = part_info["episodes"]

        # 파트 내 위치
        episode_in_part = episode_num - part_start + 1
        part_length = part_end - part_start + 1
        position_ratio = episode_in_part / part_length

        # 위치 판단
        if position_ratio <= 0.3:
            position_in_part = "초반"
            position_role = "setup"  # 설정 단계
        elif position_ratio <= 0.7:
            position_in_part = "중반"
            position_role = "development"  # 전개 단계
        else:
            position_in_part = "후반"
            position_role = "climax"  # 절정 단계

        # 시리즈 전체 내 위치
        series_ratio = episode_num / self.total_episodes
        if series_ratio <= 0.2:
            series_position = "서막"
        elif series_ratio <= 0.4:
            series_position = "상승"
        elif series_ratio <= 0.6:
            series_position = "중반"
        elif series_ratio <= 0.8:
            series_position = "절정"
        else:
            series_position = "대단원"

        return {
            "episode_in_part": episode_in_part,
            "part_length": part_length,
            "position_ratio": position_ratio,
            "position_in_part": position_in_part,
            "position_role": position_role,
            "series_position": series_position,
            "is_part_finale": episode_num == part_end,
            "is_part_opener": episode_num == part_start,
        }

    def _customize_five_act_structure(
        self,
        context: EpisodeContext,
        part_info: Dict[str, Any],
        episode_position: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """5막 구조를 에피소드 특성에 맞게 커스터마이징"""
        scenes = []

        for act in self.five_act_structure:
            scene = {
                "act": act["act"],
                "name": act["name"],
                "target_chars": act["target_chars"],
                "emotional_beat": act["emotional_beat"],
                "purpose": act["purpose"],
                "tips": act["structure_tips"].copy(),
            }

            # 파트 파이널레인 경우 클라이맥스 강화
            if episode_position["is_part_finale"] and act["name"] == "클라이맥스":
                scene["target_chars"] += 500
                scene["tips"].append("★ 파트 피날레: 이 파트의 모든 복선 회수")
                scene["emotional_beat"] = "극적인 절정 + 파트 마무리"

            # 파트 오프너인 경우 설정 강화
            if episode_position["is_part_opener"] and act["name"] == "오프닝":
                scene["tips"].append("★ 파트 시작: 새로운 무대/상황 소개")
                scene["tips"].append("이전 파트와의 시간적 연결 명시")

            # 시리즈 후반부면 긴장감 강화
            if episode_position["series_position"] in ["절정", "대단원"]:
                if act["name"] == "클라이맥스":
                    scene["tips"].append("시리즈 대미를 향한 스케일 확대")

            scenes.append(scene)

        return scenes

    def _design_emotional_arc(
        self,
        episode_position: Dict[str, Any],
        part_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """감정 아크 설계"""
        base_arc = part_info.get("emotional_arc", "도전 → 시련 → 성장")

        # 에피소드 내 감정 흐름 (1~10 스케일)
        emotional_curve = {
            "오프닝": {"tension": 4, "hope": 6, "mystery": 7},
            "전개": {"tension": 6, "hope": 5, "mystery": 5},
            "클라이맥스": {"tension": 9, "hope": 4, "mystery": 3},
            "해결": {"tension": 3, "hope": 8, "mystery": 4},
            "엔딩": {"tension": 5, "hope": 7, "mystery": 8},
        }

        # 파트 파이널레면 전체적으로 긴장감 상승
        if episode_position["is_part_finale"]:
            for act in emotional_curve:
                emotional_curve[act]["tension"] = min(10, emotional_curve[act]["tension"] + 2)

        return {
            "part_arc": base_arc,
            "episode_curve": emotional_curve,
            "peak_moment": "클라이맥스 후반부",
            "catharsis_point": "해결 초반부",
            "hook_tension": "엔딩 마지막 문장",
        }

    def _get_available_characters(self, episode_num: int) -> List[Dict[str, Any]]:
        """해당 에피소드에서 사용 가능한 캐릭터 목록"""
        available = []

        for char_name, info in CHARACTER_TIMELINE.items():
            if episode_num >= info["first_appear"]:
                char_data = {
                    "name": char_name,
                    "type": info["type"],
                    "first_appear": info["first_appear"],
                    "episodes_since_intro": episode_num - info["first_appear"],
                }
                if "note" in info:
                    char_data["note"] = info["note"]
                available.append(char_data)

        return available

    def _recommend_character_focus(
        self,
        episode_num: int,
        available_characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """캐릭터 포커스 추천"""
        # 주인공은 항상 포함
        main = "무영 (주인공)"

        # 파트별 추천
        if episode_num <= 10:
            secondary = "라이트닝 (늑대)" if episode_num >= 2 else None
            focus = "무영의 각성과 적응"
        elif episode_num <= 20:
            secondary = "에이라 (히로인)" if episode_num >= 12 else "카이든 (라이벌)"
            focus = "성장과 라이벌리"
        elif episode_num <= 30:
            secondary = "이그니스 공주" if episode_num >= 21 else "에이라 (히로인)"
            focus = "명성과 인정"
        elif episode_num <= 40:
            secondary = "기사단장" if episode_num >= 22 else "에이라 (히로인)"
            focus = "음모와 발견"
        elif episode_num <= 50:
            secondary = "혈마" if episode_num >= 35 else "에이라 (히로인)"
            focus = "전쟁과 희생"
        else:
            secondary = "에이라 (히로인)"
            focus = "최종 결전"

        return {
            "main_focus": main,
            "secondary_focus": secondary,
            "episode_focus": focus,
        }

    def _generate_opening_hook(
        self,
        context: EpisodeContext,
        part_info: Dict[str, Any],
        episode_position: Dict[str, Any]
    ) -> str:
        """오프닝 훅 생성"""
        episode_num = context.episode_number

        # 훅 템플릿
        hook_templates = {
            "action": "검기가 허공을 갈랐다. 무영의 눈앞에 [상황]이 펼쳐졌다.",
            "mystery": "이상했다. [이상한 점]이 분명했다.",
            "emotion": "가슴이 뛰었다. [감정의 원인].",
            "dialogue": "\"[대사].\" [화자]의 목소리가 울렸다.",
            "description": "[장면 묘사]. 무영은 [행동/생각].",
        }

        # 에피소드 위치에 따른 훅 유형 선택
        if episode_position["is_part_opener"]:
            hook_type = "description"  # 새로운 무대 소개
        elif episode_position["position_role"] == "climax":
            hook_type = "action"  # 긴박감
        elif episode_position["position_in_part"] == "초반":
            hook_type = "mystery"  # 복선 투척
        else:
            hook_type = "emotion"  # 캐릭터 내면

        return hook_templates.get(hook_type, hook_templates["action"])

    def _generate_ending_hook(
        self,
        context: EpisodeContext,
        part_info: Dict[str, Any],
        episode_position: Dict[str, Any]
    ) -> str:
        """엔딩 훅(클리프행어) 생성"""
        # 다음 에피소드 정보 확인
        next_ep = context.next_episode

        # 클리프행어 유형
        cliffhanger_types = {
            "revelation": "그 순간, 무영은 깨달았다. [충격적 사실].",
            "danger": "하지만 무영은 미처 알지 못했다. [위험]이 다가오고 있다는 것을.",
            "arrival": "그때, [누군가]가 나타났다.",
            "decision": "무영은 결심했다. [결심 내용].",
            "question": "과연 [질문]?",
        }

        # 파트 파이널레면 더 강한 클리프행어
        if episode_position["is_part_finale"]:
            return cliffhanger_types["revelation"]

        # 위치에 따른 선택
        if episode_position["position_role"] == "setup":
            return cliffhanger_types["question"]
        elif episode_position["position_role"] == "development":
            return cliffhanger_types["danger"]
        else:
            return cliffhanger_types["decision"]

    def _design_connection_points(
        self,
        context: EpisodeContext
    ) -> Dict[str, Any]:
        """이전/다음 에피소드 연결점 설계"""
        connections = {
            "from_previous": [],
            "to_next": [],
        }

        # 이전 에피소드 연결
        if context.prev_episode:
            prev_title = context.prev_episode.get("title", "이전화")
            connections["from_previous"] = [
                f"'{prev_title}'에서 이어지는 상황 확인",
                "해결되지 않은 갈등 언급",
                "캐릭터의 감정 상태 이어받기",
            ]

        # 다음 에피소드 연결
        if context.next_episode:
            next_title = context.next_episode.get("title", "다음화")
            connections["to_next"] = [
                f"'{next_title}'를 위한 복선 배치",
                "해결되지 않은 질문 남기기",
                "새로운 위기의 암시",
            ]

        return connections

    def _determine_tone(
        self,
        part: int,
        episode_position: Dict[str, Any]
    ) -> Dict[str, str]:
        """에피소드 톤 결정"""
        base_tones = {
            1: "적응과 희망, 신비로움",
            2: "성장통과 라이벌리, 열정",
            3: "영광과 책임, 화려함",
            4: "의심과 배신, 어둠",
            5: "절망과 결의, 비장함",
            6: "결전과 희망, 장엄함",
        }

        return {
            "base_tone": base_tones.get(part, "모험과 성장"),
            "position_modifier": episode_position["position_in_part"],
            "recommended_bgm_mood": self._get_bgm_mood(part, episode_position),
        }

    def _get_bgm_mood(
        self,
        part: int,
        episode_position: Dict[str, Any]
    ) -> List[str]:
        """BGM 분위기 추천"""
        moods = {
            "오프닝": ["mysterious", "tense"],
            "전개": ["dramatic", "inspiring"],
            "클라이맥스": ["epic", "tense"],
            "해결": ["hopeful", "calm"],
            "엔딩": ["mysterious", "dramatic"],
        }

        # 파트에 따른 조정
        if part >= 5:  # 전쟁/최종전
            moods["클라이맥스"] = ["epic", "horror"]
            moods["해결"] = ["sad", "hopeful"]

        return moods

    def _generate_script_guide(
        self,
        scenes: List[Dict[str, Any]],
        emotional_arc: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ScriptAgent를 위한 가이드"""
        return {
            "scenes": scenes,
            "emotional_curve": emotional_arc["episode_curve"],
            "style_requirements": [
                "무협 소설체 (의성어/의태어 활용)",
                "오감 묘사로 몰입감 강화",
                "한자어 허용, 외래어 금지",
                "대화 비중 30~40%",
                "내면 독백 적절히 배치",
            ],
            "pacing_notes": [
                "클라이맥스에서 문장 짧게",
                "해결에서 호흡 길게",
                "전환점에서 줄바꿈 활용",
            ],
        }

    def _generate_image_guide(
        self,
        scenes: List[Dict[str, Any]],
        part: int,
        episode_position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ImageAgent를 위한 가이드"""
        return {
            "total_images": len(scenes) + 1,  # 씬별 + 썸네일
            "style_base": "korean martial arts fantasy, manhwa style",
            "color_mood": "dark fantasy with magical glow",
            "key_scenes": [
                {"scene": "클라이맥스", "priority": "high", "focus": "action/emotion"},
                {"scene": "오프닝", "priority": "medium", "focus": "atmosphere"},
            ],
            "avoid": [
                "밝은 톤의 배경 (다크 판타지 유지)",
                "현대적 요소",
                "텍스트/로고",
            ],
        }

    def _generate_review_criteria(
        self,
        part_info: Dict[str, Any],
        episode_position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ReviewAgent를 위한 검수 기준"""
        return {
            "must_check": [
                "Series Bible 캐릭터 설정 준수",
                "파워 스케일 일관성",
                "이전화 연결 확인",
            ],
            "critical_for_this_episode": [
                f"파트 {part_info['name']} 테마 반영",
                f"감정 아크: {part_info['emotional_arc']}",
            ],
            "pass_threshold": "B등급 이상",
            "special_attention": (
                "파트 피날레 퀄리티 검증" if episode_position["is_part_finale"]
                else "일반 검수"
            ),
        }


# 동기 실행 래퍼
def plan_episode(
    context: EpisodeContext,
    feedback: str = None,
    series_bible: str = None
) -> Dict[str, Any]:
    """
    에피소드 기획 (동기 버전)

    Args:
        context: 에피소드 컨텍스트
        feedback: 검수 피드백
        series_bible: Series Bible 텍스트

    Returns:
        기획서 딕셔너리
    """
    import asyncio

    agent = PlannerAgent()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        agent.execute(context, feedback=feedback, series_bible=series_bible)
    )

    if result.success:
        return result.data.get("brief", {})
    else:
        raise Exception(result.error)


def get_part_info(episode_number: int) -> Dict[str, Any]:
    """에피소드 번호로 파트 정보 조회"""
    for part_num, info in PART_STORY_FOCUS.items():
        start, end = info["episodes"]
        if start <= episode_number <= end:
            return {
                "part": part_num,
                "name": info["name"],
                "main_theme": info["main_theme"],
                "emotional_arc": info["emotional_arc"],
                "power_scale": info["power_scale"],
            }
    return PART_STORY_FOCUS[1]


def get_available_characters(episode_number: int) -> List[str]:
    """해당 에피소드에서 사용 가능한 캐릭터 이름 목록"""
    available = []
    for char_name, info in CHARACTER_TIMELINE.items():
        if episode_number >= info["first_appear"]:
            available.append(char_name)
    return available

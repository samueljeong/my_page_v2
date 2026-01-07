"""
혈영 이세계편 - Review Agent (검수 에이전트)

## 성격 및 역할
40년간 출판사에서 편집장으로 근무한 베테랑 편집자.
"타협 없는 품질"을 추구하는 깐깐한 전문가.

## 전문 분야
- 웹소설/라이트노벨 편집 경험
- 무협/판타지 장르 전문
- 시리즈물 일관성 검증
- TTS 최적화 문장 검토

## 철학
- "한 번 통과한 대본은 완벽해야 한다"
- "작은 오류가 전체 몰입을 깬다"
- "비판이 아닌 개선을 위한 피드백"
- "Series Bible은 절대 법칙이다"

## 책임
- 대본 품질 검수 (길이, 문체, 구조)
- Series Bible 준수 여부 검증
- 캐릭터 일관성 확인
- 스토리 연결성 검토
- 구체적이고 실행 가능한 피드백 생성
- 최종 승인/반려 결정 (S/A/B/C/D 등급)

## 검수 기준
- 길이: 12,000~15,000자 (30점)
- 구조: 5막 구조 준수 (20점)
- 문체: 무협 소설체, 대화 비율 (20점)
- 일관성: Series Bible 준수, 캐릭터 (20점)
- 몰입도: 훅, 클라이맥스, 클리프행어 (10점)

## 통과 기준
- S등급 (90점+): 즉시 통과, 수정 불필요
- A등급 (80-89점): 사소한 수정 후 통과
- B등급 (70-79점): 수정 필요
- C/D등급: 재작성 필요
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseAgent, AgentResult, AgentStatus, EpisodeContext


# =============================================================================
# 검수 기준 상세
# =============================================================================
REVIEW_CRITERIA = """
## 대본 검수 기준 (혈영 이세계편)

### 1. 길이 검수 (30점)
| 글자수 | 점수 | 판정 |
|--------|------|------|
| 12,000~15,000자 | 30점 | PASS |
| 11,000~12,000 또는 15,000~16,000 | 20점 | WARNING |
| 그 외 | 10점 | FAIL |

### 2. 구조 검수 (20점)
- 5막 구조 준수 (오프닝/전개/클라이맥스/해결/엔딩)
- 각 막의 글자수 비율 적절 (±20%)
- 씬 전환의 자연스러움

### 3. 문체 검수 (20점)
- 무협 소설체 사용 (의성어/의태어)
- 대화 비율 30-40%
- TTS 최적화 (문장 길이 15-50자)
- 금지 표현 미사용 (외래어, 현대 용어)

### 4. 일관성 검수 (20점)
- Series Bible 캐릭터 설정 준수
- 파워 스케일 일관성
- 이전 에피소드와의 연결
- 등장 타이밍 준수 (카이든 5화~, 에이라 12화~)

### 5. 몰입도 검수 (10점)
- 오프닝 훅의 강도
- 클라이맥스 긴장감
- 엔딩 클리프행어
- 감정선 흐름

### 등급 기준
| 등급 | 점수 | 조치 |
|------|------|------|
| S | 90-100 | 즉시 통과 |
| A | 80-89 | 사소한 수정 후 통과 |
| B | 70-79 | 수정 필요 |
| C | 60-69 | 대폭 수정 필요 |
| D | 60 미만 | 재작성 필요 |
"""


# =============================================================================
# 금지 표현 목록
# =============================================================================
FORBIDDEN_EXPRESSIONS = {
    "foreign_words": [
        "어택", "디펜스", "스킬", "버프", "너프", "대미지",
        "HP", "MP", "레벨업", "스테이터스", "인벤토리",
        "퀘스트", "미션", "보스", "몹", "NPC",
    ],
    "modern_slang": [
        "미쳤다", "대박", "존잼", "갓", "레전드", "역대급",
        "쩐다", "개쩔어", "존버", "핵노잼",
    ],
    "academic_hedging": [
        "단정하기 어렵습니다",
        "해석이 갈립니다",
        "알 수 없습니다",
        "추측입니다",
        "아마도",
    ],
}


# =============================================================================
# 캐릭터 등장 타이밍 (Series Bible)
# =============================================================================
CHARACTER_TIMELINE = {
    "무영": 1,
    "라이트닝": 2,
    "카이든": 5,
    "에이라": 12,
    "이그니스 공주": 21,
    "공주": 21,
    "기사단장": 22,
    "혈마": 35,  # 본격 등장, 암시는 20화부터
}


# =============================================================================
# 파워 스케일 (Series Bible)
# =============================================================================
POWER_SCALE = {
    (1, 5): {"무영": "F급", "enemies": "일반 몬스터"},
    (6, 10): {"무영": "D급", "enemies": "중급 몬스터"},
    (11, 15): {"무영": "C급", "enemies": "상급 몬스터"},
    (16, 20): {"무영": "B급 진입", "enemies": "A급 이하 적"},
    (21, 30): {"무영": "B~A급", "enemies": "A급 적"},
    (31, 40): {"무영": "A~A+급", "enemies": "A+급 + 혈마 암시"},
    (41, 50): {"무영": "A+~S급 진입", "enemies": "S급 + 혈마군"},
    (51, 60): {"무영": "S~SS급", "enemies": "혈마"},
}


class ReviewAgent(BaseAgent):
    """
    검수 에이전트 - 40년 경력의 베테랑 편집자

    핵심 역량:
    - 무협/판타지 장르 전문 편집
    - Series Bible 일관성 검증
    - 깐깐하고 구체적인 피드백
    - 품질 타협 없음
    """

    def __init__(self):
        super().__init__("ReviewAgent")

        # 검수 설정
        self.min_length = 12000
        self.max_length = 15000
        self.target_length = 14000

        # 구조 설정 (5막 비율)
        self.structure_ratios = {
            "오프닝": 0.15,   # 2,100 / 14,000
            "전개": 0.22,     # 3,100 / 14,000
            "클라이맥스": 0.28,  # 3,900 / 14,000
            "해결": 0.20,     # 2,800 / 14,000
            "엔딩": 0.15,     # 2,100 / 14,000
        }

        # 금지 표현
        self.forbidden = FORBIDDEN_EXPRESSIONS

    async def execute(self, context: EpisodeContext, **kwargs) -> AgentResult:
        """
        대본 검수 실행

        Args:
            context: 에피소드 컨텍스트 (script 필수)
            **kwargs:
                strict: 엄격 모드 (기본 False)

        Returns:
            AgentResult with review data
        """
        self.set_status(AgentStatus.RUNNING)
        start_time = time.time()

        strict = kwargs.get("strict", False)

        context.add_log(
            self.name,
            "대본 검수 시작",
            "running",
            f"EP{context.episode_number:03d}, 엄격 모드: {strict}"
        )

        try:
            # 대본 확인
            if not context.script:
                raise ValueError("대본(script)이 없습니다. ScriptAgent를 먼저 실행하세요.")

            script = context.script

            # 5개 영역 검수
            scores = self._evaluate_all(script, context)

            # 총점 및 등급 계산
            total_score = sum(scores.values())
            grade = self._calculate_grade(total_score)

            # 피드백 생성
            feedback = self._generate_feedback(script, scores, context)

            # 통과 여부 결정
            passed = self._determine_pass(grade, strict)

            duration = time.time() - start_time

            result_status = "success" if passed else "warning"
            context.add_log(
                self.name,
                f"검수 완료: {grade}등급 ({total_score}점)",
                result_status,
                f"통과: {passed}"
            )

            if passed:
                self.set_status(AgentStatus.SUCCESS)
            else:
                self.set_status(AgentStatus.WAITING_REVIEW)

            return AgentResult(
                success=True,
                data={
                    "scores": scores,
                    "total_score": total_score,
                    "grade": grade,
                    "passed": passed,
                    "feedback": feedback,
                    "review_criteria": REVIEW_CRITERIA,
                },
                duration=duration,
                needs_improvement=not passed,
                feedback=feedback.get("summary", ""),
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            context.add_log(self.name, "검수 실패", "error", error_msg)
            self.set_status(AgentStatus.FAILED)

            return AgentResult(
                success=False,
                error=error_msg,
                duration=duration,
            )

    def _evaluate_all(
        self,
        script: str,
        context: EpisodeContext
    ) -> Dict[str, int]:
        """전체 검수 실행"""
        scores = {}

        # 1. 길이 검수 (30점)
        scores["length"] = self._evaluate_length(script)

        # 2. 구조 검수 (20점)
        scores["structure"] = self._evaluate_structure(script, context)

        # 3. 문체 검수 (20점)
        scores["style"] = self._evaluate_style(script)

        # 4. 일관성 검수 (20점)
        scores["consistency"] = self._evaluate_consistency(script, context)

        # 5. 몰입도 검수 (10점)
        scores["immersion"] = self._evaluate_immersion(script, context)

        return scores

    def _evaluate_length(self, script: str) -> int:
        """길이 검수 (30점 만점)"""
        length = len(script)

        if self.min_length <= length <= self.max_length:
            return 30
        elif 11000 <= length < self.min_length or self.max_length < length <= 16000:
            return 20
        else:
            return 10

    def _evaluate_structure(
        self,
        script: str,
        context: EpisodeContext
    ) -> int:
        """구조 검수 (20점 만점)"""
        score = 0

        # 씬 분할이 있으면 확인
        scenes = context.scenes
        if scenes and len(scenes) == 5:
            # 5막 구조 확인
            scene_names = ["오프닝", "전개", "클라이맥스", "해결", "엔딩"]
            total_length = sum(len(s) for s in scenes)

            for i, (name, scene) in enumerate(zip(scene_names, scenes)):
                expected_ratio = self.structure_ratios.get(name, 0.2)
                actual_ratio = len(scene) / total_length if total_length > 0 else 0

                # ±20% 이내면 OK
                if abs(actual_ratio - expected_ratio) <= 0.2 * expected_ratio:
                    score += 4

            return min(score, 20)

        # 씬 분할이 없으면 대본 자체 분석
        paragraphs = [p for p in script.split("\n\n") if len(p.strip()) > 100]

        if len(paragraphs) >= 5:
            score = 15
        elif len(paragraphs) >= 3:
            score = 10
        else:
            score = 5

        # 씬 전환 표현 확인
        transition_keywords = ["그때", "얼마나 지났을까", "다음 순간", "시간이 흘렀"]
        transition_count = sum(1 for kw in transition_keywords if kw in script)
        if transition_count >= 3:
            score = min(score + 5, 20)

        return score

    def _evaluate_style(self, script: str) -> int:
        """문체 검수 (20점 만점)"""
        score = 0

        # 1. 의성어/의태어 사용 (5점)
        onomatopoeia = [
            "쩌렁", "휘이잉", "우지직", "쾅", "파직", "스르륵",
            "두근", "쿵쾅", "치직", "펄럭", "휙"
        ]
        found_onomatopoeia = sum(1 for w in onomatopoeia if w in script)
        if found_onomatopoeia >= 5:
            score += 5
        elif found_onomatopoeia >= 3:
            score += 3
        elif found_onomatopoeia >= 1:
            score += 1

        # 2. 대화 비율 (5점)
        dialogue_count = script.count('"') // 2
        script_length = len(script)
        # 대략 150자당 1회 대화 = 30-40% 비율
        expected_dialogues = script_length // 200  # 200자당 1회가 30% 정도
        if dialogue_count >= expected_dialogues * 0.8:
            score += 5
        elif dialogue_count >= expected_dialogues * 0.5:
            score += 3
        else:
            score += 1

        # 3. 금지 표현 미사용 (5점)
        penalty = 0

        # 외래어
        for word in self.forbidden["foreign_words"]:
            if word in script:
                penalty += 2

        # 현대 용어
        for word in self.forbidden["modern_slang"]:
            if word in script:
                penalty += 1

        style_score = max(0, 5 - penalty)
        score += style_score

        # 4. TTS 최적화 (5점)
        sentences = re.split(r'[.!?]', script)
        long_sentences = [s for s in sentences if len(s.strip()) > 60]
        short_sentences = [s for s in sentences if 15 <= len(s.strip()) <= 50]

        if len(long_sentences) < 10 and len(short_sentences) > len(sentences) * 0.5:
            score += 5
        elif len(long_sentences) < 20:
            score += 3
        else:
            score += 1

        return min(score, 20)

    def _evaluate_consistency(
        self,
        script: str,
        context: EpisodeContext
    ) -> int:
        """일관성 검수 (20점 만점)"""
        score = 20  # 감점제
        issues = []

        episode_num = context.episode_number

        # 1. 캐릭터 등장 타이밍 검증 (10점)
        for char_name, first_episode in CHARACTER_TIMELINE.items():
            if char_name in script and episode_num < first_episode:
                issues.append(f"{char_name}이(가) {first_episode}화 이전에 등장")
                score -= 5

        # 2. 파워 스케일 검증 (5점)
        for (start, end), power_info in POWER_SCALE.items():
            if start <= episode_num <= end:
                muying_power = power_info["무영"]
                # S급, SS급 같은 표현이 너무 일찍 나오면 감점
                if episode_num < 40:
                    if "SS급" in script or "SS급" in script:
                        issues.append("SS급 표현이 너무 일찍 등장")
                        score -= 3
                    if episode_num < 20 and "S급" in script:
                        issues.append("S급 표현이 너무 일찍 등장")
                        score -= 2
                break

        # 3. 이전 에피소드 연결 (5점)
        if context.prev_episode and episode_num > 1:
            # 이전화 제목이나 내용 언급 확인
            prev_title = context.prev_episode.get("title", "")
            # 연결 키워드
            connection_keywords = ["저번", "지난", "이전", "그때", "그 일"]
            has_connection = any(kw in script for kw in connection_keywords)

            if not has_connection and episode_num > 3:
                issues.append("이전 에피소드와의 연결 부족")
                score -= 3

        return max(0, score)

    def _evaluate_immersion(
        self,
        script: str,
        context: EpisodeContext
    ) -> int:
        """몰입도 검수 (10점 만점)"""
        score = 0

        # 1. 오프닝 훅 (3점)
        intro = script[:500]
        hook_indicators = [
            "검기", "검이", "눈앞", "순간", "그때",
            "상상", "생각해", "만약", "이상했다"
        ]
        has_hook = any(indicator in intro for indicator in hook_indicators)
        if has_hook and "?" in intro:
            score += 3
        elif has_hook or "?" in intro:
            score += 2
        else:
            score += 1

        # 2. 클라이맥스 긴장감 (4점)
        # 중간 40% 영역에서 긴장감 키워드 확인
        middle_start = int(len(script) * 0.35)
        middle_end = int(len(script) * 0.65)
        middle = script[middle_start:middle_end]

        tension_keywords = [
            "긴장", "위험", "목숨", "죽", "피", "검기",
            "공격", "방어", "회피", "전투"
        ]
        tension_count = sum(1 for kw in tension_keywords if kw in middle)

        if tension_count >= 10:
            score += 4
        elif tension_count >= 5:
            score += 3
        elif tension_count >= 2:
            score += 2
        else:
            score += 1

        # 3. 엔딩 클리프행어 (3점)
        outro = script[-500:]
        cliffhanger_patterns = [
            r"하지만.+않았다",
            r"그때.+나타났다",
            r"과연.+\?",
            r"깨달았다",
            r"시작.+불과",
            r"끝이 아니",
        ]
        has_cliffhanger = any(re.search(p, outro) for p in cliffhanger_patterns)

        if has_cliffhanger:
            score += 3
        elif "?" in outro or "..." in outro:
            score += 2
        else:
            score += 1

        return min(score, 10)

    def _calculate_grade(self, total_score: int) -> str:
        """등급 계산"""
        if total_score >= 90:
            return "S"
        elif total_score >= 80:
            return "A"
        elif total_score >= 70:
            return "B"
        elif total_score >= 60:
            return "C"
        else:
            return "D"

    def _determine_pass(self, grade: str, strict: bool) -> bool:
        """통과 여부 결정"""
        if strict:
            return grade in ["S", "A"]
        else:
            return grade in ["S", "A", "B"]

    def _generate_feedback(
        self,
        script: str,
        scores: Dict[str, int],
        context: EpisodeContext
    ) -> Dict[str, Any]:
        """피드백 생성"""
        feedback = {
            "summary": "",
            "strengths": [],
            "improvements": [],
            "critical_issues": [],
            "details": {},
        }

        length = len(script)

        # 1. 길이 피드백
        if scores["length"] == 30:
            feedback["strengths"].append(f"길이 적절 ({length:,}자)")
        elif scores["length"] == 20:
            if length < self.min_length:
                diff = self.min_length - length
                feedback["improvements"].append(
                    f"대본이 {diff:,}자 부족합니다 (현재 {length:,}자, 최소 {self.min_length:,}자)"
                )
            else:
                diff = length - self.max_length
                feedback["improvements"].append(
                    f"대본이 {diff:,}자 초과입니다 (현재 {length:,}자, 최대 {self.max_length:,}자)"
                )
        else:
            feedback["critical_issues"].append(
                f"대본 길이가 기준 범위를 크게 벗어남 ({length:,}자)"
            )

        # 2. 구조 피드백
        if scores["structure"] >= 18:
            feedback["strengths"].append("5막 구조가 잘 구성됨")
        elif scores["structure"] < 12:
            feedback["improvements"].append(
                "5막 구조 (오프닝/전개/클라이맥스/해결/엔딩) 명확히 구분 필요"
            )

        # 3. 문체 피드백
        if scores["style"] >= 17:
            feedback["strengths"].append("무협 소설체 문체가 잘 살아있음")
        else:
            # 금지 표현 체크
            found_forbidden = []
            for category, words in self.forbidden.items():
                for word in words:
                    if word in script:
                        found_forbidden.append(word)

            if found_forbidden:
                feedback["critical_issues"].append(
                    f"금지 표현 발견: {', '.join(found_forbidden[:5])}"
                )

            # 의성어/의태어 부족
            onomatopoeia = ["쩌렁", "휘이잉", "우지직", "쾅", "파직"]
            found = [w for w in onomatopoeia if w in script]
            if len(found) < 3:
                feedback["improvements"].append(
                    "의성어/의태어 추가 권장 (무협 분위기 강화)"
                )

        # 4. 일관성 피드백
        if scores["consistency"] >= 18:
            feedback["strengths"].append("Series Bible 설정을 잘 준수함")
        else:
            # 캐릭터 등장 타이밍
            episode_num = context.episode_number
            for char_name, first_episode in CHARACTER_TIMELINE.items():
                if char_name in script and episode_num < first_episode:
                    feedback["critical_issues"].append(
                        f"⚠️ {char_name}은 {first_episode}화부터 등장 가능 (현재 {episode_num}화)"
                    )

        # 5. 몰입도 피드백
        if scores["immersion"] >= 8:
            feedback["strengths"].append("훅과 클리프행어가 효과적임")
        else:
            intro = script[:500]
            outro = script[-500:]

            if "?" not in intro:
                feedback["improvements"].append(
                    "오프닝에 질문이나 미스터리 요소 추가 권장"
                )
            if "..." not in outro and "?" not in outro:
                feedback["improvements"].append(
                    "엔딩에 클리프행어 강화 필요"
                )

        # 요약 생성
        total = sum(scores.values())
        grade = self._calculate_grade(total)

        grade_messages = {
            "S": "훌륭한 대본입니다! 바로 제작을 진행하세요.",
            "A": "좋은 대본입니다. 사소한 부분만 다듬으면 됩니다.",
            "B": "괜찮은 대본이지만 개선 사항을 반영해주세요.",
            "C": "수정이 필요합니다. 피드백을 참고하여 다시 작성해주세요.",
            "D": "대폭 수정이 필요합니다. 구조부터 다시 검토해주세요.",
        }
        feedback["summary"] = grade_messages.get(grade, "검토가 필요합니다.")

        # 점수 상세
        feedback["details"] = {
            "length": {"score": scores["length"], "max": 30},
            "structure": {"score": scores["structure"], "max": 20},
            "style": {"score": scores["style"], "max": 20},
            "consistency": {"score": scores["consistency"], "max": 20},
            "immersion": {"score": scores["immersion"], "max": 10},
        }

        return feedback


# =============================================================================
# 동기 실행 래퍼
# =============================================================================
def review_script(
    context: EpisodeContext,
    strict: bool = False
) -> Dict[str, Any]:
    """
    대본 검수 (동기 버전)

    Args:
        context: 에피소드 컨텍스트 (script 필수)
        strict: 엄격 모드

    Returns:
        검수 결과
    """
    import asyncio

    agent = ReviewAgent()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        agent.execute(context, strict=strict)
    )

    if result.success:
        return result.data
    else:
        raise Exception(result.error)


def quick_review(script: str, episode_number: int = 1) -> Tuple[str, int, List[str]]:
    """
    간단 검수 (컨텍스트 없이)

    Args:
        script: 대본 텍스트
        episode_number: 에피소드 번호

    Returns:
        (등급, 점수, 이슈 목록)
    """
    # 임시 컨텍스트 생성
    context = EpisodeContext.from_episode(episode_number)
    context.script = script

    agent = ReviewAgent()

    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(agent.execute(context))

    if result.success:
        data = result.data
        issues = data["feedback"].get("critical_issues", [])
        issues.extend(data["feedback"].get("improvements", []))
        return data["grade"], data["total_score"], issues
    else:
        return "F", 0, [result.error]


def review_script_strict(
    script: str,
    episode_number: int = 1,
    min_length: int = 12000
) -> Dict[str, Any]:
    """
    대본 엄격 검수 (블로킹)

    C/D 등급 또는 글자수 미달 시 ValueError 발생

    Args:
        script: 대본 텍스트
        episode_number: 에피소드 번호
        min_length: 최소 글자수

    Returns:
        검수 결과 (통과 시)

    Raises:
        ValueError: C/D 등급 또는 필수 기준 미충족 시
    """
    length = len(script)

    # 1. 글자수 필수 검증
    if length < min_length:
        raise ValueError(
            f"대본 검수 실패 - 글자수 미달 (진행 불가)\n"
            f"  현재: {length:,}자\n"
            f"  최소: {min_length:,}자\n"
            f"  부족: {min_length - length:,}자"
        )

    # 2. 상세 검수
    grade, score, issues = quick_review(script, episode_number)

    # 3. C/D 등급 차단
    if grade in ["C", "D"]:
        issues_str = "\n".join(f"  - {issue}" for issue in issues if issue)
        raise ValueError(
            f"대본 검수 실패 - {grade}등급 (진행 불가)\n"
            f"  점수: {score}/100\n"
            f"  등급: {grade} (최소 B등급 필요)\n"
            f"  문제점:\n{issues_str if issues_str else '  - 전체적인 품질 미달'}"
        )

    # 4. B등급 경고
    if grade == "B":
        warnings_str = "\n".join(f"  ⚠️ {issue}" for issue in issues if issue)
        if warnings_str:
            print(f"[ReviewAgent] 경고 - B등급 (통과하지만 개선 권장):\n{warnings_str}")

    # 5. 통과
    print(f"[ReviewAgent] ✓ 대본 검수 통과: {length:,}자, {grade}등급 ({score}/100점)")

    return {
        "passed": True,
        "grade": grade,
        "score": score,
        "length": length,
        "issues": issues,
    }


def get_power_scale(episode_number: int) -> Dict[str, str]:
    """에피소드별 파워 스케일 조회"""
    for (start, end), power_info in POWER_SCALE.items():
        if start <= episode_number <= end:
            return power_info
    return POWER_SCALE[(1, 5)]


def get_character_timeline() -> Dict[str, int]:
    """캐릭터 등장 타임라인 조회"""
    return CHARACTER_TIMELINE.copy()


def check_character_availability(
    character_name: str,
    episode_number: int
) -> bool:
    """캐릭터 등장 가능 여부 확인"""
    first_episode = CHARACTER_TIMELINE.get(character_name)
    if first_episode is None:
        return True  # 알 수 없는 캐릭터는 허용
    return episode_number >= first_episode

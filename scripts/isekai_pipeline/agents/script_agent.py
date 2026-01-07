"""
혈영 이세계편 - Script Agent (대본 에이전트)

## 성격 및 역할
40년간 무협/판타지 소설을 집필해온 베테랑 작가.
"문장 하나에 영혼을 담는다"는 철학의 장인 작가.

## 전문 분야
- 무협 소설 특유의 문체와 리듬
- 오감을 활용한 몰입형 묘사
- 전투 씬의 긴박감 있는 전개
- 캐릭터 내면 심리 묘사
- TTS 최적화 문장 구성

## 철학
- "독자는 눈으로 읽지만, 귀로 듣는다" - 리듬감 있는 문장
- "보여주지 말고 느끼게 하라" - Show, don't tell의 한계를 넘어
- "한 문장이 천 문장을 이긴다" - 압축과 함축의 미학
- "전투는 체스다" - 논리적인 액션 시퀀스

## 책임
- 12,000~15,000자 분량의 무협+판타지 융합 대본 작성
- 5막 구조 준수 (오프닝/전개/클라이맥스/해결/엔딩)
- TTS 음성 합성에 최적화된 문장
- 검수 피드백 반영 및 개선

## 타겟 독자
- 웹소설/웹툰에 익숙한 10-40대
- 무협+판타지 장르 선호층
- 유튜브 오디오 드라마 청취자

## 문체 특징
1. 의성어/의태어 적극 활용 (쩌렁, 우지직, 휘이잉)
2. 오감 묘사 (시각/청각/촉각/후각/미각)
3. 한자어 허용, 외래어 금지 (검기 ○, 소드 ✕)
4. 짧은 문장과 긴 문장의 교차
5. 내면 독백과 대화의 균형
"""

import re
import time
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentResult, AgentStatus, EpisodeContext


# =============================================================================
# 문체 가이드 (무협+판타지 융합)
# =============================================================================
SCRIPT_STYLE_GUIDE = """
## 문체 가이드 (혈영 이세계편 - 무협+판타지 융합)

### 기본 톤
- 다크 판타지 분위기 (밝은 코미디 지양)
- 긴장감 있으면서도 희망이 있는 서사
- 주인공의 성장을 중심으로 한 서사시적 문체

### 장르 융합 원칙
1. **무협 요소**
   - 무공 묘사: 검기, 기공, 내공 등 전통 무협 용어
   - 무예 대결: 초식, 공방, 검세 등 전투 용어
   - 수련과 깨달음: 오의 체득, 경지 상승

2. **판타지 요소**
   - 마법 체계: 마나, 마력, 속성 마법
   - 이세계 세계관: 몬스터, 던전, 등급 시스템
   - 특수 능력: 혈기창, 혈영 스킬

3. **융합 시 주의점**
   - 무협 느낌 60%, 판타지 30%, 현대 감성 10%
   - 한자어 용어 우선 (검기 ○, 소드 오라 ✕)
   - 외래어는 고유명사일 때만 허용 (이그니스 왕국)

### 문장 구성 원칙

#### 1. 리듬감 (음절 흐름)
나쁜 예:
"무영은 검을 들고 적에게 달려가서 공격을 했습니다."

좋은 예:
"무영이 검을 쥐었다. 대지를 박차고, 뛰었다. 검이 허공을 갈랐다."

#### 2. 의성어/의태어 활용
- 전투: 쩌렁, 쾅, 우지직, 치직, 파직
- 움직임: 휘이잉, 스르륵, 펄럭, 휙
- 감정: 두근, 쿵쾅, 찌릿, 뜨끔

#### 3. 오감 묘사
- 시각: "붉은 검기가 밤하늘을 수놓았다"
- 청각: "검과 검이 부딪히는 쩌렁한 금속음"
- 촉각: "손끝으로 전해오는 검의 떨림"
- 후각: "피비린내가 코끝을 스쳤다"
- 미각: "입안에 감도는 피의 쓴맛"

#### 4. 문장 길이 패턴
- **긴장 상승**: 문장 점점 짧게
  "적이 다가왔다. 거리 10보. 5보. 3보. 눈앞이다."

- **여운**: 문장 길게
  "전투가 끝나고, 무영은 검을 거두며 깊은 한숨을 내쉬었다."

- **반전**: 짧은 문장으로 끊기
  "다 끝났다고 생각했다. 하지만."

### TTS 최적화

#### 1. 문장 길이
- 권장: 15-50자
- 최대: 70자 (그 이상은 분할)

#### 2. 호흡 표시
- 쉼표로 자연스러운 끊어읽기
- "하지만, 그것은, 시작에 불과했다."

#### 3. 강조 표현
- 중요 단어 앞뒤 쉼표
- "그것이 바로, 혈기창이었다."

#### 4. 숫자/한자어 처리
- 연도: 그대로 사용 (TTS가 자연스럽게 읽음)
- 큰 숫자: "약 5만 명" → "약 오만 명"으로 변환
- 한자 병기 금지 (TTS 오류 유발)

### 금지 표현

1. **외래어**
   - ✕: 어택, 디펜스, 스킬, 버프
   - ○: 공격, 방어, 기술, 강화

2. **현대 인터넷 용어**
   - ✕: 미쳤다, 대박, 존잼, 갓
   - ○: 경악, 놀라움, 흥미, 최고

3. **학술적 유보**
   - ✕: "단정하기 어렵다", "해석이 갈린다"
   - ○: 확신 있는 서술

4. **과도한 설명**
   - ✕: "무영은 화가 났다. 왜냐하면..."
   - ○: "무영의 눈에 살기가 어렸다."

### 대화문 작성

1. **캐릭터별 말투**
   - 무영: 간결, 낮은 톤, 냉정
   - 에이라: 활발, 밝은 톤
   - 카이든: 오만, 도발적
   - 혈마: 위압적, 고어체

2. **대화 비중**
   - 전체의 30-40%
   - 씬당 최소 1회 이상

3. **대화 형식**
   "대사." 화자의 행동.
   예: "물러서라." 무영이 검을 들었다.

### 씬(Scene) 구조

| 씬 | 이름 | 글자수 | 목적 |
|---|------|-------|-----|
| 1 | 오프닝 | 2,100자 | 훅 + 상황 설정 |
| 2 | 전개 | 3,100자 | 갈등 심화 |
| 3 | 클라이맥스 | 3,900자 | 절정 + 대결 |
| 4 | 해결 | 2,800자 | 결과 + 의미 |
| 5 | 엔딩 | 2,100자 | 마무리 + 클리프행어 |
| 합계 | | 14,000자 | |

### 씬 전환 표현

- "그때였다."
- "얼마나 지났을까."
- "어둠이 걷히고,"
- "시간이 흘렀다."
- "다음 순간,"
"""


# =============================================================================
# 전투 씬 작성 가이드
# =============================================================================
BATTLE_SCENE_GUIDE = """
## 전투 씬 작성 가이드 (40년 경력 무협 작가의 노하우)

### 전투의 3단계 구조

1. **대치 (Standoff)**
   - 긴장감 고조
   - 상대방 분석 묘사
   - "무영의 눈이 좁아졌다. 상대의 기세가 예사롭지 않다."

2. **격돌 (Clash)**
   - 짧은 문장의 연속
   - 의성어/의태어 활용
   - "검이 부딪혔다. 쩌렁. 불꽃이 튀었다. 다시, 세 번."

3. **결착 (Resolution)**
   - 결정적 일격
   - 여운과 결과
   - "피가 튀었다. 승부는 갈렸다."

### 전투 묘사 공식

```
[상황] + [동작] + [결과] + [반응]

예시:
적의 검이 쏟아졌다. (상황)
무영이 검을 휘둘러 막아냈다. (동작)
금속음과 함께 불꽃이 튀었다. (결과)
팔이 저렸다. 만만찮다. (반응)
```

### 1:1 대결 vs 다수 전투

**1:1 대결**
- 심리전 강조
- 초식과 검법 상세 묘사
- 상대의 약점 분석 과정

**다수 전투**
- 빠른 템포
- 전체 전황 조망
- 핵심 순간만 상세히

### 파워 스케일링 주의점

무영의 현재 등급에 맞는 전투력 표현:
- F~D급: 일반 검술, 기초 혈기
- C~B급: 검기 발현, 혈기창 기본기
- A급: 오의급 기술, 광역 공격
- S급 이상: 초월적 전투, 세계관 영향

### 전투 중 감정선

전투만 하면 지루해진다. 감정을 끼워넣어라.
- 분노: "피가 끓었다. 용서할 수 없다."
- 공포: "등골이 서늘해졌다."
- 결의: "이를 악물었다. 여기서 물러설 순 없다."
- 희열: "입꼬리가 올라갔다. 재미있군."
"""


# =============================================================================
# 내면 묘사 가이드
# =============================================================================
INNER_VOICE_GUIDE = """
## 내면 묘사 가이드

### 내면 독백 형식

1. **직접 독백** (따옴표 없이)
   이상하다. 뭔가 놓치고 있다.
   무영은 생각에 잠겼다.

2. **간접 독백** (서술형)
   무영은 이상하다고 느꼈다. 무언가 놓치고 있다는 감각.

3. **생각 표시**
   '이건... 덫이다.'
   무영의 눈이 날카로워졌다.

### 내면 묘사 비율
- 전투 씬: 20% (행동 위주)
- 일반 씬: 40%
- 감정 씬: 60%

### 피해야 할 패턴
✕ 지나친 자기 설명: "나는 화가 났다. 왜냐하면..."
○ 행동으로 보여주기: "주먹을 꽉 쥐었다."
"""


# =============================================================================
# 씬 구조 정의
# =============================================================================
SCENE_STRUCTURE = [
    {
        "scene": 1,
        "name": "오프닝",
        "target_length": 2100,
        "purpose": "훅으로 독자 사로잡기, 상황 설정",
        "tone": "긴장감 또는 미스터리",
        "requirements": [
            "첫 문장에서 즉시 몰입 유도",
            "이전화 연결 (있다면)",
            "핵심 갈등 암시",
        ],
        "avoid": [
            "지루한 상황 설명으로 시작",
            "너무 많은 배경 정보",
        ],
    },
    {
        "scene": 2,
        "name": "전개",
        "target_length": 3100,
        "purpose": "갈등 심화, 장애물 제시",
        "tone": "기대감, 긴장 고조",
        "requirements": [
            "주인공의 목표 명확화",
            "장애물/적대자 등장",
            "첫 번째 전환점",
        ],
        "avoid": [
            "무의미한 대화",
            "갈등 없는 일상 묘사",
        ],
    },
    {
        "scene": 3,
        "name": "클라이맥스",
        "target_length": 3900,
        "purpose": "절정, 핵심 대결",
        "tone": "극도의 긴장, 카타르시스",
        "requirements": [
            "에피소드의 핵심 순간",
            "주인공의 선택/결단",
            "가장 강렬한 액션 또는 감정",
        ],
        "avoid": [
            "긴장감 해소 없는 지루한 전개",
            "논리적 비약",
        ],
    },
    {
        "scene": 4,
        "name": "해결",
        "target_length": 2800,
        "purpose": "결과 정리, 의미 부여",
        "tone": "안도감, 여운",
        "requirements": [
            "클라이맥스의 결과 처리",
            "캐릭터의 성장/변화 확인",
            "주변 인물 반응",
        ],
        "avoid": [
            "급하게 마무리",
            "새로운 갈등 추가",
        ],
    },
    {
        "scene": 5,
        "name": "엔딩",
        "target_length": 2100,
        "purpose": "마무리 + 클리프행어",
        "tone": "여운 + 기대감",
        "requirements": [
            "핵심 메시지 정리",
            "다음화 복선/암시",
            "강력한 클리프행어",
        ],
        "avoid": [
            "완결된 느낌 (시리즈물)",
            "약한 엔딩",
        ],
    },
]


# =============================================================================
# 캐릭터 말투 사전
# =============================================================================
CHARACTER_SPEECH_PATTERNS = {
    "무영": {
        "tone": "간결하고 낮은 톤, 냉정",
        "endings": ["~다.", "~군.", "~지."],
        "traits": ["과묵", "필요한 말만", "가끔 자조적"],
        "example": "알았다. 가자.",
    },
    "라이트닝": {
        "tone": "(늑대) 울음, 행동으로 표현",
        "note": "텔레파시 또는 행동 묘사",
        "example": "라이트닝이 낮게 으르렁거렸다.",
    },
    "카이든": {
        "tone": "오만하고 도발적, 자신만만",
        "endings": ["~하군.", "~인가?", "~이라도?"],
        "traits": ["자존심 강함", "인정하지 않음", "나중에 변화"],
        "example": "고작 그 정도인가? 실망이군.",
    },
    "에이라": {
        "tone": "활발하고 밝음, 때론 진지",
        "endings": ["~요!", "~네요.", "~인 거예요?"],
        "traits": ["낙천적", "따뜻함", "숨겨진 강함"],
        "example": "무영 씨, 괜찮아요? 다치신 거 아니에요?",
    },
    "이그니스 공주": {
        "tone": "품위 있고 단호함, 왕족의 위엄",
        "endings": ["~하오.", "~이니라.", "~하도록."],
        "traits": ["책임감", "백성 사랑", "고독함"],
        "example": "경의 충성, 잊지 않겠소.",
    },
    "혈마": {
        "tone": "위압적, 고어체, 초월적 존재감",
        "endings": ["~로다.", "~하느냐.", "~이리라."],
        "traits": ["절대 악", "오만", "인간 경시"],
        "example": "보잘것없는 인간이 감히... 재미있구나.",
    },
}


class ScriptAgent(BaseAgent):
    """
    대본 에이전트 - 40년 경력의 무협/판타지 작가

    핵심 역량:
    - 무협 소설체 문장
    - 오감 묘사 몰입감
    - 전투 씬 전문
    - TTS 최적화
    """

    def __init__(self):
        super().__init__("ScriptAgent")

        # 대본 설정
        self.target_length = 14000  # 목표 글자수
        self.min_length = 12000  # 최소
        self.max_length = 15000  # 최대
        self.tolerance = 0.1  # ±10%

        # 씬 구조
        self.scene_structure = SCENE_STRUCTURE

        # TTS 최적화 설정
        self.tts_config = {
            "sentence_length_min": 10,
            "sentence_length_max": 60,
            "optimal_sentence_length": 30,
            "max_paragraph_length": 300,
        }

    async def execute(self, context: EpisodeContext, **kwargs) -> AgentResult:
        """
        대본 작성 가이드 생성

        Args:
            context: 에피소드 컨텍스트 (brief 필수)
            **kwargs:
                feedback: 검수 피드백 (개선 시)

        Returns:
            AgentResult with script guide data
        """
        self.set_status(AgentStatus.RUNNING)
        start_time = time.time()

        feedback = kwargs.get("feedback")
        is_improvement = feedback is not None

        context.script_attempts += 1
        context.add_log(
            self.name,
            "대본 가이드 생성 시작" if not is_improvement else "대본 개선 가이드",
            "running",
            f"시도 {context.script_attempts}/{context.max_attempts}"
        )

        try:
            # 기획서 확인
            if not context.brief:
                raise ValueError("기획서(brief)가 없습니다. PlannerAgent를 먼저 실행하세요.")

            # 대본 작성 가이드 생성
            guide = self._generate_script_guide(context, feedback)

            # 메타데이터 템플릿 생성
            metadata = self._generate_metadata_template(context)

            duration = time.time() - start_time

            context.add_log(
                self.name,
                "대본 가이드 생성 완료",
                "success",
                f"{duration:.1f}초"
            )
            self.set_status(AgentStatus.WAITING_REVIEW)

            return AgentResult(
                success=True,
                data={
                    "guide": guide,
                    "metadata_template": metadata,
                    "style_guide": SCRIPT_STYLE_GUIDE,
                    "battle_guide": BATTLE_SCENE_GUIDE,
                    "inner_voice_guide": INNER_VOICE_GUIDE,
                    "scene_structure": self.scene_structure,
                    "character_speech": CHARACTER_SPEECH_PATTERNS,
                    "tts_config": self.tts_config,
                },
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            context.add_log(self.name, "대본 가이드 생성 실패", "error", error_msg)
            self.set_status(AgentStatus.FAILED)

            return AgentResult(
                success=False,
                error=error_msg,
                duration=duration,
            )

    def _generate_script_guide(
        self,
        context: EpisodeContext,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """대본 작성 가이드 생성"""
        brief = context.brief
        episode_num = context.episode_number

        # 씬별 상세 가이드 생성
        scene_guides = []
        for scene_template in self.scene_structure:
            scene_info = self._build_scene_info(scene_template, context)
            scene_guides.append(scene_info)

        # 등장 캐릭터별 말투 가이드
        character_guides = self._get_character_guides(context.characters)

        guide = {
            "episode_info": {
                "episode_id": context.episode_id,
                "episode_number": episode_num,
                "part": context.part,
                "part_name": context.part_name,
                "title": context.title,
            },

            "brief_summary": {
                "hook": brief.get("hook", ""),
                "ending_hook": brief.get("ending_hook", ""),
                "emotional_arc": brief.get("emotional_arc", {}),
                "tone": brief.get("tone", {}),
            },

            "length_requirements": {
                "target": self.target_length,
                "min": self.min_length,
                "max": self.max_length,
                "estimated_duration": f"{self.target_length / 910:.0f}분",
                "scenes_breakdown": {
                    scene["name"]: scene["target_length"]
                    for scene in self.scene_structure
                },
            },

            "scene_guides": scene_guides,
            "character_speech": character_guides,

            "style_requirements": {
                "genre": "무협 + 판타지 융합",
                "tone": "다크 판타지",
                "vocabulary": "한자어 우선, 외래어 금지",
                "dialogue_ratio": "30-40%",
                "inner_voice_ratio": "20-40%",
            },

            "tts_optimization": {
                "sentence_length": f"{self.tts_config['sentence_length_min']}-{self.tts_config['sentence_length_max']}자",
                "paragraph_length": f"최대 {self.tts_config['max_paragraph_length']}자",
                "breathing": "쉼표로 자연스러운 호흡",
                "emphasis": "중요 단어 앞뒤 쉼표",
            },

            "connections": {
                "prev_episode": context.prev_episode,
                "next_episode": context.next_episode,
            },

            "feedback_to_apply": feedback,
        }

        return guide

    def _build_scene_info(
        self,
        scene_template: Dict[str, Any],
        context: EpisodeContext
    ) -> Dict[str, Any]:
        """씬별 상세 정보 구성"""
        brief = context.brief or {}
        scenes_in_brief = brief.get("scenes", [])

        # brief에서 해당 씬 정보 찾기
        brief_scene = None
        for s in scenes_in_brief:
            if s.get("name") == scene_template["name"]:
                brief_scene = s
                break

        scene_info = {
            "scene": scene_template["scene"],
            "name": scene_template["name"],
            "target_length": scene_template["target_length"],
            "purpose": scene_template["purpose"],
            "tone": scene_template["tone"],
            "requirements": scene_template["requirements"],
            "avoid": scene_template["avoid"],
        }

        # brief에서 추가 정보 병합
        if brief_scene:
            scene_info["tips"] = brief_scene.get("tips", [])
            scene_info["emotional_beat"] = brief_scene.get("emotional_beat", "")

        return scene_info

    def _get_character_guides(
        self,
        characters: List[str]
    ) -> List[Dict[str, Any]]:
        """등장 캐릭터별 말투 가이드"""
        guides = []

        for char_name in characters:
            # 캐릭터명에서 키 추출 (괄호 앞 부분)
            char_key = char_name.split(" (")[0] if " (" in char_name else char_name

            if char_key in CHARACTER_SPEECH_PATTERNS:
                pattern = CHARACTER_SPEECH_PATTERNS[char_key]
                guides.append({
                    "name": char_name,
                    "key": char_key,
                    **pattern,
                })

        # 무영은 항상 포함
        if not any(g["key"] == "무영" for g in guides):
            guides.insert(0, {
                "name": "무영",
                "key": "무영",
                **CHARACTER_SPEECH_PATTERNS["무영"],
            })

        return guides

    def _generate_metadata_template(
        self,
        context: EpisodeContext
    ) -> Dict[str, Any]:
        """YouTube 메타데이터 템플릿 생성"""
        episode_num = context.episode_number
        title = context.title or f"EP{episode_num:03d}"

        # 제목 옵션
        title_options = [
            f"[혈영 이세계편] {episode_num}화: {title}",
            f"혈영 이세계편 EP{episode_num:03d} | {title}",
            f"무협 이세계물 | {title} [{episode_num}화]",
        ]

        # 설명 템플릿
        description_template = f"""
혈영 이세계편 {episode_num}화: {title}

{context.part_name} 파트의 이야기입니다.

#무협 #이세계 #판타지 #웹소설 #오디오드라마

📚 시리즈 정보
- 총 60화 시리즈
- 매주 업로드

⏰ 타임스탬프
00:00 오프닝
(씬별 타임스탬프 추가)

🔔 구독과 좋아요 부탁드립니다!
"""

        # 태그
        tags = [
            "무협", "이세계", "판타지", "웹소설", "오디오드라마",
            "혈영", "전생", "회귀", "성장물", "먼치킨",
            f"혈영이세계편{episode_num}화",
        ]

        # 썸네일 문구 제안
        thumbnail_suggestions = [
            title[:15] if len(title) > 15 else title,
            f"EP{episode_num:03d}",
            context.part_name,
        ]

        return {
            "title_options": title_options,
            "description_template": description_template.strip(),
            "tags": tags,
            "thumbnail_suggestions": thumbnail_suggestions,
            "category": "Entertainment",
            "language": "ko",
        }

    def validate_script(self, script: str) -> Dict[str, Any]:
        """대본 유효성 검사"""
        length = len(script)
        issues = []
        warnings = []

        # 1. 길이 검사
        if length < self.min_length:
            issues.append(f"대본이 너무 짧습니다 ({length:,}자 < {self.min_length:,}자)")
        elif length > self.max_length:
            warnings.append(f"대본이 깁니다 ({length:,}자 > {self.max_length:,}자)")

        # 2. 외래어 검사
        foreign_words = ["어택", "디펜스", "스킬", "버프", "너프", "대미지", "HP", "MP"]
        found_foreign = [w for w in foreign_words if w in script]
        if found_foreign:
            issues.append(f"외래어 발견: {', '.join(found_foreign)}")

        # 3. 현대 용어 검사
        modern_words = ["미쳤다", "대박", "존잼", "갓", "레전드", "역대급"]
        found_modern = [w for w in modern_words if w in script]
        if found_modern:
            warnings.append(f"현대 인터넷 용어 발견: {', '.join(found_modern)}")

        # 4. 대화문 비율 검사
        dialogue_count = script.count('"')
        if dialogue_count < 10:
            warnings.append(f"대화문이 적습니다 (따옴표 {dialogue_count}개)")

        # 5. 의성어/의태어 검사
        onomatopoeia = ["쩌렁", "휘이잉", "우지직", "쾅", "파직", "스르륵"]
        found_onomatopoeia = [w for w in onomatopoeia if w in script]
        if len(found_onomatopoeia) < 3:
            warnings.append("의성어/의태어가 적습니다 (무협 느낌 부족)")

        # 6. TTS 최적화 - 긴 문장
        sentences = re.split(r'[.!?]', script)
        long_sentences = [s for s in sentences if len(s.strip()) > 80]
        if len(long_sentences) > 10:
            warnings.append(f"80자 초과 문장 {len(long_sentences)}개 (TTS 부적합)")

        # 점수 계산
        score = self._calculate_script_score(script, issues, warnings)

        return {
            "valid": len(issues) == 0,
            "length": length,
            "issues": issues,
            "warnings": warnings,
            "score": score,
            "dialogue_count": dialogue_count // 2,
            "onomatopoeia_found": found_onomatopoeia,
        }

    def _calculate_script_score(
        self,
        script: str,
        issues: List[str],
        warnings: List[str]
    ) -> int:
        """대본 점수 계산 (100점 만점)"""
        score = 100

        # 이슈당 -20점
        score -= len(issues) * 20

        # 경고당 -5점
        score -= len(warnings) * 5

        # 길이 보너스/감점
        length = len(script)
        if self.min_length <= length <= self.max_length:
            diff = abs(length - self.target_length)
            if diff < 500:
                score += 5  # 목표에 가까우면 보너스
        else:
            score -= 10

        return max(0, min(100, score))


# =============================================================================
# 동기 실행 래퍼
# =============================================================================
def generate_script_guide(
    context: EpisodeContext,
    feedback: str = None
) -> Dict[str, Any]:
    """
    대본 작성 가이드 생성 (동기 버전)

    Args:
        context: 에피소드 컨텍스트
        feedback: 검수 피드백

    Returns:
        대본 작성 가이드
    """
    import asyncio

    agent = ScriptAgent()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        agent.execute(context, feedback=feedback)
    )

    if result.success:
        return result.data
    else:
        raise Exception(result.error)


def validate_script(script: str) -> Dict[str, Any]:
    """대본 유효성 검사 (동기 버전)"""
    agent = ScriptAgent()
    return agent.validate_script(script)


def validate_script_strict(script: str) -> Dict[str, Any]:
    """
    대본 엄격 검증 (블로킹)

    기준 미달 시 ValueError 발생

    Raises:
        ValueError: 필수 기준 미충족 시
    """
    agent = ScriptAgent()
    result = agent.validate_script(script)

    if not result["valid"]:
        issues_str = "\n".join(f"  - {issue}" for issue in result["issues"])
        raise ValueError(
            f"대본 검증 실패 (진행 불가):\n{issues_str}\n"
            f"현재 길이: {result['length']:,}자\n"
            f"허용 범위: {agent.min_length:,}~{agent.max_length:,}자"
        )

    if result["warnings"]:
        warnings_str = "\n".join(f"  ⚠️ {w}" for w in result["warnings"])
        print(f"[ScriptAgent] 경고 (통과하지만 개선 권장):\n{warnings_str}")

    print(f"[ScriptAgent] ✓ 대본 검증 통과: {result['length']:,}자, 점수 {result['score']}/100")
    return result


def get_character_speech_pattern(character_name: str) -> Optional[Dict[str, Any]]:
    """캐릭터 말투 패턴 조회"""
    return CHARACTER_SPEECH_PATTERNS.get(character_name)


def get_scene_structure() -> List[Dict[str, Any]]:
    """씬 구조 조회"""
    return SCENE_STRUCTURE.copy()

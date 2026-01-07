"""
혈영 이세계편 - Image Agent (이미지 에이전트)

## 성격 및 역할
40년간 게임/애니메이션 컨셉 아트를 담당해온 시니어 아티스트.
AI 이미지 생성 프롬프트 엔지니어링의 대가.

## 전문 분야
- 무협+판타지 융합 비주얼 스타일
- 다크 판타지 색채와 분위기
- 전투 액션 구도와 역동성
- 캐릭터 디자인 일관성 유지
- AI 이미지 생성 프롬프트 최적화

## 철학
- "한 장의 이미지가 천 마디 대본을 대신한다"
- "색채는 감정이다" - 분위기를 색으로 표현
- "구도가 서사다" - 캐릭터 배치로 관계를 보여줌
- "일관성이 생명이다" - 시리즈 전체의 비주얼 통일

## 책임
- 대본 기반 이미지 프롬프트 생성 (5~12개)
- 무협+판타지 융합 스타일 가이드
- 씬별 구도와 분위기 설정
- 썸네일 문구 및 디자인 제안
- 캐릭터 외형 일관성 유지

## 이미지 유형
- establishing_shot: 세계관 전경
- action_scene: 전투/액션 장면
- character_portrait: 캐릭터 초상
- emotional_moment: 감정 클로즈업
- power_display: 능력/스킬 발현
- atmosphere: 분위기 샷

## 스타일 키워드
- 기본: korean martial arts fantasy, manhwa style
- 색감: dark fantasy, magical glow, dramatic lighting
- 질감: detailed, cinematic, epic composition
"""

import re
import time
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentResult, AgentStatus, EpisodeContext


# =============================================================================
# 이미지 스타일 가이드 (무협+판타지 융합)
# =============================================================================
IMAGE_STYLE_GUIDE = """
## 이미지 스타일 가이드 (혈영 이세계편)

### 기본 스타일
- **장르**: Korean martial arts fantasy (무협 판타지)
- **화풍**: Manhwa style with dark fantasy elements
- **품질**: Highly detailed, cinematic composition, 8K quality

### 색채 팔레트

1. **기본 색감**
   - 주조색: Deep crimson (혈영의 상징)
   - 보조색: Dark purple, midnight blue
   - 강조색: Golden glow (내공/검기 표현)
   - 배경: Dark forest, misty mountains

2. **감정별 색감**
   | 감정 | 주색 | 보조색 | 효과 |
   |------|-----|--------|------|
   | 긴장 | crimson | dark purple | rim lighting |
   | 평화 | soft blue | green | soft glow |
   | 분노 | blood red | black | harsh shadows |
   | 희망 | golden | white | lens flare |
   | 신비 | deep purple | silver | magical particles |

3. **시간대별 색감**
   - 낮: Warm but muted tones
   - 밤: Deep blue with moonlight
   - 새벽: Pink and orange gradient
   - 황혼: Golden hour lighting

### 구도 원칙

1. **전투 씬**
   - 다이나믹 앵글 (로우앵글 → 위압감)
   - 대각선 구도 (역동성)
   - 모션 블러 효과
   - 검기/마법 이펙트 강조

2. **캐릭터 샷**
   - 3/4 앵글 선호 (입체감)
   - 배경과 대비되는 조명
   - 의상 디테일 강조

3. **분위기 샷**
   - 광각 구도 (세계관 스케일)
   - 안개/연기 효과
   - 대비가 강한 조명

### 캐릭터 비주얼

**무영 (주인공)**
- 체형: 키 크고 날씬한 체형, 단련된 근육
- 머리: 검은 단발 (이마를 살짝 가림)
- 눈: 붉은색 (혈기창 발동 시 더 진해짐)
- 복장: 검은 무복, 붉은 포인트
- 무기: 검은 검 (혈영검)
- 특징: 차가운 눈빛, 무표정

**라이트닝 (늑대)**
- 거대한 검은 늑대
- 금빛 눈
- 번개 무늬 털

**카이든 (라이벌)**
- 금발, 푸른 눈
- 귀족적 외모, 자신만만한 표정
- 흰색 갑옷, 은검

**에이라 (히로인)**
- 은발, 녹색 눈
- 온화한 미소
- 치유사 복장 (흰색 + 녹색)

**혈마 (최종보스)**
- 전신 검은 갑옷
- 붉은 눈에서 마기 방출
- 거대한 체구, 위압적 존재감

### 금지 사항

1. **스타일 금지**
   - 밝은 파스텔 톤 (다크 판타지 유지)
   - 모에풍 과장된 눈
   - 현대적 배경/소품
   - 노출이 심한 의상

2. **기술적 금지**
   - 이미지 내 텍스트 (AI가 정확히 생성 못함)
   - 손가락 상세 묘사 주의
   - 복잡한 무기 패턴

3. **세계관 금지**
   - 총기, 자동차 등 현대 소품
   - 일본 사무라이 갑옷 (한국 무협 분위기)
   - 서양 판타지 과도한 요소

### 프롬프트 구조

```
[Quality] + [Style] + [Subject] + [Action] + [Environment] + [Lighting] + [Color] + [Mood]

예시:
"masterpiece, best quality, korean martial arts fantasy manhwa style,
a young warrior with black hair and red eyes wielding a dark sword,
dynamic fighting pose with crimson sword energy,
dark forest background with moonlight,
dramatic rim lighting, deep shadows,
crimson and purple color palette,
epic and intense atmosphere"
```

### 네거티브 프롬프트 (필수)

```
"text, watermark, signature, logo, modern elements, gun, car,
bright colors, cute style, chibi, deformed hands, extra fingers,
blurry, low quality, amateur, ugly"
```
"""


# =============================================================================
# 씬별 이미지 타입 매핑
# =============================================================================
SCENE_IMAGE_TYPES = {
    "오프닝": {
        "primary_type": "atmosphere",
        "secondary_types": ["establishing_shot", "character_portrait"],
        "mood": "mysterious, anticipating",
        "composition": "wide shot or medium shot",
    },
    "전개": {
        "primary_type": "character_portrait",
        "secondary_types": ["atmosphere", "emotional_moment"],
        "mood": "tense, building up",
        "composition": "medium shot with environment",
    },
    "클라이맥스": {
        "primary_type": "action_scene",
        "secondary_types": ["power_display", "emotional_moment"],
        "mood": "intense, epic, dramatic",
        "composition": "dynamic angle, motion blur",
    },
    "해결": {
        "primary_type": "emotional_moment",
        "secondary_types": ["character_portrait", "atmosphere"],
        "mood": "relief, contemplative",
        "composition": "close-up or medium shot",
    },
    "엔딩": {
        "primary_type": "atmosphere",
        "secondary_types": ["establishing_shot", "character_portrait"],
        "mood": "mysterious, cliffhanger",
        "composition": "wide shot or silhouette",
    },
}


# =============================================================================
# 이미지 타입별 프롬프트 템플릿
# =============================================================================
IMAGE_TYPE_TEMPLATES = {
    "establishing_shot": {
        "composition": "epic wide shot, panoramic view",
        "focus": "landscape and environment",
        "example_prompt": "vast dark fantasy landscape, ancient martial arts world",
    },
    "action_scene": {
        "composition": "dynamic angle, motion blur, action lines",
        "focus": "movement and impact",
        "example_prompt": "intense sword fight, crimson sword energy slashing through air",
    },
    "character_portrait": {
        "composition": "3/4 view or front view, upper body focus",
        "focus": "character expression and costume details",
        "example_prompt": "detailed character portrait, korean fantasy warrior",
    },
    "emotional_moment": {
        "composition": "close-up or medium shot, soft focus background",
        "focus": "facial expression and emotion",
        "example_prompt": "emotional close-up, dramatic lighting on face",
    },
    "power_display": {
        "composition": "hero shot, low angle, energy effects",
        "focus": "ability manifestation",
        "example_prompt": "powerful warrior unleashing crimson energy, magical aura",
    },
    "atmosphere": {
        "composition": "establishing shot with mood emphasis",
        "focus": "environment and lighting",
        "example_prompt": "moody dark forest, moonlight piercing through mist",
    },
}


# =============================================================================
# 캐릭터 비주얼 설정
# =============================================================================
CHARACTER_VISUALS = {
    "무영": {
        "appearance": "young korean man, black short hair, red eyes, tall and lean muscular build",
        "costume": "black martial arts robes with crimson accents, dark sword on back",
        "expression_range": ["cold", "determined", "angry", "contemplative"],
        "signature_elements": ["crimson sword energy", "red eye glow"],
        "note": "Always maintain cold/serious expression unless specified",
    },
    "라이트닝": {
        "appearance": "massive black wolf, golden eyes, lightning-pattern fur markings",
        "size": "larger than normal horse",
        "expression_range": ["fierce", "loyal", "alert"],
        "signature_elements": ["golden eyes glowing", "electric sparks"],
    },
    "카이든": {
        "appearance": "handsome young man, blonde hair, blue eyes, aristocratic features",
        "costume": "white knight armor with silver accents, silver longsword",
        "expression_range": ["arrogant", "surprised", "respectful"],
        "signature_elements": ["white/silver color scheme", "noble bearing"],
    },
    "에이라": {
        "appearance": "young woman, silver hair, green eyes, gentle features",
        "costume": "white and green healer robes, nature motifs",
        "expression_range": ["warm smile", "worried", "determined"],
        "signature_elements": ["green healing magic", "gentle aura"],
    },
    "이그니스 공주": {
        "appearance": "regal young woman, black hair, golden eyes, elegant features",
        "costume": "royal dress with flame motifs, golden crown",
        "expression_range": ["dignified", "kind", "commanding"],
        "signature_elements": ["golden flame accents", "royal presence"],
    },
    "혈마": {
        "appearance": "massive armored figure, glowing red eyes visible through helm",
        "costume": "full black demonic armor, corrupted red energy",
        "expression_range": ["menacing", "amused", "enraged"],
        "signature_elements": ["dark crimson miasma", "overwhelming presence"],
    },
}


# =============================================================================
# 파트별 분위기 설정
# =============================================================================
PART_VISUAL_THEMES = {
    1: {
        "name": "적응, 각성",
        "palette": "dark blue, silver, emerging crimson",
        "mood": "mysterious, discovering, awakening",
        "environment": "dark forests, abandoned ruins, moonlit landscapes",
        "lighting": "moonlight, soft glow, mysterious shadows",
    },
    2: {
        "name": "성장, 소드마스터",
        "palette": "crimson, gold, dark purple",
        "mood": "intense, competitive, growth",
        "environment": "training grounds, dueling arenas, mountain peaks",
        "lighting": "dramatic sunlight, combat lighting",
    },
    3: {
        "name": "이그니스, 명성",
        "palette": "gold, crimson, royal blue",
        "mood": "glory, responsibility, political",
        "environment": "kingdom castle, grand halls, battlefield",
        "lighting": "golden hour, torch light, grand scale",
    },
    4: {
        "name": "혈마 발견, 정치",
        "palette": "dark red, black, sickly green",
        "mood": "suspense, conspiracy, darkness",
        "environment": "hidden chambers, corrupt lands, dark forests",
        "lighting": "low key, ominous shadows, unnatural glow",
    },
    5: {
        "name": "전쟁",
        "palette": "blood red, black, fire orange",
        "mood": "desperate, epic, sacrifice",
        "environment": "battlefields, burning cities, demon realm",
        "lighting": "fire light, apocalyptic sky, dramatic contrast",
    },
    6: {
        "name": "최종전, 귀환",
        "palette": "crimson, pure white, golden",
        "mood": "final battle, hope, resolution",
        "environment": "demon king's throne, portal between worlds",
        "lighting": "divine light vs. darkness, ultimate contrast",
    },
}


class ImageAgent(BaseAgent):
    """
    이미지 에이전트 - 40년 경력의 컨셉 아티스트

    핵심 역량:
    - 무협+판타지 비주얼 스타일
    - AI 이미지 프롬프트 엔지니어링
    - 캐릭터 일관성 유지
    - 구도와 분위기 설계
    """

    def __init__(self):
        super().__init__("ImageAgent")

        # 이미지 설정
        self.min_images = 5
        self.max_images = 12
        self.chars_per_minute = 910  # 한국어 TTS 기준

        # 스타일 설정
        self.base_style = "korean martial arts fantasy, manhwa style, dark fantasy"
        self.quality_tags = "masterpiece, best quality, highly detailed, 8k"
        self.negative_prompt = (
            "text, watermark, signature, logo, modern elements, gun, car, "
            "bright colors, cute style, chibi, deformed hands, extra fingers, "
            "blurry, low quality, amateur, ugly, nsfw"
        )

    async def execute(self, context: EpisodeContext, **kwargs) -> AgentResult:
        """
        이미지 프롬프트 생성

        Args:
            context: 에피소드 컨텍스트 (script 필수)
            **kwargs:
                image_count: 생성할 이미지 수 (자동 계산됨)

        Returns:
            AgentResult with image prompts
        """
        self.set_status(AgentStatus.RUNNING)
        start_time = time.time()

        context.add_log(
            self.name,
            "이미지 프롬프트 생성 시작",
            "running",
            f"파트 {context.part}: {context.part_name}"
        )

        try:
            # 대본 확인
            if not context.script:
                raise ValueError("대본(script)이 없습니다. ScriptAgent를 먼저 실행하세요.")

            script = context.script
            part = context.part

            # 이미지 개수 계산
            image_count = kwargs.get("image_count")
            if not image_count:
                image_count = self._calculate_image_count(script)

            # 파트별 테마 가져오기
            visual_theme = PART_VISUAL_THEMES.get(part, PART_VISUAL_THEMES[1])

            # 씬별 이미지 프롬프트 생성
            image_prompts = self._generate_image_prompts(
                script, image_count, context, visual_theme
            )

            # 썸네일 가이드 생성
            thumbnail_guide = self._generate_thumbnail_guide(context, visual_theme)

            duration = time.time() - start_time

            context.add_log(
                self.name,
                f"이미지 가이드 생성 완료 ({len(image_prompts)}개)",
                "success",
                f"{duration:.1f}초"
            )
            self.set_status(AgentStatus.WAITING_REVIEW)

            return AgentResult(
                success=True,
                data={
                    "image_count": len(image_prompts),
                    "image_prompts": image_prompts,
                    "visual_theme": visual_theme,
                    "thumbnail_guide": thumbnail_guide,
                    "style_guide": IMAGE_STYLE_GUIDE,
                    "character_visuals": CHARACTER_VISUALS,
                    "negative_prompt": self.negative_prompt,
                },
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            context.add_log(self.name, "이미지 가이드 생성 실패", "error", error_msg)
            self.set_status(AgentStatus.FAILED)

            return AgentResult(
                success=False,
                error=error_msg,
                duration=duration,
            )

    def _calculate_image_count(self, script: str) -> int:
        """대본 길이 기반 이미지 개수 계산"""
        length = len(script)
        estimated_minutes = length / self.chars_per_minute

        # 영상 길이에 따른 이미지 수
        if estimated_minutes < 8:
            return 5
        elif estimated_minutes < 10:
            return 8
        elif estimated_minutes < 15:
            return 11
        else:
            return 12

    def _generate_image_prompts(
        self,
        script: str,
        image_count: int,
        context: EpisodeContext,
        visual_theme: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """이미지 프롬프트 생성"""
        prompts = []

        # 1. 썸네일 프롬프트
        thumbnail_prompt = self._generate_thumbnail_prompt(context, visual_theme)
        prompts.append(thumbnail_prompt)

        # 2. 씬별 프롬프트
        scenes = context.scenes or self._split_script_to_scenes(script, image_count - 1)

        for i, scene_text in enumerate(scenes):
            scene_name = self._get_scene_name(i, len(scenes))
            scene_prompt = self._generate_scene_prompt(
                scene_index=i + 1,
                scene_name=scene_name,
                scene_text=scene_text,
                context=context,
                visual_theme=visual_theme,
            )
            prompts.append(scene_prompt)

        return prompts

    def _split_script_to_scenes(self, script: str, num_scenes: int) -> List[str]:
        """대본을 씬 수에 맞게 분할"""
        script_length = len(script)
        chunk_size = script_length // num_scenes

        scenes = []
        for i in range(num_scenes):
            start = i * chunk_size
            end = start + chunk_size if i < num_scenes - 1 else script_length
            scenes.append(script[start:end])

        return scenes

    def _get_scene_name(self, index: int, total: int) -> str:
        """씬 인덱스에 따른 씬 이름 반환"""
        if total <= 5:
            scene_names = ["오프닝", "전개", "클라이맥스", "해결", "엔딩"]
            return scene_names[index] if index < len(scene_names) else "전개"

        # 이미지가 많을 경우 비율로 배분
        ratio = index / total
        if ratio < 0.15:
            return "오프닝"
        elif ratio < 0.35:
            return "전개"
        elif ratio < 0.6:
            return "클라이맥스"
        elif ratio < 0.85:
            return "해결"
        else:
            return "엔딩"

    def _generate_thumbnail_prompt(
        self,
        context: EpisodeContext,
        visual_theme: Dict[str, Any]
    ) -> Dict[str, Any]:
        """썸네일 프롬프트 생성"""
        # 주인공 비주얼
        muying = CHARACTER_VISUALS["무영"]

        # 파트별 테마 반영
        palette = visual_theme["palette"]
        mood = visual_theme["mood"]

        prompt = f"""
{self.quality_tags}, {self.base_style},
{muying['appearance']}, {muying['costume']},
powerful stance, looking at viewer with intense gaze,
{muying['signature_elements'][0]} emanating from sword,
{visual_theme['environment']},
{visual_theme['lighting']}, {palette} color scheme,
epic cinematic composition, dramatic atmosphere,
youtube thumbnail style, high impact visual
""".strip().replace("\n", " ")

        return {
            "scene_index": 0,
            "scene_name": "썸네일",
            "image_type": "thumbnail",
            "prompt": prompt,
            "negative_prompt": self.negative_prompt,
            "description": f"EP{context.episode_number:03d} 썸네일: 무영 히어로 샷",
            "aspect_ratio": "16:9",
            "priority": "highest",
        }

    def _generate_scene_prompt(
        self,
        scene_index: int,
        scene_name: str,
        scene_text: str,
        context: EpisodeContext,
        visual_theme: Dict[str, Any]
    ) -> Dict[str, Any]:
        """개별 씬 프롬프트 생성"""
        # 씬 타입 정보
        scene_type_info = SCENE_IMAGE_TYPES.get(scene_name, SCENE_IMAGE_TYPES["전개"])
        image_type = scene_type_info["primary_type"]
        type_template = IMAGE_TYPE_TEMPLATES.get(image_type, IMAGE_TYPE_TEMPLATES["atmosphere"])

        # 씬에서 핵심 요소 추출
        key_elements = self._extract_key_elements(scene_text, context)

        # 등장 캐릭터 추출
        characters_in_scene = self._detect_characters(scene_text, context)

        # 캐릭터 비주얼 정보
        character_descriptions = []
        for char_name in characters_in_scene[:2]:  # 최대 2명
            char_key = char_name.split(" (")[0] if " (" in char_name else char_name
            if char_key in CHARACTER_VISUALS:
                char_visual = CHARACTER_VISUALS[char_key]
                character_descriptions.append(
                    f"{char_visual['appearance']}, {char_visual['costume']}"
                )

        # 프롬프트 조합
        prompt_parts = [
            self.quality_tags,
            self.base_style,
        ]

        # 캐릭터 추가
        if character_descriptions:
            prompt_parts.append(", ".join(character_descriptions))

        # 씬 타입 구도
        prompt_parts.append(type_template["composition"])

        # 핵심 요소
        if key_elements:
            prompt_parts.append(", ".join(key_elements[:3]))

        # 환경과 조명
        prompt_parts.append(visual_theme["environment"])
        prompt_parts.append(visual_theme["lighting"])
        prompt_parts.append(f"{visual_theme['palette']} color scheme")

        # 분위기
        prompt_parts.append(f"{scene_type_info['mood']} atmosphere")

        prompt = ", ".join(prompt_parts)

        return {
            "scene_index": scene_index,
            "scene_name": scene_name,
            "image_type": image_type,
            "prompt": prompt,
            "negative_prompt": self.negative_prompt,
            "description": f"씬{scene_index}: {scene_name} - {', '.join(key_elements[:2])}",
            "aspect_ratio": "16:9",
            "characters": characters_in_scene,
            "mood": scene_type_info["mood"],
        }

    def _extract_key_elements(
        self,
        scene_text: str,
        context: EpisodeContext
    ) -> List[str]:
        """씬에서 핵심 시각 요소 추출"""
        elements = []

        # 전투 관련
        battle_patterns = [
            (r"검[기세]", "sword energy slash"),
            (r"전투|싸움|공격", "combat scene"),
            (r"혈기", "crimson energy"),
            (r"마법|마력", "magical energy"),
        ]

        for pattern, element in battle_patterns:
            if re.search(pattern, scene_text):
                elements.append(element)

        # 감정 관련
        emotion_patterns = [
            (r"분노|화가", "angry expression"),
            (r"슬[픔퍼]", "sad mood"),
            (r"기쁨|웃", "joyful"),
            (r"긴장|두려", "tense atmosphere"),
        ]

        for pattern, element in emotion_patterns:
            if re.search(pattern, scene_text):
                elements.append(element)

        # 환경 관련
        environment_patterns = [
            (r"숲|나무", "forest setting"),
            (r"성|궁전", "castle/palace"),
            (r"밤|달", "night scene, moonlight"),
            (r"새벽|아침", "dawn"),
        ]

        for pattern, element in environment_patterns:
            if re.search(pattern, scene_text):
                elements.append(element)

        return elements[:5] if elements else ["dark fantasy scene"]

    def _detect_characters(
        self,
        scene_text: str,
        context: EpisodeContext
    ) -> List[str]:
        """씬에 등장하는 캐릭터 감지"""
        characters = []

        # 이름으로 감지
        character_names = {
            "무영": "무영 (주인공)",
            "라이트닝": "라이트닝 (늑대)",
            "카이든": "카이든 (라이벌)",
            "에이라": "에이라 (히로인)",
            "공주": "이그니스 공주",
            "혈마": "혈마",
        }

        for name, full_name in character_names.items():
            if name in scene_text:
                characters.append(full_name)

        # 무영은 대부분 등장
        if "무영 (주인공)" not in characters:
            # 주인공 언급이 많으면 추가
            if any(word in scene_text for word in ["그는", "그가", "자신", "검을"]):
                characters.insert(0, "무영 (주인공)")

        return characters

    def _generate_thumbnail_guide(
        self,
        context: EpisodeContext,
        visual_theme: Dict[str, Any]
    ) -> Dict[str, Any]:
        """썸네일 디자인 가이드"""
        episode_num = context.episode_number
        title = context.title or f"EP{episode_num:03d}"

        # 텍스트 제안
        text_suggestions = [
            {
                "line1": title[:10] if len(title) > 10 else title,
                "line2": f"EP{episode_num:03d}",
                "style": "impact, large font",
            },
            {
                "line1": context.part_name,
                "line2": title[:15],
                "style": "dramatic, serif font",
            },
        ]

        return {
            "recommended_style": "dark fantasy manhwa",
            "color_scheme": visual_theme["palette"],
            "text_suggestions": text_suggestions,
            "composition_tips": [
                "중앙에 무영 배치 (히어로 샷)",
                "검기 또는 마법 이펙트로 시선 유도",
                "우하단에 텍스트 영역 확보",
                "고대비로 가독성 확보",
            ],
            "avoid": [
                "너무 어두운 배경 (썸네일에서 안 보임)",
                "복잡한 배경 (시선 분산)",
                "작은 글씨",
            ],
        }


# =============================================================================
# 동기 실행 래퍼
# =============================================================================
def generate_image_guide(
    context: EpisodeContext,
    image_count: int = None
) -> Dict[str, Any]:
    """
    이미지 가이드 생성 (동기 버전)

    Args:
        context: 에피소드 컨텍스트 (script 필수)
        image_count: 이미지 개수 (자동 계산)

    Returns:
        이미지 가이드
    """
    import asyncio

    agent = ImageAgent()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        agent.execute(context, image_count=image_count)
    )

    if result.success:
        return result.data
    else:
        raise Exception(result.error)


def calculate_image_count(script: str) -> int:
    """대본 기반 이미지 개수 계산"""
    agent = ImageAgent()
    return agent._calculate_image_count(script)


def get_character_visual(character_name: str) -> Optional[Dict[str, Any]]:
    """캐릭터 비주얼 정보 조회"""
    return CHARACTER_VISUALS.get(character_name)


def get_part_visual_theme(part: int) -> Dict[str, Any]:
    """파트별 비주얼 테마 조회"""
    return PART_VISUAL_THEMES.get(part, PART_VISUAL_THEMES[1])


def enhance_prompt_with_style(prompt: str, part: int = 1) -> str:
    """
    프롬프트에 스타일 강제 적용

    Args:
        prompt: 원본 프롬프트
        part: 파트 번호

    Returns:
        스타일 적용된 프롬프트
    """
    agent = ImageAgent()
    visual_theme = PART_VISUAL_THEMES.get(part, PART_VISUAL_THEMES[1])

    enhanced = f"""
{agent.quality_tags}, {agent.base_style},
{prompt},
{visual_theme['environment']},
{visual_theme['lighting']},
{visual_theme['palette']} color scheme,
{visual_theme['mood']} atmosphere
""".strip().replace("\n", " ")

    return enhanced


def validate_image_prompts(
    prompts: List[Dict[str, Any]],
    min_count: int = 5
) -> Dict[str, Any]:
    """
    이미지 프롬프트 검증

    Args:
        prompts: 프롬프트 목록
        min_count: 최소 개수

    Returns:
        검증 결과
    """
    issues = []
    warnings = []

    # 개수 검증
    if len(prompts) < min_count:
        issues.append(f"이미지 개수 부족: {len(prompts)}개 (최소 {min_count}개)")

    # 썸네일 확인
    has_thumbnail = any(p.get("scene_index") == 0 for p in prompts)
    if not has_thumbnail:
        warnings.append("썸네일 프롬프트가 없습니다")

    # 금지 요소 검사
    forbidden_in_prompt = ["text", "logo", "watermark"]
    for i, prompt_data in enumerate(prompts):
        prompt_text = prompt_data.get("prompt", "").lower()

        for word in forbidden_in_prompt:
            if word in prompt_text and f"no {word}" not in prompt_text:
                warnings.append(f"프롬프트 {i}: '{word}' 포함 (네거티브에 있어야 함)")

    # 네거티브 프롬프트 확인
    for i, prompt_data in enumerate(prompts):
        negative = prompt_data.get("negative_prompt", "")
        if not negative:
            warnings.append(f"프롬프트 {i}: 네거티브 프롬프트 없음")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "prompt_count": len(prompts),
    }


def validate_image_prompts_strict(
    prompts: List[Dict[str, Any]],
    min_count: int = 5
) -> Dict[str, Any]:
    """
    이미지 프롬프트 엄격 검증 (블로킹)

    Raises:
        ValueError: 필수 기준 미충족 시
    """
    result = validate_image_prompts(prompts, min_count)

    if not result["valid"]:
        issues_str = "\n".join(f"  - {issue}" for issue in result["issues"])
        raise ValueError(f"이미지 프롬프트 검증 실패:\n{issues_str}")

    if result["warnings"]:
        warnings_str = "\n".join(f"  ⚠️ {w}" for w in result["warnings"])
        print(f"[ImageAgent] 경고:\n{warnings_str}")

    print(f"[ImageAgent] ✓ 이미지 프롬프트 검증 통과: {len(prompts)}개")
    return result

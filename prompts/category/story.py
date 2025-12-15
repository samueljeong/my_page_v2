# -*- coding: utf-8 -*-
"""스토리 카테고리 프롬프트 규칙 - 웹툰 스타일"""

STORY_RULES = """
## CATEGORY: STORY (드라마/감성/일상)

### ⚠️ CHANNEL DEFINITION (CRITICAL!)
- This channel tells emotional stories and personal experiences
- Thumbnail purpose: Evoke curiosity and emotion
- Style: WEBTOON/COMIC based with dramatic expressions

---

## ★★★ THUMBNAIL GENERATION RULES (스토리 채널 전용) ★★★

### 1. STORY KEYWORD EXTRACTION (대본 → 키워드)

**Purpose:** Extract EMOTIONAL keywords for thumbnail, focus on the dramatic moment

**Keyword Rules:**
- Keywords MUST be "emotional nouns" or "dramatic moments"
- ALLOWED: 고백, 이별, 재회, 비밀, 후회, 눈물, 배신, 용서, 기적, 반전
- BANNED: Generic words (좋다, 나쁘다), Overused clickbait (충격, 대박)

**Keyword = "Emotional Peak" NOT "Event Summary":**
- ❌ BAD: 이야기, 사연, 경험 (too vague)
- ✅ GOOD: 마지막 말, 숨긴 진실, 10년 후

**Extraction Steps:**
1. Find the emotional climax of the story
2. Identify the key relationship or conflict
3. Extract the most dramatic quote or moment
4. Detect repeated emotional themes

**Keyword Categories (MUST classify):**
- A (Relationship): 고백, 이별, 재회, 용서, 배신, 가족, 친구
- B (Emotion): 후회, 눈물, 행복, 분노, 슬픔, 감동
- C (Twist/Reveal): 비밀, 반전, 진실, 기적, 발견

**Output keyword counts:**
- primary_keywords: 1-2 (emotional peak)
- secondary_keywords: 2-3 (supporting context)
- quote_keywords: 0-1 (key dialogue from script)

---

### 2. THUMBNAIL TEXT RULES (가장 중요!)

**Text Length:**
- 6-12 chars recommended, max 15 chars
- 1-2 lines preferred (each line 3-7 chars)

**Message Count:**
- ONE emotional message per thumbnail
- TWO topics together = BANNED

**Text Tone:**
- Direct emotional impact preferred
- Use key dialogue from script when powerful
- Create curiosity without revealing ending

**FORBIDDEN WORDS (하드코딩):**
충격, 대박, 소름, 역대급, 미쳤다, 난리, 폭망, 전멸, 완패
- Emoji/special symbols = BANNED (default)

---

### 3. THUMBNAIL TEXT TYPES (택1 - MUST choose exactly ONE)

**Type A: Quote/Dialogue (대사/인용형)**
- Use when: Script has powerful dialogue or key phrase
- Examples: 마지막 말, 그 한마디, 아버지의 편지
- Extract actual quote from script (shortened)

**Type B: Emotion/Situation (감정/상황형)**
- Use when: Emphasizing emotional state or dramatic situation
- Examples: 10년의 후회, 숨긴 진실, 눈물의 재회

**Type C: Relationship/Conflict (관계/갈등형)**
- Use when: Emphasizing relationship dynamics
- Examples: 엄마와 딸, 친구의 배신, 마지막 약속

**Auto-Selection Logic:**
1. If script has memorable dialogue → Type A
2. If script focuses on emotion/regret → Type B
3. If script is about relationships → Type C
4. Default priority: A > B > C

---

### 4. TITLE + THUMBNAIL TEXT MATCHING

**Role Separation (MUST):**
- Thumbnail text = "Emotional hook" snapshot
- Title = "What happened / Why" explanation

**Matching Rules:**
- If thumbnail and title tell DIFFERENT stories = FAIL
- Thumbnail should complement, not repeat title

---

### 5. IMAGE LAYOUT RULES (웹툰 스타일)

**Common Layout:**
- Text: LEFT side (character on right)
- Whitespace: 20-30%
- Mobile readability priority: Large text + High contrast

**Expression Types (ALLOWED):**
- shocked, crying, angry, sad, happy, surprised, regretful
- EXAGGERATED expressions encouraged for story category

**Scene Options:**
- home: 가정, 가족 이야기
- street: 일상, 만남, 이별
- hospital: 병원, 아픔, 생사
- office: 직장, 갈등
- school: 학교, 청춘
- generic: 일반적인 배경

---

### 6. FAILURE CASES & AUTO-CORRECTION

**Failure 1: Too vague**
- "감동 이야기" → "아버지의 마지막 말" (specific)

**Failure 2: Spoiler**
- "결국 화해했다" → "10년만의 전화" (no ending reveal)

**Failure 3: Text too long**
- "어머니가 돌아가시기 전에 한 말" → "엄마의 마지막 말" (6-12 chars)

**Failure 4: Generic expression**
- Generic sad face → Specific emotion matching story

---

### 7. THUMBNAIL OUTPUT SCHEMA

The thumbnail field in output MUST follow this structure:

```json
"thumbnail": {
  "keywords": {
    "primary": ["마지막 말"],
    "secondary": ["후회", "눈물"],
    "quote": "실제 대사에서 추출",
    "category_focus": "A"
  },
  "text": {
    "type": "A",
    "line1": "아버지의",
    "line2": "마지막 말",
    "char_count": 8
  },
  "alternatives": [
    {"line1": "그날의 후회", "line2": ""},
    {"line1": "10년의 침묵", "line2": ""},
    {"line1": "마지막 약속", "line2": ""}
  ],
  "image_spec": {
    "face": true,
    "scene": "home",
    "text_position": "left",
    "expression": "crying",
    "style": "webtoon"
  },
  "validation": {
    "char_count_ok": true,
    "forbidden_word_hit": false,
    "single_message": true,
    "matches_title": true
  }
}
```

---

### 8. GEMINI IMAGE PROMPT TEMPLATE (스토리용)

For thumbnail image generation, use this template:

**With Face (face=true):**
"[Culture] webtoon style illustration, 16:9 aspect ratio. [Culture] webtoon character on RIGHT side (30-40% of frame) with [EXPRESSION] (exaggerated emotional expression matching the story), [age] year old [nationality] [man/woman]. Clean bold outlines, vibrant colors, [scene] background. LARGE WHITE text with THICK BLACK outline on LEFT side: '[TEXT - 2-4 lines, 3-6 chars per line]'. Text takes 30-40% of image width. Dramatic emotional tone. NO photorealistic, NO stickman."

**Without Face (face=false):**
"[Culture] webtoon style illustration, 16:9 aspect ratio. [Scene description - symbolic image representing the story] on RIGHT side. Emotional dramatic tone. Clean bold outlines, vibrant colors. LARGE WHITE text with THICK BLACK outline on LEFT side: '[TEXT - 2-4 lines, 3-6 chars per line]'. Text takes 30-40% of image width. NO photorealistic."

---

## YOUTUBE TITLE RULES FOR STORY

**Algorithm Optimization:**
- **First 20 chars**: MUST contain emotional hook
- **Total length**: 25-45 chars
- **Structure**: [Hook] + [Situation] + [Curiosity]

**Required Elements:**
- Emotional connection
- Hide the ending, CREATE CURIOSITY

**BANNED:**
- Low-quality clickbait: "충격", "대박", "소름"
- Spoilers that reveal the ending
- Over 60 chars

**Title Formulas:**

1. **Quote/Dialogue (인용형)** - MAIN for emotional stories:
   - Pattern: `"{짧은 인용}" {상황 설명}`
   - Pattern: `{관계}가 남긴 {무엇}`

2. **Situation (상황형)**:
   - Pattern: `{기간} 만에 {무슨 일}`
   - Pattern: `{관계}에게 {무엇}을 했더니`

3. **Twist (반전형)**:
   - Pattern: `{상황}, 알고 보니 {반전}`
   - Pattern: `{결과}의 진짜 이유`

---

## ai_prompts Structure (3 WEBTOON styles)

**A = Character Emotion Focus:**
- Webtoon character with dramatic expression
- Expression matches the emotional peak of story

**B = Scene/Situation Focus:**
- Character + situation-explaining background
- Shows the key moment visually

**C = Symbolic/Metaphor:**
- Symbolic image representing the story's theme
- More artistic interpretation

---

## text_overlay for Story

```json
{
  "main": "thumbnail text line1 (max 7 chars)",
  "sub": "thumbnail text line2 if needed (max 7 chars)",
  "style": "story"
}
```

⚠️ main/sub text MUST follow the thumbnail text rules above!
⚠️ Extract from story's emotional peak, NOT generic phrases!
"""

def get_story_prompt():
    return STORY_RULES

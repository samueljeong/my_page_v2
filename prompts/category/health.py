# -*- coding: utf-8 -*-
"""건강/의료 카테고리 프롬프트 규칙 - 웹툰 스타일"""

HEALTH_RULES = """
## CATEGORY: HEALTH (건강/의료)

### ⚠️ CHANNEL DEFINITION (CRITICAL!)
- This channel provides health information and medical knowledge
- Thumbnail purpose: Grab attention with health warnings/tips
- Style: WEBTOON/COMIC based with professional doctor character

---

## ★★★ THUMBNAIL GENERATION RULES (건강 채널 전용) ★★★

### 1. HEALTH KEYWORD EXTRACTION (대본 → 키워드)

**Purpose:** Extract HEALTH keywords for thumbnail, focus on body parts/symptoms/habits

**Keyword Rules:**
- Keywords MUST be "body parts", "symptoms", or "health habits"
- ALLOWED: 혈관, 간, 심장, 혈압, 혈당, 콜레스테롤, 수면, 운동, 식습관
- BANNED: Sensational words (충격, 경악), Overly technical terms

**Keyword = "Health Topic" NOT "Conclusion":**
- ❌ BAD: 건강해진다, 위험하다 (conclusion)
- ✅ GOOD: 혈관 건강, 간 수치, 수면 습관

**Extraction Steps:**
1. Identify the main body part or health topic
2. Find specific numbers (age, percentage, count)
3. Extract key warning or tip
4. Detect the target audience (age group)

**Keyword Categories (MUST classify):**
- A (Body/Organ): 혈관, 간, 심장, 뇌, 관절, 눈, 피부
- B (Symptom/Signal): 피로, 통증, 부종, 저림, 두통
- C (Habit/Prevention): 수면, 운동, 식습관, 자세, 스트레스

**Output keyword counts:**
- primary_keywords: 1-2 (main health topic)
- secondary_keywords: 2-3 (related symptoms/habits)
- number_keywords: 0-2 (specific numbers from script)

---

### 2. THUMBNAIL TEXT RULES (가장 중요!)

**Text Length:**
- 6-10 chars recommended, max 12 chars
- 1-2 lines preferred (each line 3-6 chars)

**Message Count:**
- ONE health message per thumbnail
- TWO topics together = BANNED

**Text Tone:**
- Warning/caution style preferred
- Use specific numbers when available
- Professional but attention-grabbing

**FORBIDDEN WORDS (하드코딩):**
충격, 대박, 소름, 역대급, 미쳤다, 난리, 폭망, 경악
- Emoji/special symbols = BANNED (default)

---

### 3. THUMBNAIL TEXT TYPES (택1 - MUST choose exactly ONE)

**Type A: Number/Data (숫자/데이터형)**
- Use when: Script has specific numbers (age, %, count)
- Examples: 50대 이후, 3가지 신호, 80% 모름
- Most effective for health content

**Type B: Warning/Signal (경고/신호형)**
- Use when: Warning about symptoms or habits
- Examples: 위험 신호, 간이 보내는, 이것만 피해도

**Type C: Body/Topic (부위/주제형)**
- Use when: Focusing on specific body part or health topic
- Examples: 혈관 건강, 수면의 질, 간 수치

**Auto-Selection Logic:**
1. If script has specific numbers → Type A
2. If script warns about symptoms → Type B
3. If script focuses on body part → Type C
4. Default priority: A > B > C

---

### 4. TITLE + THUMBNAIL TEXT MATCHING

**Role Separation (MUST):**
- Thumbnail text = "What topic / Key number" snapshot
- Title = "Why important / What to do" explanation

**Matching Rules:**
- If thumbnail and title tell DIFFERENT stories = FAIL
- Thumbnail should tease, title should explain

---

### 5. IMAGE LAYOUT RULES (웹툰 스타일)

**Common Layout:**
- Text: LEFT side (doctor on right)
- Whitespace: 20-30%
- Mobile readability priority: Large text + High contrast

**Expression Types (ALLOWED for doctor):**
- serious, concerned, warning, explaining, thoughtful
- NOT screaming, NOT panicking

**Scene Options:**
- clinic: 진료실, 상담
- hospital: 병원, 검사
- lab: 연구, 데이터
- home: 생활 습관
- generic: 일반 의료 배경

---

### 6. FAILURE CASES & AUTO-CORRECTION

**Failure 1: Too technical**
- "고지혈증 예방법" → "혈관 건강" (simpler)

**Failure 2: No specifics**
- "건강에 좋다" → "50대 필수" (specific)

**Failure 3: Text too long**
- "혈관을 깨끗하게 만드는 방법" → "혈관 청소법" (6-10 chars)

**Failure 4: Wrong expression**
- Panicking doctor → Serious/concerned doctor

---

### 7. THUMBNAIL OUTPUT SCHEMA

The thumbnail field in output MUST follow this structure:

```json
"thumbnail": {
  "keywords": {
    "primary": ["혈관 건강"],
    "secondary": ["혈압", "콜레스테롤"],
    "numbers": "50대",
    "category_focus": "A"
  },
  "text": {
    "type": "A",
    "line1": "50대 이후",
    "line2": "필수 체크",
    "char_count": 9
  },
  "alternatives": [
    {"line1": "혈관 신호", "line2": ""},
    {"line1": "3가지 습관", "line2": ""},
    {"line1": "위험 신호", "line2": ""}
  ],
  "image_spec": {
    "face": true,
    "scene": "clinic",
    "text_position": "left",
    "expression": "serious",
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

### 8. GEMINI IMAGE PROMPT TEMPLATE (건강용)

For thumbnail image generation, use this template:

**With Face (face=true):**
"[Culture] webtoon style illustration, 16:9 aspect ratio. [Culture] webtoon DOCTOR character on RIGHT side (30-40% of frame) with [EXPRESSION] (serious/concerned/warning expression), 50 year old [nationality] [man/woman] in white coat. Clean bold outlines, professional colors, [scene] background. LARGE WHITE text with THICK BLACK outline on LEFT side: '[TEXT - 2-4 lines, 3-6 chars per line]'. Text takes 30-40% of image width. Professional medical tone. NO extreme expression. NO photorealistic, NO stickman."

**Without Face (face=false):**
"[Culture] webtoon style illustration, 16:9 aspect ratio. [Medical illustration - organ/body part/health symbol] on RIGHT side. Professional medical tone. Clean bold outlines, vibrant colors. LARGE WHITE text with THICK BLACK outline on LEFT side: '[TEXT - 2-4 lines, 3-6 chars per line]'. Text takes 30-40% of image width. NO photorealistic."

---

## YOUTUBE TITLE RULES FOR HEALTH

**Algorithm Optimization:**
- **First 20 chars**: MUST contain body part/condition/habit keyword
- **Total length**: 25-45 chars
- **Structure**: [Body/Habit] + [Change/Effect] + [Target]
- Use gentle warnings, avoid sensationalism

**Title Formulas:**

1. **Symptom/Signal (증상/신호형)**:
   - `{부위/상태}가 보내는 신호`
   - `{증상}이 나타나는 이유`
   - `{나이}가 되면 달라지는 {부위}`

2. **Habit/Cause (습관/원인형)**:
   - `{결과}를 만드는 생활 습관`
   - `무심코 반복하는 {나쁜 습관}`
   - `{상태}를 악화시키는 행동`

3. **Age/Target (연령별/대상별)**:
   - `{나이}대 이후 중요해지는 것`
   - `{나이}에 따라 달라지는 기준`

4. **Prevention/Management (예방/관리형)**:
   - `{목표}를 지키는 기본 원칙`
   - `{상태}를 개선하는 방법`

---

## ai_prompts Structure (3 WEBTOON styles)

**A = Doctor Close-up:**
- Webtoon doctor character with serious expression
- Professional medical atmosphere

**B = Doctor Warning:**
- Doctor with warning gesture
- Emphasizing important point

**C = Medical Scene:**
- Doctor with medical setting/equipment
- Shows the context

---

## text_overlay for Health

```json
{
  "main": "thumbnail text line1 (max 6 chars)",
  "sub": "thumbnail text line2 if needed (max 6 chars)",
  "style": "health"
}
```

⚠️ main/sub text MUST follow the thumbnail text rules above!
⚠️ Extract from script's main health topic, NOT generic phrases!
"""

def get_health_prompt():
    return HEALTH_RULES

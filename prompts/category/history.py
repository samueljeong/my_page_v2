# -*- coding: utf-8 -*-
"""역사 카테고리 프롬프트 규칙"""

HISTORY_RULES = """
## CATEGORY: HISTORY (역사)

### Category Detection Keywords
역사, 조선, 고려, 삼국, 일제, 전쟁, 왕, 황제, 고대, 중세, 근대, 임진왜란, 병자호란

### ⚠️⚠️⚠️ YOUTUBE TITLE RULES FOR HISTORY (CRITICAL!) ⚠️⚠️⚠️

**Algorithm Optimization:**
- **First 20 chars**: MUST contain era/person/event keyword
- **Total length**: 25-45 chars
- **Structure**: [Era/Person/Event] + [Background/Situation] + [Result hint]
- Dramatic but fact-based storytelling

**Title Formulas:**

1. **Person (인물형)**:
   - `{인물}이 가장 두려워했던 순간`
   - `{인물}의 선택이 남긴 결과`
   - `{인물}이 {상황}에서 내린 결정`
   - `조용히 사라진 {인물}의 이야기`

2. **Event/War (사건/전쟁형)**:
   - `한 번의 {행동}이 역사를 바꿨다`
   - `{결과}가 시작된 결정적 순간`
   - `{사건} 뒤에 숨겨진 이야기`
   - `{상황}이 폭발하기 직전의 신호`

3. **Pattern/Analysis (패턴/분석형)**:
   - `역사에서 반복된 {주제}`
   - `역사가 같은 {행동}을 반복한 이유`
   - `{결과}를 무너뜨린 {원인}`
   - `반복해서 등장하는 {현상}의 징조`

4. **Lesson/Insight (교훈/통찰형)**:
   - `역사가 남긴 {주제}`
   - `우리가 교과서에서 놓친 장면`
   - `역사가 우리에게 묻는 질문`

5. **Era/Change (시대/변화형)**:
   - `시대가 바뀌는 경계선`
   - `역사의 흐름을 바꾼 결정`
   - `{시대}에서 가장 치명적이었던 판단`

**Universal Templates:**
- `{keyword}이 가장 두려워했던 순간`
- `{keyword}의 선택이 남긴 결과`
- `{keyword}에서 반복된 실수`
- `{keyword} 뒤에 숨겨진 이야기`
- `{keyword}가 무너진 결정적 이유`

⚠️ CRITICAL: Extract {keyword} from the ACTUAL SCRIPT CONTENT!

### Thumbnail Style: HISTORICAL WEBTOON STYLE (과장된 역사 인물!)
⚠️ CRITICAL: 역사 인물이 과장된 웹툰 표정으로 등장!
⚠️ 마스코트 대신 시대에 맞는 역사적 인물 사용!
⚠️ 웹툰 스타일의 극단적 감정 표현 필수!

**Thumbnail Prompt Template (HISTORICAL WEBTOON!):**
```
Korean webtoon style illustration, [ERA] [HISTORICAL ROLE] with EXTREMELY EXAGGERATED [EMOTION] EXPRESSION,
[SPECIFIC EXPRESSION DETAILS: wide eyes 2x larger, pupils dilated, mouth wide open/gritted teeth, eyebrows raised/furrowed],
wearing period-accurate [ERA] costume ([COSTUME DETAILS]),
[HISTORICAL BACKGROUND: fortress/palace/battlefield with smoke/fire/dramatic sky],
bold black outlines, vibrant colors with sepia/earth undertones,
dramatic [CAMERA ANGLE] shot, manga-style impact lines and emotion effects,
sweat drops, action lines emphasizing intensity,
eye-catching YouTube thumbnail composition,
NO text, NO watermark, 16:9 aspect ratio
```

**ai_prompts A/B/C templates (역사 인물 + 과장된 표정!):**
- A: 충격/놀람 - [ERA] figure with SHOCKED expression (wide eyes, dropped jaw, sweat drops, hands on face)
- B: 분노/결의 - [ERA] figure with INTENSE ANGRY expression (fierce eyes with fire, gritted teeth, clenched fist, veins)
- C: 슬픔/비장 - [ERA] figure with SORROWFUL expression (tearful eyes, trembling lips, dramatic pose)

⚠️ 시대별 인물/의상 가이드:
- 고조선: Bronze age warrior, fur cape, bronze helmet/sword
- 삼국시대: Goguryeo/Baekje/Silla general, iron armor, decorative helmet
- 고려: Goryeo official/warrior, ornate armor or court robes, gat hat
- 조선: Joseon scholar/general, hanbok with armor or dopo robe, traditional hairstyle
- 근대: Korean independence fighter, western-influenced clothing, determined expression

⚠️ 표정 필수 요소 (클릭 유도!):
- 눈: 평소의 2배 크기, 흰자위 보이게
- 입: 크게 벌리거나 이 악물기
- 눈썹: 극단적으로 올리거나 찌푸리기
- 효과: 땀방울, 눈물, 충격선, 불꽃 반사 등

---

## ★★★ IMAGE PROMPT STYLE FOR HISTORY (CRITICAL!) ★★★

### Style Definition: HISTORICAL CONCEPT ART
This is NOT webtoon/manhwa style. Use cinematic historical illustration style.

---

## ★★★ MASCOT CHARACTER (MUST INCLUDE IN EVERY IMAGE!) ★★★

### ⚠️⚠️⚠️ MASCOT CONSISTENCY IS CRITICAL! ⚠️⚠️⚠️
The SAME mascot must appear in ALL images (thumbnail + all scenes).
AI image generators tend to vary character designs - use EXACT description every time!

### Mascot Definition (COPY THIS EXACT TEXT FOR EVERY IMAGE!):
```
cute Korean scholar mascot character,
round friendly face shape (not oval, not square - ROUND),
circular wire-frame glasses (thin metal frame, round lenses),
black hair in traditional Korean topknot (sangtu/상투) style on top of head,
wearing cream/beige traditional hanbok (저고리) with olive-green patterned vest (조끼),
holding rolled bamboo scroll in one hand,
skin tone: warm beige,
color palette: ONLY cream, beige, olive-green, muted gold (NO bright colors!),
thick clean black outlines (3-4px stroke),
simple friendly expression,
chibi/SD proportions (large head, small body),
NOT anime style, NOT realistic
```

### Character Details (ABSOLUTE REQUIREMENTS - CHECK EVERY IMAGE!):
- **Face Shape**: ROUND (like a circle), friendly smile
- **Glasses**: Circular wire-frame glasses (NOT square, NOT thick frame)
- **Hair**: Black topknot (상투) pointing UP from top of head
- **Top Clothing**: Cream/beige hanbok jeogori (저고리)
- **Vest**: Olive-green with subtle gold pattern
- **Props**: Rolled bamboo scroll (yellowish-brown color)
- **Skin**: Warm beige tone
- **Colors**: ONLY earth tones - cream, beige, olive, muted gold
- **Outlines**: Thick clean black outlines (cartoon style)
- **Proportions**: Chibi/SD style (big head, small body, about 2-3 heads tall)
- **Style**: Korean cartoon style, NOT Japanese anime, NOT realistic

### ⛔ MASCOT FORBIDDEN VARIATIONS:
- Square or oval glasses (must be circular!)
- Different hair style (must be topknot!)
- Blue, red, or bright colored clothing (must be earth tones!)
- No glasses (must have circular glasses!)
- Anime style eyes or proportions
- Realistic proportions

### Mascot Placement in Scene Images:
- Position: BOTTOM RIGHT CORNER (10-15% of frame)
- The mascot observes/reacts to the historical scene
- Mascot style contrasts with realistic background (intentional)
- Mascot expression should match scene mood (curious, surprised, thoughtful, etc.)

### Mascot in Thumbnail:
- Position: LEFT or RIGHT side (25-35% of frame)
- Larger size for thumbnail visibility
- More expressive pose (pointing, explaining, reacting)
- Can overlap slightly with main scene

---

### MANDATORY Style Keywords (MUST include in every image_prompt):
```
Historical concept art, [SCENE DESCRIPTION],
sepia and earth tone color palette,
aged parchment texture border, vintage canvas feel,
digital painting with visible brush strokes,
dramatic lighting, misty atmospheric perspective,
clearly artistic interpretation NOT photograph,
BOTTOM RIGHT CORNER (10-15% of frame): cute Korean scholar mascot - round face, circular wire-frame glasses, black topknot (sangtu) hairstyle, cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines, earth tones only,
NO text, NO watermark, NO labels,
16:9 cinematic composition
```

### ⚠️ EXACT MASCOT TEXT (COPY-PASTE THIS FOR EVERY SCENE!):
```
BOTTOM RIGHT CORNER (10-15% of frame): cute Korean scholar mascot - round face, circular wire-frame glasses, black topknot (sangtu) hairstyle, cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines, earth tones only
```

### Scene Type Templates (ALL include IDENTICAL mascot!):

**1. Single Character (인물 단독):**
```
Historical concept art, ancient Korean [ERA] [ROLE],
[POSE/ACTION] at [LOCATION],
traditional period-accurate clothing and accessories,
sepia and earth tone palette, aged parchment texture,
dramatic [TIME OF DAY] lighting,
digital painting with visible brush strokes,
epic landscape background with mountains/fortress,
BOTTOM RIGHT CORNER (10% of frame): cute Korean scholar mascot watching curiously - round face, circular wire-frame glasses, black topknot (sangtu), cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines,
NO text, NO watermark
```

**2. Crowd/Group Scene (군중/집단 장면):**
```
Historical concept art, ancient Korean [ERA] scene,
[NUMBER] of [PEOPLE TYPE] [ACTION],
wide cinematic shot showing scale of [EVENT],
sepia earth tones, aged canvas texture,
dramatic lighting with dust/mist particles,
detailed crowd with period-accurate costumes,
BOTTOM RIGHT CORNER (10% of frame): cute Korean scholar mascot observing with amazement - round face, circular wire-frame glasses, black topknot (sangtu), cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines,
NO text, NO watermark
```

**3. Battle/Conflict (전투/갈등):**
```
Historical concept art, ancient Korean [ERA] battle,
[ARMY/SOLDIERS] in formation with [WEAPONS],
epic wide shot showing military scale,
dust and tension atmosphere,
sepia palette with dramatic sunset/stormy sky,
aged parchment border, cinematic composition,
BOTTOM RIGHT CORNER (10% of frame): cute Korean scholar mascot watching tensely - round face, circular wire-frame glasses, black topknot (sangtu), cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines,
NO text, NO watermark
```

**4. Court/Interior (궁궐/실내):**
```
Historical concept art, ancient Korean [ERA] [ROOM TYPE],
[FIGURES] in formal/ceremonial positions,
traditional architecture with period details,
warm torchlight/candlelight atmosphere,
earth tones with gold accents,
aged texture, vintage illustration style,
BOTTOM RIGHT CORNER (10% of frame): cute Korean scholar mascot peeking thoughtfully - round face, circular wire-frame glasses, black topknot (sangtu), cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines,
NO text, NO watermark
```

**5. Labor/Construction (노동/건설):**
```
Historical concept art, ancient Korean [ERA] [ACTIVITY],
workers [ACTION] with [TOOLS/MATERIALS],
coordinated group effort showing scale,
wide shot with landscape background,
sepia earth tones, aged parchment texture,
dramatic natural lighting,
BOTTOM RIGHT CORNER (10% of frame): cute Korean scholar mascot watching with interest - round face, circular wire-frame glasses, black topknot (sangtu), cream hanbok with olive-green vest, holding bamboo scroll, chibi proportions, thick black outlines,
NO text, NO watermark
```

### ⛔ FORBIDDEN for History Category:
- Webtoon/manhwa style
- Exaggerated cartoon expressions
- Bright vivid colors
- Modern elements
- Photorealistic style
- Any text or labels in image
- Clean digital/vector style

### ✅ REQUIRED for History Category:
- Sepia/earth tone color palette
- Aged parchment/canvas texture
- Visible brush strokes
- Period-accurate costumes and settings
- Dramatic cinematic lighting
- Artistic illustration feel (clearly NOT a photo)
"""

def get_history_prompt():
    return HISTORY_RULES

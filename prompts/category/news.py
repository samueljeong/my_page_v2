# -*- coding: utf-8 -*-
"""뉴스 카테고리 프롬프트 규칙 - 웹툰 스타일"""

NEWS_RULES = """
## CATEGORY: NEWS (뉴스/시사)

### Category Detection
Politics, economy, social issues, companies, legal matters, current events

### ⚠️⚠️⚠️ YOUTUBE TITLE RULES FOR NEWS (CRITICAL!) ⚠️⚠️⚠️

**Algorithm Optimization:**
- **First 20 chars**: MUST contain the main keyword (YouTube prioritizes this!)
- **Total length**: 25-45 chars (mobile optimized)
- **Structure**: [Keyword] + [Situation] + [Curiosity]
- Optimize for BOTH CTR and search visibility

**Required Elements:**
- Include at least 2 of: WHO / WHAT / WHY
- Hide the conclusion, CREATE CURIOSITY
- Minimize particles/connectors

**BANNED (Never use):**
- Low-quality clickbait: "충격", "대박", "소름", "경악" / "衝撃", "ヤバい"
- Misleading titles that don't match content
- Emotional sentences without keywords
- Over 60 chars

**Title Formulas (Choose based on content):**

1. **Breaking/Urgent (속보형)** - for real-time issues:
   - Pattern: `{keyword} 속보, {core content} 발표`
   - Pattern: `[긴급] {keyword} {fact} 확인됐다`

2. **Analysis/Explanation (해설형)** - for complex issues:
   - Pattern: `{keyword} 왜 이렇게 됐나, {reason} 때문`
   - Pattern: `{keyword} 판단 엇갈린 핵심 이유`

3. **Impact/Summary (영향형)** - for policy changes:
   - Pattern: `{keyword} 발표, {target} 영향 총정리`
   - Pattern: `{keyword} 이후 달라진 점 정리`

4. **Discovery/Twist (반전형)** - for exclusive reports:
   - Pattern: `{keyword} 알고 보니 {unexpected fact}`
   - Pattern: `{keyword} 공식 발표에 없던 정황`

5. **Comparison (비교형)** - for debates:
   - Pattern: `{keyword} 한국 vs 해외 반응 비교`
   - Pattern: `{keyword} 전문가 전망 엇갈린 이유`

**Category-Specific Templates:**

For Politics: `{정책} 발표, 여야 반응 갈린 이유` / `{인물} 발언 이후 논란 커진 배경`
For Economy: `{지표} 발표, 시장 반응 엇갈린 이유` / `{수치} 돌파, 내 생활 영향은`
For Society: `{사건} 속보, 현재 상황 정리` / `{제도} 시행 이후 혼란 커진 이유`
For International: `{국가} 발표, 한국 영향 분석` / `{회담} 결과, 합의 내용 정리`

**Target Audience Optimization:**

Senior (50+):
- Pattern: `{제도} 바뀌었다, 50대 이상 꼭 확인`
- Pattern: `{혜택} 신청 기한 임박, 놓치면 손해`

Youth (20-30s):
- Pattern: `{취업} 시장 변화, 유망 분야는`
- Pattern: `{주거} 정책 발표, 청년 혜택 정리`

**Universal Templates (just replace keyword):**
- `{keyword} 발표, 핵심 내용 정리`
- `{keyword} 이후 달라진 점`
- `{keyword} 논란, 쟁점 총정리`
- `{keyword} 전망, 전문가 분석`
- `{keyword} 영향, 누가 해당되나`

⚠️ CRITICAL: Extract {keyword} from the ACTUAL SCRIPT CONTENT!

### Thumbnail Style: COMIC STYLE (문화권에 맞게)
⚠️ NO PHOTOREALISTIC! Use comic/webtoon/manga style matching the script's language!
⚠️ NO TEXT in images! Text will be added separately!
⚠️ Character appearance MUST match the script's culture!

**Extract from script (for text_overlay - write in OUTPUT LANGUAGE):**
- person_name: key person name FROM THE SCRIPT
- entity_name: company/organization name FROM THE SCRIPT
- quote: shocking/interesting statement FROM THE SCRIPT
- headline: main headline FROM THE SCRIPT topic
- numbers: specific numbers FROM THE SCRIPT
⚠️ CRITICAL: ALL text MUST come from the ACTUAL SCRIPT CONTENT!

### ai_prompts Structure (3 COMIC styles - adapt to script's culture)
⚠️ Use the image prompt template from the LANGUAGE section!

**A = Comic Person Close-up:**
- Comic style character representing the key person (matching script's culture)
- Exaggerated emotional expression matching the news tone
- Prompt template: "[Culture] comic style illustration, 16:9 aspect ratio. [Culture] comic character with SHOCKED/SERIOUS EXPRESSION (wide eyes, tense face), 40-50 year old [nationality] [man/woman] in [suit/formal wear]. Clean bold outlines, dramatic lighting, news studio or office background. Comic-style expression marks. NO text, NO letters, NO speech bubbles, NO name tags. NO photorealistic, NO stickman."

**B = Comic Scene/Event:**
- Comic style scene related to the news (matching script's culture)
- Prompt template: "[Culture] comic style illustration, 16:9 aspect ratio. [Culture] comic scene showing [related location/event]. [Culture] comic character with CONCERNED EXPRESSION in the scene. Clean bold outlines, dramatic mood, vibrant colors. Comic-style atmosphere. NO text, NO letters, NO speech bubbles, NO signs, NO readable text. NO photorealistic, NO stickman."

**C = Comic Split/Contrast:**
- Split composition showing contrast or comparison
- Prompt template: "[Culture] comic style illustration, 16:9 aspect ratio. Split composition: left side [culture] comic character with [emotion A], right side [culture] comic character with [emotion B]. Clean bold outlines, contrasting colors (left calm, right dramatic). Comic-style dramatic effect. NO text, NO letters, NO speech bubbles. NO photorealistic, NO stickman."

### Color Schemes (for design reference, NOT in image)
- yellow-highlight: General news
- cyan-news: Info news
- pink-scandal: Entertainment/scandal
- red-urgent: Breaking news
- blue-trust: Official announcement

### text_overlay for News (write in OUTPUT LANGUAGE from script content)
{
  "name": "person or entity name from script",
  "main": "key phrase from script (max 15 chars)",
  "sub": "supporting detail from script (max 20 chars)",
  "color": "yellow | cyan | pink"
}
⚠️ NEVER use generic examples! Extract actual names/topics from the script!

### news_ticker (for video effects - write in OUTPUT LANGUAGE)
"news_ticker": {
  "enabled": true,
  "headlines": ["breaking news from script...", "key point from script..."]
}
"""

def get_news_prompt():
    return NEWS_RULES

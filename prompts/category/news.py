# -*- coding: utf-8 -*-
"""뉴스 카테고리 프롬프트 규칙"""

NEWS_RULES = """
## CATEGORY: NEWS (뉴스/시사)

### Category Detection Keywords
정치인, 대통령, 국회, 정당, 경제, 주가, 환율, 부동산,
사건, 사고, 사회 이슈, 논쟁, 갈등, 기업, 브랜드,
법원, 검찰, 재판

### Thumbnail Style: PHOTOREALISTIC NEWS
Real person photos, news photography style

**Extract from script:**
- person_name: 핵심 인물 이름 (조진웅, 윤석열 등)
- entity_name: 기업/기관명 (쿠팡, 삼성전자 등)
- quote: 충격적/흥미로운 발언 "따옴표"
- headline: 핵심 헤드라인 2줄
- numbers: 강조 숫자 (30년, 3370만)

**IMPORTANT:** If person_name or entity_name exists, MUST include in thumbnail text!

### ai_prompts Structure (3 styles)

**A = Person Close-up:**
- Key person's face/upper body close-up
- Dark gradient at bottom for text
- Emotional expression (shocked, angry, confident)
- Prompt: "korean [gender] in [age]s, [expression] expression, close-up portrait, dark navy gradient at bottom for text space, news photography style, photorealistic, 16:9"

**B = Scene/Event:**
- News scene or related location
- Space for text overlay
- Prompt: "korean national assembly/courtroom/stock exchange building, dramatic lighting, news photography style, space for text overlay at bottom, 16:9"

**C = Split Comparison:**
- 2-split screen: left vs right
- Before/After, Pro/Con, Two people contrast
- Prompt: "split screen comparison, left: [option A], right: [option B], dramatic lighting, versus composition, 16:9"

### Color Schemes
- yellow-highlight: General news (MBC style)
- cyan-news: Info news (SBS style)
- pink-scandal: Entertainment/scandal (TV조선 style)
- red-urgent: Breaking news
- blue-trust: Official announcement

### text_overlay for News
{
  "name": "인물명 또는 기업명",
  "main": "핵심 문구 (15자 이내)",
  "sub": "부연 설명 (20자 이내)",
  "color": "yellow | cyan | pink"
}

### news_ticker (NEWS ONLY!)
"news_ticker": {
  "enabled": true,
  "headlines": ["속보: ...", "이슈: ...", "핵심: ..."]
}
"""

def get_news_prompt():
    return NEWS_RULES

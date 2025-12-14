# -*- coding: utf-8 -*-
"""요리/레시피 카테고리 프롬프트 규칙"""

COOKING_RULES = """
## CATEGORY: COOKING (요리/레시피)

### Category Detection Keywords
요리, 레시피, 음식, 맛있게, 만들기, 재료, 손질, 조리, 굽기, 볶기, 찌기, 반찬, 국, 찌개

### ⚠️⚠️⚠️ YOUTUBE TITLE RULES FOR COOKING (CRITICAL!) ⚠️⚠️⚠️

**Algorithm Optimization:**
- **First 20 chars**: MUST contain food/dish name keyword
- **Total length**: 25-45 chars
- **Structure**: [Food name] + [Method/Tip] + [Result]
- Make it sound easy and appetizing

**Title Formulas:**

1. **Core Recipe (핵심 레시피형)**:
   - `{음식} 맛있게 만드는 핵심 포인트`
   - `{음식} 실패 없이 만드는 방법`
   - `{재료}로 만드는 간단한 {음식}`

2. **Tips/Secrets (비법/팁형)**:
   - `{음식} 더 맛있어지는 한 가지`
   - `{음식} 망하는 이유와 해결법`
   - `{음식} 맛의 차이를 만드는 것`

3. **Quick/Easy (간편/시간형)**:
   - `{시간}분이면 완성되는 {음식}`
   - `냉장고 재료로 만드는 {음식}`
   - `{음식} 남은 것 활용하는 방법`

4. **Ingredients (재료형)**:
   - `{재료} 제대로 손질하는 방법`
   - `{계절} 제철 {재료}로 만드는 요리`
   - `{재료} 고르는 법과 보관법`

5. **Comparison (비교형)**:
   - `{식당} 맛 따라잡는 {음식} 비법`
   - `{음식} 더 건강하게 만드는 법`
   - `{음식} A vs B 뭐가 더 맛있을까`

**Universal Templates:**
- `{keyword} 맛있게 만드는 핵심 포인트`
- `{keyword} 실패 없이 만드는 방법`
- `{keyword} 더 맛있어지는 비법`
- `{keyword} 손질하는 방법`
- `{keyword}로 만드는 간단 요리`

⚠️ CRITICAL: Extract {keyword} from the ACTUAL SCRIPT CONTENT!

### Thumbnail Style: COMIC STYLE (문화권에 맞게)
⚠️ Appetizing food illustration or cooking scene
⚠️ Character with happy/satisfied expression, chef outfit optional

**ai_prompts templates:**
- A: Delicious food close-up with steam/sparkle effects
- B: Character cooking with happy expression
- C: Before/After transformation of ingredients to dish
"""

def get_cooking_prompt():
    return COOKING_RULES

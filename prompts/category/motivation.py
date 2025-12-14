# -*- coding: utf-8 -*-
"""자기계발/동기부여 카테고리 프롬프트 규칙"""

MOTIVATION_RULES = """
## CATEGORY: MOTIVATION (자기계발/동기부여)

### Category Detection Keywords
자기계발, 습관, 목표, 성공, 실패, 시간관리, 집중력, 번아웃, 동기부여, 성장, 변화, 마인드

### ⚠️⚠️⚠️ YOUTUBE TITLE RULES FOR MOTIVATION (CRITICAL!) ⚠️⚠️⚠️

**Algorithm Optimization:**
- **First 20 chars**: MUST contain self-improvement keyword
- **Total length**: 25-45 chars
- **Structure**: [Topic/Habit] + [Process/Reason] + [Outcome hint]
- Focus on relatable struggles and actionable insights

**Title Formulas:**

1. **Habit/Process (습관/과정형)**:
   - `{습관}이 만들어지는 과정`
   - `{습관}을 유지하기 어려운 이유`
   - `작은 변화가 큰 차이를 만드는 이유`

2. **Problem/Reason (문제/이유형)**:
   - `시간이 없다고 느끼는 진짜 이유`
   - `미루는 습관이 생기는 구조`
   - `집중력이 흐트러지는 원인`

3. **Comparison/Difference (비교/차이형)**:
   - `목표를 이루는 사람들의 공통점`
   - `성장하는 사람과 정체된 사람의 차이`
   - `부정적인 생각이 반복되는 이유`

4. **Recovery/Change (회복/변화형)**:
   - `번아웃이 오는 과정과 회복법`
   - `실패 후 다시 시작하는 방법`
   - `불안할 때 마음을 다스리는 방법`

5. **Action/Start (행동/시작형)**:
   - `{나이}에 시작해도 괜찮은 이유`
   - `생각이 행동으로 이어지는 구조`
   - `하루를 바꾸는 아침 루틴의 원리`

**Universal Templates:**
- `{keyword}이 만들어지는 과정`
- `{keyword}이 어려운 이유`
- `{keyword}하는 사람들의 공통점`
- `{keyword}이 반복되는 이유`
- `{keyword}을 바꾸는 방법`

⚠️ CRITICAL: Extract {keyword} from the ACTUAL SCRIPT CONTENT!

### Thumbnail Style: COMIC STYLE (문화권에 맞게)
⚠️ Relatable character showing determination or reflection
⚠️ Avoid overly dramatic or preachy tone

**ai_prompts templates:**
- A: Character with determined expression, sunrise/light background
- B: Character in contemplation, thought bubble effects
- C: Before/After transformation showing growth
"""

def get_motivation_prompt():
    return MOTIVATION_RULES

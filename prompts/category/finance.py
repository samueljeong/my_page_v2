# -*- coding: utf-8 -*-
"""재테크/경제 카테고리 프롬프트 규칙"""

FINANCE_RULES = """
## CATEGORY: FINANCE (재테크/경제)

### Category Detection Keywords
재테크, 투자, 주식, 부동산, 저축, 금리, 대출, 연금, 세금, 자산, 월급, 적금, ETF

### ⚠️⚠️⚠️ YOUTUBE TITLE RULES FOR FINANCE (CRITICAL!) ⚠️⚠️⚠️

**Algorithm Optimization:**
- **First 20 chars**: MUST contain money/investment keyword
- **Total length**: 25-45 chars
- **Structure**: [Topic] + [Specific content] + [Target/Result]
- Realistic and specific, avoid get-rich-quick tone

**Title Formulas:**

1. **Basics/Start (기초/시작형)**:
   - `{금액}으로 시작하는 현실적인 재테크`
   - `{나이}대 자산관리에서 중요한 것`
   - `{투자방식} 시작 전 알아야 할 것`

2. **Problem/Reason (문제/이유형)**:
   - `돈이 모이지 않는 진짜 이유`
   - `재테크 실패하는 사람들의 공통점`
   - `월급에서 돈이 새는 이유`

3. **Practical Tips (실용 팁형)**:
   - `{상황}일 때 돈 관리하는 방법`
   - `{금융상품} 선택할 때 확인할 것`
   - `{대출} 이자 줄이는 현실적 방법`

4. **Knowledge (지식형)**:
   - `{세금/제도} 모르면 손해보는 정보`
   - `신용점수가 중요한 진짜 이유`
   - `{지표} 이 숫자의 의미`

5. **Strategy (전략형)**:
   - `{시기}에 달라지는 재테크 전략`
   - `부자들이 하지 않는 돈 습관`
   - `경제 뉴스 읽는 법 (초보자용)`

**Universal Templates:**
- `{keyword}으로 시작하는 현실적인 재테크`
- `{keyword}가 중요한 진짜 이유`
- `{keyword} 모르면 손해보는 정보`
- `{keyword} 선택할 때 확인할 것`
- `{keyword}에서 실패하는 이유`

⚠️ CRITICAL: Extract {keyword} from the ACTUAL SCRIPT CONTENT!

### Thumbnail Style: COMIC STYLE (문화권에 맞게)
⚠️ Professional but approachable look
⚠️ Character with confident or thoughtful expression

**ai_prompts templates:**
- A: Character with money/chart background, confident expression
- B: Character analyzing documents or phone
- C: Before/After financial situation comparison
"""

def get_finance_prompt():
    return FINANCE_RULES

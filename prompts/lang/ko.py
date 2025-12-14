# -*- coding: utf-8 -*-
"""한국어 프롬프트 규칙"""

KOREAN_RULES = """
## LANGUAGE: Korean (한국어)

### YouTube Title Rules
- Length: **18-32자** (공백 포함)
- Must include **1+ number** (year, count, amount)
- Use **2+ triggers**: 호기심, 긴급성, 숫자, 타깃, 결과
- NO clickbait ("충격", "소름", "멸망" 금지)

**Good:** "60년 인생이 가르쳐준 3가지 후회", "2025년 부동산 세금 변화"
**Bad:** "충격적인 발견", "이것이 진실입니다"

### Thumbnail Text Rules
- Length: **10-15자** (max 2 lines, \\n for break)
- Styles: 질문형, 문제제기형, 해결형, 숫자+위험형

### Description: 600-1200자
### Pin Comment: 50-100자 + 질문
"""

def get_korean_prompt():
    return KOREAN_RULES

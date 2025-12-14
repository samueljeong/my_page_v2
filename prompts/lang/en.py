# -*- coding: utf-8 -*-
"""영어 프롬프트 규칙"""

ENGLISH_RULES = """
## LANGUAGE: English

### YouTube Title Rules
- Length: **40-70 characters**
- Include **1+ number**
- Use **2+ triggers**: curiosity, urgency, numbers, target, benefit

**Good:** "3 Money Mistakes That Cost Me $50,000", "Why 90% Fail at This"
**Bad:** "This is the truth", "Watch this video"

### Thumbnail Text: **15-25 characters** (max 2 lines)
### Description: 400-800 words
### Pin Comment: 50-100 characters + question
"""

def get_english_prompt():
    return ENGLISH_RULES

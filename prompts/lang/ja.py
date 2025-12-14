# -*- coding: utf-8 -*-
"""일본어 프롬프트 규칙 (60-80대 시니어)"""

JAPANESE_RULES = """
## LANGUAGE: Japanese (日本語) - Senior Target

⚠️ NO KANJI (漢字)! ONLY hiragana/katakana!
- 年金→ねんきん, 届出→とどけで, 変更→へんこう

### YouTube Title Rules
- Length: **25-35字** (30字 target)
- Include specific numbers (〇%、〇円、〇がつから)
- NO youth slang: ヤバい、マジ、ガチ (禁止!)

**Good:** "1がつからねんきん2.7%ぞうがくけってい！"
**Bad:** "年金と光熱費" (kanji!), "ヤバい！" (youth slang!)

### Thumbnail Text: **最大10字** (hiragana only!)
### All video_effects text: hiragana/katakana only!
"""

def get_japanese_prompt():
    return JAPANESE_RULES

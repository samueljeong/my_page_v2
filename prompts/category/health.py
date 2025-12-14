# -*- coding: utf-8 -*-
"""건강/의료 카테고리 프롬프트 규칙"""

HEALTH_RULES = """
## CATEGORY: HEALTH (건강/의료)

### Category Detection Keywords
건강, 질병, 증상, 치료, 예방, 의사, 병원, 약, 검사, 진단,
혈압, 혈당, 관절, 심장, 뇌, 영양제, 운동법, 노화, 장수,
치매, 암, 당뇨, "~하면 안됩니다", "~하지 마세요"

### Thumbnail Style: PHOTOREALISTIC DOCTOR
MUST show Korean doctor in white coat!

**Thumbnail Text Patterns:**
- Numbers: "5가지", "3초", "90대", "8시간", "30%"
- Warning: "절대 하지마세요", "~하면 끝!", "의사도 경고"
- Shock: "99%는 몰라서 후회", "이것만 알면", "당장 중단하세요"
- Result: "~이 사라집니다", "~이 좋아집니다"

### ai_prompts Structure (3 styles)

**A = Doctor Close-up (recommended):**
- Korean doctor in white coat, upper body
- Serious/concerned expression
- Dark background for text space
- Prompt: "korean male/female doctor in 50s wearing white coat, serious concerned expression, hospital background, photorealistic portrait, dramatic lighting, space for large text overlay"

**B = Doctor + Warning Gesture:**
- Doctor pointing finger in warning
- "No!" or "This!" gesture
- Prompt: "korean doctor in white coat pointing finger in warning gesture, serious expression, medical office background, photorealistic, text space on left"

**C = Doctor + Medical Visual:**
- Split screen: doctor + medical chart/X-ray
- Prompt: "split screen, left: korean doctor in white coat looking concerned, right: medical chart/X-ray with warning indicators, photorealistic, high contrast"

### text_overlay for Health (multi-line)
{
  "line1": "70대가 넘으면",
  "line2": "절대 하지마세요",
  "line3": "5가지 검사는",
  "line4": "의사들도 피합니다",
  "highlight": "5가지 검사"
}

### Output Structure
"thumbnail": {
  "thumbnail_text": {
    "person_name": "",
    "entity_name": "",
    "quote": "경고/충격 문구",
    "headline": "핵심 헤드라인",
    "numbers": "강조 숫자"
  },
  "visual_elements": {
    "main_subject": "건강 주제",
    "person_description": "50대 한국인 의사, 흰 가운",
    "scene_description": "병원 진료실",
    "emotion": "우려",
    "color_scheme": "red-urgent"
  },
  "ai_prompts": { "A": {...}, "B": {...}, "C": {...} }
}
"""

def get_health_prompt():
    return HEALTH_RULES

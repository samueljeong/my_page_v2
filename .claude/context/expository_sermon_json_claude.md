# 강해설교 JSON - Claude 제안안

> 작성일: 2025-01-27
> GPT 분석 + Claude 분석 종합

---

## Step1: 본문 분석 (해석 원자료)

```json
{
  "step": "step1",
  "style": "강해설교",
  "role": "성경 본문 분석가",
  "principle": "강해설교는 본문이 말하는 그대로 해석하는 데 초점을 둔다. Step1은 설교를 위한 해석 원자료만 제공하며, 적용이나 설교적 언어는 포함하지 않는다.",

  "output_format": {
    "historical_background": {
      "label": "역사·정황 배경",
      "description": "본문의 시대·저자·수신자·정치·사회·지리·신앙적 상황을 6-10문장으로 정리",
      "required_items": [
        "기록 시기",
        "저자와 수신자",
        "문맥(앞뒤 단락과의 연결)",
        "당시 공동체가 직면한 문제",
        "지리적·문화적 배경",
        "작성 목적"
      ]
    },

    "literary_structure": {
      "label": "문학 구조",
      "description": "본문의 자연스러운 단락 구분과 흐름",
      "required_items": [
        "단락 구분 (절 범위 명시)",
        "각 단락의 핵심 내용",
        "단락 간 논리적 연결"
      ],
      "example": "1-3절: 감사 → 4-6절: 권면 → 7-10절: 결론"
    },

    "verse_structure": {
      "label": "절별 분석",
      "description": "각 절의 관찰(Observation) 중심 분석",
      "per_verse": {
        "observation": "문법·주어·동사·핵심 표현 분석",
        "meaning": "문장이 말하는 객관적 의미",
        "connection": "앞뒤 절과 연결되는 논리적 흐름"
      },
      "purpose": "강해설교의 핵심인 절-by-절 해석의 기초 자료"
    },

    "section_grouping": {
      "label": "대지 단위 절 그룹핑",
      "description": "Step2의 3대지 구성을 위해 절을 3개 섹션으로 사전 그룹핑",
      "format": {
        "section1": { "verses": "절 범위", "theme": "섹션 주제 한 문장" },
        "section2": { "verses": "절 범위", "theme": "섹션 주제 한 문장" },
        "section3": { "verses": "절 범위", "theme": "섹션 주제 한 문장" }
      },
      "note": "이 그룹핑은 본문의 자연스러운 흐름을 따르며, Step2에서 조정 가능"
    },

    "key_terms": {
      "label": "핵심 단어·원어 분석",
      "description": "본문의 주요 단어 5-8개에 대한 원어 분석",
      "per_term": {
        "word": "본문에 나온 단어",
        "original": "원어 (헬라어/히브리어)",
        "basic_meaning": "기본 사전적 의미",
        "contextual_meaning": "본문 안에서의 뉘앙스",
        "theological_significance": "신학적 의미 (있는 경우)"
      }
    },

    "cross_references": {
      "label": "보충 성경구절",
      "description": "본문 해석을 강화하는 직접 연결 구절 4-6개",
      "format": {
        "reference": "성경구절 (예: 롬 8:15)",
        "connection_reason": "본문과 연결되는 이유 한 문장"
      },
      "purpose": "성경이 성경을 해석하게 하는 원칙 적용"
    },

    "author_intent": {
      "label": "저자 의도",
      "description": "저자가 이 본문을 기록한 목적을 3-5문장으로 정리",
      "focus": "수신자에게 전달하고자 한 핵심 메시지"
    },

    "theological_summary": {
      "label": "신학적 요약",
      "description": "본문이 말하는 하나님·인간·구원·순종에 관한 신학적 핵심 3-5문장",
      "exclude": ["적용", "권면", "감성적 표현"],
      "focus": "오직 '이 본문이 신학적으로 무엇을 말하는가'"
    },

    "logical_flow": {
      "label": "본문 논리 흐름",
      "description": "본문 전체의 논리적 흐름을 한 줄로 정리",
      "example": "상황 제시 → 문제 인식 → 해결 방향 → 결론"
    }
  }
}
```

---

## Step2: 설교 구조 설계

```json
{
  "step": "step2",
  "style": "강해설교",
  "role": "설교 구조 설계자",
  "principle": "Step1의 분석 자료를 바탕으로 설교 구조만을 설계한다. 새로운 해석이나 신학적 주장을 추가하지 않는다.",

  "required_input": [
    "step1.section_grouping",
    "step1.literary_structure",
    "step1.theological_summary",
    "step1.key_terms",
    "step1.cross_references"
  ],

  "output_format": {
    "title": {
      "label": "설교 제목",
      "description": "본문 전체 내용을 압축한 제목"
    },

    "scripture_text": {
      "label": "본문",
      "description": "장과 절 범위 (예: 디모데후서 1:3-8)"
    },

    "introduction": {
      "label": "서론 구성",
      "components": {
        "hook": {
          "label": "도입",
          "description": "청중의 관심을 끄는 질문이나 상황 1-2문장"
        },
        "previous_context": {
          "label": "이전 본문 요약",
          "description": "직전 본문과의 연결 3-4문장"
        },
        "historical_link": {
          "label": "역사적 배경",
          "description": "본문 이해에 필요한 최소한의 배경 2-3문장",
          "source": "step1.historical_background에서 발췌"
        },
        "sermon_direction": {
          "label": "설교 방향",
          "description": "이 설교가 다루는 핵심 질문 또는 메시지 1문장"
        }
      }
    },

    "big_idea": {
      "label": "핵심 주제 (Big Idea)",
      "description": "설교 전체를 관통하는 단 하나의 메시지",
      "example": "하나님은 두려움에 빠진 자녀에게 담대함의 영을 주신다"
    },

    "sermon_outline": {
      "label": "3대지 구조",
      "description": "본문을 3개의 대지로 나눔. Step1의 section_grouping을 기반으로 구성",
      "format": {
        "point1": {
          "title": "대지1 제목",
          "verses": "절 범위 (예: 3-5절)",
          "summary": "핵심 내용 3-4문장",
          "key_term": "이 대지에서 강조할 원어 단어 (step1.key_terms에서 선택)",
          "supporting_verses": ["보충 구절1", "보충 구절2"]
        },
        "point2": {
          "title": "대지2 제목",
          "verses": "절 범위",
          "summary": "핵심 내용 3-4문장",
          "key_term": "원어 단어",
          "supporting_verses": ["보충 구절1", "보충 구절2"]
        },
        "point3": {
          "title": "대지3 제목",
          "verses": "절 범위",
          "summary": "핵심 내용 3-4문장",
          "key_term": "원어 단어",
          "supporting_verses": ["보충 구절1", "보충 구절2"]
        }
      }
    },

    "flow_connection": {
      "label": "대지 연결 흐름",
      "description": "대지1 → 대지2 → 대지3이 어떤 논리로 연결되는지 2-3문장"
    },

    "application_direction": {
      "label": "적용 방향",
      "description": "Step3에서 적용을 작성할 때 참고할 방향 2-3문장",
      "note": "구체적 적용은 Step3에서 작성"
    },

    "conclusion_direction": {
      "label": "결론 방향",
      "description": "설교 결론에서 강조할 핵심 메시지 방향 1-2문장"
    }
  },

  "writing_spec": {
    "style": "강해설교",
    "tone": "자연스러운 문장 흐름, 대화형",
    "interpretation": "본문에 충실한 해석",
    "vocabulary": "60-80대 성도도 이해 가능한 어휘",
    "avoid": ["과도한 수사", "감정적 과장", "본문에 없는 상상"]
  },

  "constraints": {
    "no_new_interpretation": "Step1에 없는 새로운 신학·해석 추가 금지",
    "balanced_points": "세 대지는 분량과 논리 비중이 균형 있게",
    "verse_coverage": "본문의 모든 절이 대지 안에 포함되어야 함"
  }
}
```

---

## Step3: 설교문 작성

```json
{
  "step": "step3",
  "style": "강해설교",
  "role": "설교문 작성자",
  "principle": "Step1의 해석 자료와 Step2의 구조를 변경 없이 그대로 반영하여 설교문을 작성한다.",

  "priority_order": {
    "1_최우선": "홈화면 설정 (분량, 예배유형, 대상, 특별참고사항)",
    "2_필수반영": "Step2 구조 (3대지, 절 범위, supporting_verses)",
    "3_핵심활용": "Step1 절별 분석 (verse_structure) + 원어 (key_terms)",
    "4_참고활용": "Step1 보충 구절 (cross_references), 저자 의도 (author_intent)"
  },

  "required_input": [
    "step1.verse_structure",
    "step1.key_terms",
    "step1.cross_references",
    "step1.author_intent",
    "step2.sermon_outline",
    "step2.big_idea",
    "step2.introduction",
    "step2.writing_spec",
    "system_settings (분량, 예배유형, 대상)"
  ],

  "use_from_step1": {
    "verse_structure": {
      "instruction": "각 절의 observation·meaning을 설교 본론에 자연스럽게 풀어서 강해",
      "format": "~절을 보면, '~'라고 되어 있습니다. 이것은 ~를 의미합니다.",
      "priority": "필수"
    },
    "key_terms": {
      "instruction": "각 대지에서 지정된 원어(key_term)를 설명에 포함",
      "format": "여기서 '~'라는 단어는 헬라어로 '~'인데, 이는 ~를 뜻합니다.",
      "frequency": "대지별 1회 이상",
      "priority": "필수"
    },
    "cross_references": {
      "instruction": "각 대지의 supporting_verses를 인용하여 해석 강화",
      "format": "~에서도 이렇게 말씀합니다.",
      "priority": "권장"
    },
    "author_intent": {
      "instruction": "결론부에서 저자 의도를 강조",
      "priority": "권장"
    }
  },

  "use_from_step2": {
    "sermon_outline": {
      "instruction": "3대지 구조와 절 범위를 그대로 유지",
      "priority": "필수 - 변경 금지"
    },
    "big_idea": {
      "instruction": "설교 전체를 관통하는 메시지로 유지, 결론에서 재강조",
      "priority": "필수"
    },
    "introduction": {
      "instruction": "hook, previous_context, historical_link, sermon_direction을 자연스러운 문장으로 확장",
      "priority": "필수"
    },
    "supporting_verses": {
      "instruction": "각 대지에서 지정된 보충 구절 인용",
      "priority": "필수"
    },
    "writing_spec": {
      "instruction": "tone, vocabulary, avoid 규칙을 설교문 전체에 적용",
      "priority": "필수"
    }
  },

  "writing_rules": {
    "structure": {
      "label": "설교 구조",
      "rules": [
        "서론 → 본론(대지1 → 대지2 → 대지3) → 결론 순서 유지",
        "각 대지는 해당 절 범위의 내용만 다룸",
        "대지 전환 시 연결 문장 필수 (예: '이제 다음 부분으로 넘어가겠습니다')"
      ]
    },
    "verse_exposition": {
      "label": "절별 강해",
      "rules": [
        "절을 인용한 후 meaning 설명",
        "verse_structure의 connection을 활용하여 흐름 연결",
        "절 순서대로 진행 (역순 또는 건너뛰기 금지)"
      ]
    },
    "original_language": {
      "label": "원어 활용",
      "rules": [
        "각 대지에서 지정된 key_term을 1회 이상 설명",
        "원어는 쉬운 설명과 함께 제시",
        "과도한 학문적 용어 사용 금지"
      ]
    },
    "scripture_citation": {
      "label": "성경 인용",
      "rules": [
        "각 대지의 supporting_verses 인용",
        "같은 구절 반복 인용 금지",
        "본문 외 구절은 supporting_verses에서만 선택"
      ]
    },
    "application": {
      "label": "적용",
      "rules": [
        "각 대지 끝에 신앙 적용 또는 일상 적용 1개",
        "추상적 권면이 아닌 구체적 행동 제시",
        "결론에서 전체 적용 요약"
      ]
    },
    "tone": {
      "label": "어조",
      "rules": [
        "대화형·설득형 톤 유지",
        "과도한 수사, 감정적 과장 금지",
        "대상(장년/청년/새벽)에 맞는 어휘 사용"
      ]
    }
  },

  "prohibitions": [
    "Step2의 대지 구조 변경 금지",
    "Step1에 없는 새로운 신학적 주장 금지",
    "본문에 없는 내용 상상 금지",
    "대지 순서 변경 금지",
    "지정된 절 범위 외의 내용 추가 금지"
  ],

  "output_structure": {
    "description": "순수 텍스트 형식으로 출력 (마크다운 기호 사용 금지)",
    "sections": [
      "서론",
      "본론 - 대지1 (제목, 절 강해, 원어 설명, 보충 구절, 적용)",
      "본론 - 대지2 (동일 구조)",
      "본론 - 대지3 (동일 구조)",
      "결론 (요약, big_idea 재강조, 결단 촉구)"
    ]
  }
}
```

---

## 변경 사항 요약 (기존 대비)

### Step1
| 항목 | 변경 내용 |
|------|----------|
| section_grouping | 신규 추가 - Step2 연결 강화 |
| author_intent | 신규 추가 - 결론부 활용 |
| logical_flow | 신규 추가 - 흐름 파악 |
| required_items | 각 필드에 필수 항목 명시 |

### Step2
| 항목 | 변경 내용 |
|------|----------|
| required_input | 신규 추가 - Step1 데이터 명시 |
| introduction | 4개 컴포넌트로 세분화 |
| key_term per point | 신규 추가 - 대지별 원어 지정 |
| supporting_verses | 대지별로 통합 (소대지별 제거) |
| flow_connection | 신규 추가 |
| constraints | 신규 추가 |
| writing_spec | 유지 (GPT 버전에서 누락된 것 복원) |

### Step3
| 항목 | 변경 내용 |
|------|----------|
| 원어 빈도 | "3회 이상" → "대지별 1회 이상" |
| 예화 규칙 | 필수에서 제거 (강해설교 원칙) |
| output_structure | markdown 제거 → 순수 텍스트 |
| prohibitions | 명확한 금지 사항 추가 |
| supporting_verses | 대지별로 통합 |

# Session Log: Step3 스타일별 지침 JSON 구조

## 작업 일자
2025-11-26

## 문제 상황
- Step1, Step2는 스타일별로 다른 JSON 지침이 있었지만, Step3는 공통 프롬프트만 사용
- Step1/Step2에서 체계적으로 분석해도 Step3가 이를 제대로 반영하지 못함
- 결과적으로 모든 스타일의 설교가 비슷하게 나오는 문제

## 해결 방향
Step3도 스타일마다 다른 지침 JSON을 사용하도록 변경

---

## 완료된 작업

### 1. 프론트엔드 (sermon.html)

#### 관리자 공간 UI 변경
- `renderGuideTabs()` 함수 수정
- Step1, Step2 탭 외에 **Step3 탭** 추가
- 스타일 선택 시 Step1, Step2, Step3 지침 모두 편집 가능

#### Step3 지침 서버 전송
- Step3 API 호출 시 `step3Guide` 추가 전송
- localStorage에서 `guide-{category}-{style}-step3` 키로 불러옴

### 2. 백엔드 (sermon_server.py)

#### /api/sermon/gpt-pro 엔드포인트
- `step3_guide = data.get("step3Guide")` 추가

#### build_step3_prompt_from_json 함수 전면 개편
- Step3 지침 (json_guide) 활용하도록 수정
- 우선순위 체계:
  1. 홈화면 설정 (최우선)
  2. Step3 스타일별 지침
  3. Step2 설교 구조 (필수 반영)
  4. Step1 분석 자료 (참고 활용)

---

## 다음 세션에서 해야 할 작업

### 1. Step3 지침 JSON 샘플 작성 (스타일별)

**3대지 설교 Step3 지침 예시:**
```json
{
  "step": "step3",
  "style": "3대지",
  "role": "설교문 작성자",
  "principle": "홈화면 설정값을 최우선으로, Step1/Step2 결과를 활용하여 설교문 작성",

  "priority_order": {
    "1_최우선": "홈화면 설정 (제목, 예배유형, 분량, 대상, 특별참고사항)",
    "2_필수반영": "Step2 구조 (3대지, 소대지, supporting_verses)",
    "3_참고활용": "Step1 분석 (cross_references, key_terms, logical_flow)"
  },

  "use_from_step1": {
    "cross_references": {
      "instruction": "각 대지에서 보충 성경구절로 인용",
      "format": "~말씀에서도 확인할 수 있듯이"
    },
    "logical_flow": {
      "instruction": "대지 간 연결의 흐름으로 활용"
    },
    "key_terms": {
      "instruction": "핵심 단어의 원어 의미를 설교에 녹여내기"
    }
  },

  "use_from_step2": {
    "supporting_verses": {
      "instruction": "각 소대지의 보충 성경구절 반드시 인용",
      "priority": "필수"
    },
    "big_idea": {
      "instruction": "설교 전체를 관통하는 메시지로 유지"
    },
    "detailed_points": {
      "instruction": "3대지+소대지 구조 유지 (분량에 맞게 조절)"
    }
  },

  "writing_rules": {
    "connection": {
      "label": "대지 연결",
      "rules": [
        "대지 전환 시 연결 문장 필수",
        "예: '~를 살펴보았습니다. 이제 ~를 보겠습니다.'"
      ]
    },
    "no_duplication": {
      "label": "중복 방지",
      "rules": [
        "소대지 간 내용 중복 금지",
        "같은 성경구절 반복 인용 금지"
      ]
    },
    "scripture_usage": {
      "label": "성경 인용",
      "rules": [
        "본문 외 보충 성경구절 필수",
        "구약-신약 연결 시도"
      ]
    }
  }
}
```

### 2. 강해설교 Step3 지침 작성

강해설교는 3대지와 다른 구조를 가지므로 별도 지침 필요:
- `verse_structure` 활용법
- 절별 강해 방식
- 원어 해석 강조 방식

### 3. Step4 지침 JSON 구조 설계 (필요시)

Step4는 "전체 복사" 기능으로 현재 별도 지침이 필요한지 확인 필요

### 4. 테스트

1. 관리자 공간에서 Step3 탭 클릭하여 지침 입력
2. Step3 실행하여 지침이 반영되는지 확인
3. 여러 스타일에서 결과가 차별화되는지 검증

---

## 파일 변경 목록

| 파일 | 변경 내용 |
|------|----------|
| `templates/sermon.html` | renderGuideTabs() 수정, Step3 지침 전송 추가 |
| `sermon_server.py` | step3_guide 받기, build_step3_prompt_from_json() 전면 개편 |

---

## 관련 함수/변수 위치

### 프론트엔드
- `renderGuideTabs()`: 약 3857행
- Step3 API 호출: 약 3382행
- `getGuideKey()`: 약 2769행

### 백엔드
- `build_step3_prompt_from_json()`: 약 1458행
- `/api/sermon/gpt-pro`: 약 1894행
- `step3_guide` 변수: 약 1943행

---

## 참고: 기존 Step1/Step2 JSON 구조

### Step1 (3대지 - 강해설교) output_format
```
- historical_background (배경 연구)
- literary_structure (절 구조 분석)
- verse_structure (절별 관찰)
- key_terms (핵심 단어 연구)
- cross_references (보충 성경구절)
- theological_observation (저자 의도)
- summary (신학 요약)
- logical_flow (논리적 전개 흐름)
```

### Step2 (3대지) output_format
```
- title (설교 제목)
- scripture_text (본문)
- ice_breaking (아이스브레이킹)
- introduction_context (서론)
- big_idea (핵심 주제)
- sermon_outline (3대지 구조)
- detailed_points (3대지 상세 설계)
- conclusion (결론)
- application_direction (적용 방향)
- writing_spec (작성 규격)
```

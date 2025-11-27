# 설교 스타일 JSON 설계 논의

> **마지막 업데이트**: 2025-11-27 05:21
> **작업 브랜치**: claude/continue-sermon-work-01AzCLQzz6AFzTC6nFRRQuzm

---

## 현재 작업 상태

**목표**: 강해설교 JSON 지침 확정 (Step1, Step2, Step3)

**진행 상황**:
- [x] 기존 강해설교 JSON 검토 완료
- [x] GPT 분석/개선안 검토 완료
- [ ] Claude 제안 JSON 작성 중
- [ ] 최종 JSON 확정
- [ ] 테스트

---

## 시스템 구조 요약

### API 파이프라인
```
Step1 (gpt-5) → Step2 (gpt-4o-mini) → Step3 (gpt-5)
   해석만         구조만              설교문만
```

### 핵심 파일
- `sermon_server.py`: 백엔드 API
- `templates/sermon.html`: 프론트엔드
- JSON 지침은 프론트엔드 스타일 설정에 저장됨

### JSON 처리 흐름
1. 프론트엔드에서 `guide` (Step1), `step2Guide`, `step3Guide` 전송
2. 백엔드 `build_prompt_from_json()` → 시스템 프롬프트 생성
3. GPT API 호출 → JSON 응답 → `format_json_result()` → 텍스트 변환

---

## GPT 분석 요약 (2025-01-27)

### 장점 6가지
1. Step1-2-3 역할 분리 완벽
2. 강해설교 핵심 4요소 포함 (역사정황, 절구조, 원어, 신학적관찰)
3. 절 범위 지정 강력
4. Step3 priority_order 훌륭
5. 절별 강해 규칙 안정적
6. API 시스템에 최적화

### 문제점 5가지
1. verse_structure → detailed_points 호환성 약함 (절-소대지 매칭)
2. key_terms "최소 3회 이상" 과도
3. application_direction 중복
4. supporting_verses 위치 애매 (대지별 vs 소대지별)
5. "예화 필수"는 강해설교와 충돌

### 개선 포인트 7가지
1. Step1에 section_grouping 추가 (절 그룹핑)
2. Step2에 소대지 구조 추가
3. supporting_verses는 대지 단위로만
4. 예화 규칙 유연화
5. Step1에 author_intent 추가
6. Step2 서론 → Step3 연결 강화
7. 원어 인용 "대지별 1회 이상"으로 완화

---

## Claude 추가 분석

### 추가 우려사항
1. `section_grouping`이 Step1에 있으면 "해석만" 원칙 위반 가능성
2. `writing_spec`이 GPT 버전에서 누락됨
3. `output_format: markdown`은 우리 시스템과 호환성 문제

### 최종 방향
- GPT 개선안 기반 + 시스템 호환성 고려
- writing_spec Step2에 유지
- output_format markdown 제거
- supporting_verses 대지별로 통일

---

## 다음 세션에서 할 일

1. Claude 제안 JSON (Step1, Step2, Step3) 검토
2. 최종 JSON 확정
3. 실제 본문으로 테스트

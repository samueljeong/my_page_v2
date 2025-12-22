# 자동화 파이프라인 가이드

> 마지막 업데이트: 2025-12-22

---

## 파이프라인 구조

```
scripts/
├── news_pipeline/        # 뉴스 자동화
├── history_pipeline/     # 한국사 자동화
├── mystery_pipeline/     # 미스테리 자동화
│   ├── 해외 미스테리    # 영어 위키백과
│   └── 한국 미스테리    # 나무위키 (2025-12-22 추가)
└── PIPELINE_README.md    # 이 파일
```

---

## 상태 코드 정의

| 상태 | 설명 | 다음 단계 |
|------|------|----------|
| `준비` | 자료 수집 완료, 대본 작성 대기 | 사용자가 `대기`로 변경 시 영상 생성 시작 |
| `대기` | 영상 생성 파이프라인 대기 중 | 자동으로 처리 |
| `처리중` | 영상 생성 중 | 자동 완료 대기 |
| `완료` | 영상 업로드 완료 | - |
| `실패` | 오류 발생 | 에러메시지 확인 후 재시도 |

---

## 1. 뉴스 파이프라인 (NEWS)

### 워크플로우
```
RSS 수집 → 채널별 필터링 → 후보 선정 → Opus 입력 생성 → 시트 저장
```

### API
```bash
POST /api/news/run-pipeline?channel=ECON
POST /api/news/run-pipeline?channel=ECON&force=1
```

### 환경변수
| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NEWS_SHEET_ID` | - | 뉴스 시트 ID |
| `OPUS_TOP_N` | 3 | 저장할 후보 수 |
| `LLM_ENABLED` | 0 | LLM 사용 여부 |

### 채널
- `ECON`: 경제 (활성)
- `POLICY`: 정책 (비활성)
- `SOCIETY`: 사회 (비활성)
- `WORLD`: 국제 (비활성)

---

## 2. 한국사 파이프라인 (HISTORY)

### 워크플로우
```
주제 선정 → 자료 수집 (한국민족문화대백과, e뮤지엄) → Opus 프롬프트 생성 → 시트 저장
```

### API
```bash
GET /api/history/run-pipeline
GET /api/history/run-pipeline?force=1
```

### 자동 보충
- 목표: '준비' 상태 **10개** 유지
- 부족 시 자동으로 다음 에피소드 추가

### 시대 구성
| 시대 | 에피소드 수 | 상태 |
|------|------------|------|
| 선사시대 | 3 | 활성 |
| 고조선~삼국통일 | 5 | 활성 |
| 통일신라~고려 | 5 | 활성 |
| 조선 전기 | 5 | 활성 |
| 조선 후기 | 5 | 활성 |
| 근대 | 5 | 활성 |
| 현대 | 4 | 활성 |
| **총계** | **32** | |

---

## 3. 미스테리 파이프라인 (MYSTERY)

### 해외 미스테리

**워크플로우**
```
영어 위키백과 수집 → 요약 추출 → Opus 프롬프트 생성 → 시트 저장
```

**API**
```bash
POST /api/mystery/run-pipeline
POST /api/mystery/run-pipeline?force=1
```

### 한국 미스테리 (2025-12-22 추가)

**워크플로우**
```
나무위키 문서 확인 → URL 생성 → Opus가 직접 읽음 → 시트 저장
```

**API**
```bash
POST /api/mystery/run-kr-pipeline
POST /api/mystery/run-kr-pipeline?force=1
POST /api/mystery/run-kr-pipeline?category=TOP3
```

### 자동 보충
- 목표: '준비' 상태 **5개** 유지
- 부족 시 자동으로 다음 미스테리 추가

### 한국 미스테리 카테고리

| 코드 | 이름 | 개수 | 설명 |
|------|------|------|------|
| `TOP3` | 3대 미제사건 | 3 | 개구리 소년, 이형호, 화성 |
| `MURDER` | 미해결 살인 | 10 | 범인 미검거 |
| `SUSPICIOUS_DEATH` | 의문사 | 6 | 사인 불명 |
| `MISSING` | 실종 | 8 | 미해결 실종 |
| `MASS_INCIDENT` | 집단 사건 | 3 | 집단 자살, 사이비 |
| `DISASTER` | 대형 참사 | 5 | 의혹 있는 사고 |
| `SERIAL` | 연쇄 살인 | 5 | 해결됨, 미스테리 요소 |
| `URBAN_LEGEND` | 도시전설 | 8 | 괴담, 미스테리 장소 |
| **총계** | | **48** | |

---

## 통합 시트 구조

### 시트 레이아웃

```
Google Sheets
├── NEWS        # 뉴스 통합
├── HISTORY     # 한국사 통합
└── MYSTERY     # 미스테리 통합 (해외+한국)
```

### 시트 헤더 (공통)

**행 1**: 채널 설정
| A1 | B1 |
|----|-----|
| 채널ID | UCxxxxxxxxxxxx |

**행 2**: 헤더
- 수집 영역 (자동 채워짐)
- 영상 자동화 영역 (상태, 대본, 제목 등)

**행 3~**: 데이터

---

## 중복 방지

### 해시 기반 중복 체크
- 해외 미스테리: `title_en` 해시
- 한국 미스테리: `title_ko` 해시
- 뉴스: 기사 URL 해시

### 시트 조회 방식
1. 시트에서 사용된 제목 목록 조회
2. 새 자료와 비교
3. 중복 시 스킵

---

## 로그 확인

### 서버 로그 태그
```
[NEWS]       - 뉴스 파이프라인
[HISTORY]    - 한국사 파이프라인
[MYSTERY]    - 해외 미스테리
[KR_MYSTERY] - 한국 미스테리
```

### 로그 예시
```
[KR_MYSTERY] ========================================
[KR_MYSTERY] 한국 미스테리 파이프라인 시작
[KR_MYSTERY] 현재 준비: 2개, 사용 가능: 48개
[KR_MYSTERY] 3개 추가 예정
[KR_MYSTERY] 나무위키 문서 확인: 개구리 소년 실종 사건
[KR_MYSTERY] 에피소드 1 → 'MYSTERY' 시트 저장 완료
[KR_MYSTERY] ========================================
[KR_MYSTERY] 완료: 3개 추가
[KR_MYSTERY] 준비: 2 → 5
[KR_MYSTERY] ========================================
```

---

## Cron 설정 예시

```bash
# 뉴스 (매일 오전 7시 KST)
0 22 * * * curl -X POST "https://your-domain/api/news/run-pipeline?channel=ECON"

# 한국사 (매일 오전 8시 KST)
0 23 * * * curl -X POST "https://your-domain/api/history/run-pipeline"

# 미스테리 (매주 월요일 오전 9시 KST)
0 0 * * 1 curl -X POST "https://your-domain/api/mystery/run-pipeline"

# 한국 미스테리 (매주 수요일 오전 9시 KST)
0 0 * * 3 curl -X POST "https://your-domain/api/mystery/run-kr-pipeline"
```

---

## 변경 이력

### 2025-12-22
- 한국 미스테리 파이프라인 추가 (48개 사건)
- "PENDING" → "준비"로 상태명 통일
- 파이프라인 가이드 문서 생성

### 2024-12
- 한국사 파이프라인 주제 기반 개편
- 통합 시트 구조 도입

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `drama_server.py` | 메인 서버 (API 엔드포인트) |
| `scripts/news_pipeline/` | 뉴스 파이프라인 |
| `scripts/history_pipeline/` | 한국사 파이프라인 |
| `scripts/mystery_pipeline/` | 미스테리 파이프라인 |
| `scripts/mystery_pipeline/KOREAN_MYSTERIES.md` | 한국 미스테리 48개 목록 |

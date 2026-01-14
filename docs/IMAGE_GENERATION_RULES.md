# 이미지 생성 규칙

## 이미지 노출 간격 (시간 기반)

| 시간 구간 | 간격 | 이유 | 예상 개수 |
|-----------|------|------|-----------|
| 0초 ~ 1분 | 10초마다 | 초반 이탈 방지 | 6장 |
| 1분 ~ 5분 | 30초마다 | 흥미 유지 | 8장 |
| 5분 ~ 10분 | 40초마다 | 안정적 시청 | 7-8장 |
| 10분 ~ 끝 | 60초마다 | 몰입 상태 | 분당 1장 |

### 영상 길이별 예상 이미지 개수

| 영상 길이 | 이미지 개수 |
|-----------|-------------|
| 5분 | ~14장 |
| 10분 | ~19장 |
| 15분 | ~24장 |
| 20분 | ~31장 |

---

## 스타일 일관성 규칙

### 공통 스타일 프리픽스 (style_prefix)

모든 씬 이미지에 동일한 스타일 프리픽스를 적용하여 일관성 유지:

```
Korean webtoon style meets Studio Ghibli and modern flat illustration,
clean line art with soft warm lighting,
vibrant yet gentle colors,
cel shading with subtle gradients,
dynamic composition but peaceful atmosphere,
hand-painted feel with clean aesthetic,
accessible and friendly,
bright warm palette,
16:9 aspect ratio.
```

**스타일 특징:**
- 웹툰: 깔끔한 선, 생동감
- 지브리: 따뜻함, 평화로운 분위기
- 모던 일러스트: 심플, 접근성

### 프롬프트 구조

```
[스타일 프리픽스] + [씬별 프롬프트]
```

씬별 프롬프트 포함 요소:
1. **Shot type**: establishing_shot, dramatic_scene, character_group, action_scene, close_up
2. **Subject**: 누가/무엇이 있는지
3. **Action**: 무엇을 하고 있는지
4. **Environment**: 배경, 장소
5. **Lighting**: 조명 상태
6. **Mood**: 분위기

---

## 이미지 타입별 가이드

| 타입 | 용도 | 예시 |
|------|------|------|
| establishing_shot | 장소/시대 소개 | 산 위의 장군, 성곽 전경 |
| dramatic_scene | 긴장감 있는 장면 | 폭군의 옥좌, 전투 직전 |
| character_group | 여러 인물 등장 | 밀담, 회의, 대치 |
| action_scene | 동적인 장면 | 전투, 추격, 탈출 |
| close_up | 감정 표현 | 결의에 찬 표정, 눈물 |
| landscape | 분위기 전환 | 계절 변화, 시간 경과 |

---

## 모델 선택 기준

| 용도 | 모델 | 비용 | 비고 |
|------|------|------|------|
| 씬 이미지 | Gemini 2.5 Flash | $0.001/장 | 저렴, 1024x1024→16:9 크롭 |
| 썸네일 배경 | Gemini 2.5 Flash | $0.001/장 | 배경만 생성, PIL로 텍스트 합성 |

---

## 썸네일 텍스트 스타일 B (호기심형) - 현재 사용

조회수가 잘 나온 스타일 분석 결과:

```python
# 폰트
FONT_PATH = "assets/fonts/black_han_sans.ttf"

# 색상
TITLE_COLOR = (255, 255, 255)      # 흰색
STROKE_COLOR = (0, 0, 0)           # 검정 테두리
SUBTITLE_COLOR = (255, 220, 80)    # 노란색/금색

# 크기 (이미지 높이 기준 비율)
title_size = 0.17
subtitle_size = 0.07

# 위치
title_x = width * 0.04             # 왼쪽 여백
title_y = height * 0.08            # 상단 여백
title_line_gap = height * 0.05     # 제목 줄간격
subtitle_gap = height * 0.04       # 제목-부제 간격

# 테두리(stroke) 두께
title_stroke = 12
subtitle_stroke = 7
```

### 제목 자동 줄나눔 규칙

| 조건 | 줄 수 | 예시 |
|------|-------|------|
| 글자 수 ≤ 6자 | 1줄 | "삼국통일" |
| 글자 수 7~10자 | 2줄 | "발해 / 고구려를 잇다" |
| 글자 수 ≥ 11자 | 3줄 | "후삼국 / 셋으로 / 갈라지다" |

### 배경 이미지 프롬프트 규칙

```
Korean webtoon style illustration for YouTube thumbnail, 16:9 aspect ratio.
Scene: [씬 설명]
Background: [배경 설명]
Character on right side of image, left side should have space for text overlay.
Style: Clean line art, warm colors, Studio Ghibli meets modern illustration, friendly and accessible.
Character should have [표정] expression.
```

### 구현 스크립트

`scripts/history_pipeline/generate_thumbnails_v2.py`

---

## 썸네일 텍스트 스타일 A (뱃지형) - 이전 버전

```python
# 폰트
title_font = "assets/fonts/black_han_sans.ttf"  # BlackHanSans
subtitle_font = "assets/fonts/black_han_sans.ttf"

# 색상
title_color = (255, 180, 50)   # 오렌지 (CTR 최적화)
subtitle_color = (255, 255, 255)  # 흰색

# 크기 (이미지 높이 기준 비율)
title_size = 0.14   # Large
subtitle_size = 0.07

# 위치
title_gap = 0.06    # 제목-부제 간격 (XLarge)
y_offset = 0.05     # 전체 위로 이동량

# 뱃지
badge_scale = 0.065  # 뱃지 폰트 크기 (XLarge)
badge_color = (220, 40, 40)  # 빨간색
```

---

## 구현 위치

- 타임스탬프 계산: `scripts/history_pipeline/image_agent.py:696`
- 이미지 생성: `image/gemini.py`
- 스타일 프리픽스: `outputs/workspace/current_script.json` 의 `style_prefix` 필드

---

## 대본 작성 시 씬 구분 기준

대본 작성 시 위 간격 규칙에 맞춰 씬을 나눔:

```python
# 10분 영상 예시
scenes = [
    # 0~1분: 10초 간격 (6장)
    {"time": "0:00", "part": "intro"},
    {"time": "0:10", "part": "intro"},
    {"time": "0:20", "part": "intro"},
    {"time": "0:30", "part": "intro"},
    {"time": "0:40", "part": "intro"},
    {"time": "0:50", "part": "intro"},

    # 1~5분: 30초 간격 (8장)
    {"time": "1:00", "part": "body1"},
    {"time": "1:30", "part": "body1"},
    # ...

    # 5~10분: 40초 간격 (7-8장)
    {"time": "5:00", "part": "body2"},
    {"time": "5:40", "part": "body2"},
    # ...
]
```

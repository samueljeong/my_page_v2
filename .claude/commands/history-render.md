# 한국사 영상 렌더링

대본이 완성된 에피소드의 TTS, 이미지, 영상을 생성합니다.

## 사용법

```
/history-render [에피소드ID]
```

예시: `/history-render ep021`

## 실행 흐름

1. **대본 로드**: `scripts/history_pipeline/episodes/ep{ID}_*.py`
2. **TTS 생성**: 실제 오디오 길이 확인
3. **이미지 프롬프트 생성**: TTS 길이 기반 타임스탬프 자동 계산
4. **이미지 생성**: Gemini Flash (OpenRouter fallback)
5. **영상 렌더링**: FFmpeg (BGM 10%, TTS 100%)
6. **상태 업데이트**: `outputs/history/status/ep{ID}_status.json`

## 이미지 타임스탬프 규칙

TTS 실제 길이를 기준으로 자동 계산:

| 시간 구간 | 간격 | 예상 개수 |
|-----------|------|-----------|
| 0~1분 | 10초 | 6장 |
| 1~5분 | 30초 | 8장 |
| 5~10분 | 40초 | 8장 |
| 10분~끝 | 60초 | 분당 1장 |

## 실행 명령

```python
from scripts.history_pipeline.render_skill import render_episode
result = render_episode("$ARGUMENTS")
```

## 예상 시간

- 20분 영상: ~15분 소요 (이미지 32장 기준)

## 주의사항

- 대본 파일이 먼저 존재해야 함
- Google API quota 초과 시 OpenRouter fallback
- 기존 TTS가 있으면 재사용 (skip_tts=True)

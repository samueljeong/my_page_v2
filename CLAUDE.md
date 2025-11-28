# Drama Page 재구축 프로젝트

## 현재 브랜치
`claude/rebuild-drama-page-011hvTqaGHPCZynphV3U7BJG`

## 프로젝트 개요
Drama Lab - AI 기반 드라마 영상 자동 생성 시스템

## 작업 진행 상황

### 완료된 작업 (백엔드 파이프라인)
- [x] Step1: 공식 스펙 확정 - 스키마 및 프롬프트
- [x] Step2: 이미지 생성 스펙 및 뼈대 코드
- [x] Step3: TTS & 자막 생성 모듈 구축
- [x] Step4: 영상 조립 모듈 구축
- [x] Step5: YouTube 업로드 자동화 모듈 구축
- [x] 전체 파이프라인 통합 컨트롤러 구현

### 진행 중인 작업 (프론트엔드 UI)
- [ ] drama.html UI 재구축 필요 (현재 "페이지 재구축 중..." 상태)
- [ ] drama-main.js 메인 로직 구현
- [ ] drama-step1~5.js 각 스텝별 UI 구현
- [ ] drama.css 스타일 완성

## 파일 구조

### 백엔드
- `drama_server.py` (6241줄) - 메인 서버, 모든 API 엔드포인트 포함

### 프론트엔드
- `templates/drama.html` - 메인 템플릿 (재구축 필요)
- `static/css/drama.css` - 스타일시트
- `static/js/drama-main.js` - 메인 모듈
- `static/js/drama-step1.js` ~ `drama-step5.js` - 각 스텝별 모듈
- `static/js/drama-utils.js` - 유틸리티 함수
- `static/js/drama-session.js` - 세션 관리

### 가이드/설정
- `guides/drama.json` - 드라마 설정
- `guides/nostalgia-drama-prompts.json` - 향수 드라마 프롬프트
- `guides/nostalgia-drama-sample.json` - 샘플 데이터

## 알려진 이슈 (drama_issue_code.md 참조)

### 1. TTS 음성 생성 오류
- Google TTS API 5000바이트 제한 초과 문제
- SSML 태그 추가 시 바이트 제한 초과 가능성
- `max_bytes = 3500` 설정했으나 여전히 발생

### 2. 한국인 이미지 생성 문제
- 한국 할머니/할아버지 생성 시 외국인 이미지 출력
- 프롬프트에 "Korean ethnicity", "East Asian features" 명시해도 불완전

## 주요 API 엔드포인트 (drama_server.py)
- `/api/drama/generate-tts` - TTS 음성 생성 (라인 2913-3160)
- `/api/drama/analyze-characters` - 캐릭터 분석 (라인 2368-2452)
- `/api/drama/generate-image` - 이미지 생성 (라인 2556-2909)

## 다음 세션에서 할 일
1. drama.html UI 완성 (Step1~5 화면 구현)
2. 각 step별 JS 모듈 구현
3. TTS/이미지 생성 이슈 해결

## 참고 사항
- 이미지 생성: Gemini (기본) / FLUX.1 Pro / DALL-E 3 지원
- TTS: Google Cloud TTS (기본) / 네이버 클로바 지원
- 백엔드 파이프라인은 완성 상태, 프론트엔드 UI만 재구축 필요

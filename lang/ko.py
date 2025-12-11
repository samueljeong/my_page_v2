# -*- coding: utf-8 -*-
"""
한국어 설정 파일

현재 drama_server.py에 흩어져 있는 한국어 관련 설정을 모아둠.
TODO: drama_server.py에서 이 파일의 설정을 import하도록 변경 필요

참고: 아래 라인 번호는 현재 drama_server.py 기준이며, 추후 리팩토링 시 참고용
"""

# =============================================================================
# 언어 기본 정보
# =============================================================================
LANG_CODE = 'ko'
LANG_NAME = 'Korean'
LANG_NATIVE = '한국어'

# 언어 감지 패턴 (유니코드 범위)
# 사용처: drama_server.py 11204행, 12849행, 18794행, 21216행
DETECTION_PATTERN = r'[가-힣]'  # 한글 완성형


# =============================================================================
# 폰트 설정
# =============================================================================
# 사용처: drama_server.py 6664-6667행, 7994-7998행, 8757-8762행, 14079행,
#        14209행, 14311행, 14949-14953행, 15449행, 15789행, 17731-17732행

# 폰트 우선순위 (첫 번째 폰트부터 시도)
FONTS = [
    'NanumGothicBold.ttf',      # 나눔고딕 볼드 (기본)
    'NanumGothic.ttf',          # 나눔고딕
    'NanumSquareRoundB.ttf',    # 나눔스퀘어라운드 볼드
    'NanumBarunGothicBold.ttf', # 나눔바른고딕 볼드
]

# 시스템 폰트 경로 (fonts/ 폴더에 없을 때 폴백)
SYSTEM_FONT_PATHS = [
    '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
]

# ASS 자막용 폰트 이름 (경로가 아닌 폰트 이름)
# 사용처: drama_server.py 6677행, 13843행
ASS_FONT_NAME = 'NanumSquareRound'  # 자막용 (둥근 고딕, 가독성 좋음)


# =============================================================================
# 자막 설정
# =============================================================================
# ★★★ 핵심 설정: 자막이 너무 길게 나오는 문제의 원인 ★★★
# 사용처: drama_server.py 13365행, 13419행

# 자막 한 줄 최대 글자 수
# 현재값: 120 (너무 김! 5줄이나 나옴)
# 권장값: 20~25 (유튜브 자막 권장)
SUBTITLE_MAX_CHARS_PER_LINE = 20  # TODO: 현재 drama_server.py는 120 사용 중

# 자막 최대 줄 수
SUBTITLE_MAX_LINES = 2

# 자막 총 최대 글자 수 (SUBTITLE_MAX_CHARS_PER_LINE * SUBTITLE_MAX_LINES)
SUBTITLE_MAX_CHARS = SUBTITLE_MAX_CHARS_PER_LINE * SUBTITLE_MAX_LINES  # = 40

# ASS 자막 스타일
# 사용처: drama_server.py 13840-13846행
ASS_SUBTITLE_STYLE = {
    'font_name': 'NanumSquareRound',
    'font_size': 28,
    'primary_color': '&H00FFFF',      # 노란색 (BGR)
    'outline_color': '&H00000000',    # 검은색 테두리
    'back_color': '&H80000000',       # 반투명 검은 배경
    'border_style': 1,                # 테두리 + 그림자
    'outline': 4,                     # 테두리 두께
    'shadow': 2,                      # 그림자
    'margin_v': 40,                   # 하단 여백
    'bold': 1,                        # 볼드
}

# ASS 스타일 문자열 (FFmpeg에서 직접 사용)
def get_ass_style_string():
    s = ASS_SUBTITLE_STYLE
    return (
        f"FontName={s['font_name']},FontSize={s['font_size']},"
        f"PrimaryColour={s['primary_color']},"
        f"OutlineColour={s['outline_color']},BackColour={s['back_color']},"
        f"BorderStyle={s['border_style']},Outline={s['outline']},"
        f"Shadow={s['shadow']},MarginV={s['margin_v']},Bold={s['bold']}"
    )


# =============================================================================
# TTS 음성 설정
# =============================================================================
# 사용처: drama_server.py 4557행, 4933행, 12863행, 13279행, 17169행, 21098행, 22128행

# 기본 TTS 음성
TTS_VOICE_DEFAULT = 'ko-KR-Neural2-C'  # 남성 (고품질)

# 성별별 TTS 음성
TTS_VOICES = {
    'male': 'ko-KR-Neural2-C',    # 남성
    'female': 'ko-KR-Neural2-A',  # 여성
}

# 대체 음성 (Neural2 사용 불가 시)
TTS_VOICE_FALLBACK = 'ko-KR-Wavenet-A'

# TTS 설정
TTS_CONFIG = {
    'language_code': 'ko-KR',
    'speaking_rate': 0.9,  # 약간 느리게 (시니어 타겟)
}


# =============================================================================
# 유튜브 메타데이터 설정
# =============================================================================
# 사용처: drama_server.py 11688행

# 제목 길이
YOUTUBE_TITLE_MIN_LENGTH = 18  # 최소
YOUTUBE_TITLE_MAX_LENGTH = 32  # 최대 (공백 포함)

# 설명 길이
YOUTUBE_DESCRIPTION_MIN_LENGTH = 600   # 최소 글자
YOUTUBE_DESCRIPTION_MAX_LENGTH = 1200  # 최대 글자


# =============================================================================
# 썸네일 텍스트 설정
# =============================================================================
# 사용처: drama_server.py 11604행, 12071행, 12075행

# 메인 텍스트 (큰 글씨)
THUMBNAIL_MAIN_TEXT_MAX = 6  # 최대 6자

# 서브 텍스트 (작은 글씨)
THUMBNAIL_SUB_TEXT_MAX = 15  # 최대 15자


# =============================================================================
# 문장 분할 설정
# =============================================================================
# 사용처: drama_server.py 5027-5053행

# 한국어 문장 종료 패턴
SENTENCE_END_PATTERNS = [
    '다.', '요.', '죠.', '네요.', '니다.', '까요?', '나요?',
    '!', '?', '...'
]

# 문장 분할 포인트 (자막용)
SENTENCE_SPLIT_PATTERNS = [
    ',',    # 쉼표
    '~고',  # 연결어미
    '~며',
    '~면',
    '~서',
    '~니',
    '~는데',
]


# =============================================================================
# 이미지 프롬프트 설정 (추후 확장)
# =============================================================================
# 사용처: drama_server.py 3574-3595행, 4323-4326행, 11517행

# 한국인 인물 프롬프트 프리픽스
PERSON_PROMPT_PREFIX = (
    "Korean person from South Korea with authentic Korean/East Asian ethnicity, "
    "Korean facial bone structure, Korean skin tone"
)

# 한국 배경 키워드
BACKGROUND_KEYWORDS = [
    'Korean cafe', 'Korean apartment', 'Korean restaurant',
    'Korean street', 'Korean countryside'
]

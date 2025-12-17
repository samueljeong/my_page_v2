"""
한국사 자동화 파이프라인 설정

시대 흐름형 시리즈를 위한 설정 파일
- 고조선부터 대한제국까지 시대별 트랙 정의
- 각 시대별 수집 키워드 관리
- 시트 구조 및 제한 설정
"""

from typing import Dict, List, Any


# ============================================================
# 시대 트랙 설정 (순서 고정)
# ============================================================

# 시대 순서 (영문 키 사용)
ERA_ORDER: List[str] = [
    "GOJOSEON",      # 고조선
    "BUYEO",         # 부여/옥저/동예
    "SAMGUK",        # 삼국시대
    "NAMBUK",        # 남북국시대
    "GORYEO",        # 고려
    "JOSEON_EARLY",  # 조선 전기
    "JOSEON_LATE",   # 조선 후기
    "DAEHAN",        # 대한제국
]

# 시대 메타데이터
ERAS: Dict[str, Dict[str, Any]] = {
    "GOJOSEON": {
        "name": "고조선",
        "name_en": "Gojoseon",
        "period": "BC 2333 ~ BC 108",
        "description": "한반도 최초의 국가, 단군조선과 위만조선",
        "active": True,  # 첫 번째 시대부터 시작
    },
    "BUYEO": {
        "name": "부여/옥저/동예",
        "name_en": "Buyeo Period",
        "period": "BC 2세기 ~ AD 494",
        "description": "고조선 멸망 후 등장한 여러 나라",
        "active": False,
    },
    "SAMGUK": {
        "name": "삼국시대",
        "name_en": "Three Kingdoms",
        "period": "BC 57 ~ AD 668",
        "description": "고구려, 백제, 신라의 경쟁과 발전",
        "active": False,
    },
    "NAMBUK": {
        "name": "남북국시대",
        "name_en": "North-South States",
        "period": "AD 698 ~ AD 926",
        "description": "통일신라와 발해의 병존",
        "active": False,
    },
    "GORYEO": {
        "name": "고려",
        "name_en": "Goryeo Dynasty",
        "period": "AD 918 ~ AD 1392",
        "description": "왕건의 건국부터 조선 건국까지",
        "active": False,
    },
    "JOSEON_EARLY": {
        "name": "조선 전기",
        "name_en": "Early Joseon",
        "period": "AD 1392 ~ AD 1592",
        "description": "조선 건국부터 임진왜란 이전",
        "active": False,
    },
    "JOSEON_LATE": {
        "name": "조선 후기",
        "name_en": "Late Joseon",
        "period": "AD 1592 ~ AD 1897",
        "description": "임진왜란 이후부터 대한제국 선포 이전",
        "active": False,
    },
    "DAEHAN": {
        "name": "대한제국",
        "name_en": "Korean Empire",
        "period": "AD 1897 ~ AD 1910",
        "description": "근대화 시도와 국권 상실",
        "active": False,
    },
}


# ============================================================
# 시대별 수집 키워드
# ============================================================

ERA_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "GOJOSEON": {
        "primary": [
            "고조선", "단군", "단군왕검", "아사달", "위만조선", "위만",
            "기자조선", "조선", "요동", "왕검성", "고조선 멸망",
        ],
        "secondary": [
            "청동기", "비파형동검", "고인돌", "미송리식토기",
            "한사군", "낙랑군", "8조법", "팔조법금",
        ],
        "exclude": [
            "북한", "김정은", "조선일보", "조선시대",  # 현대 조선 관련 제외
        ],
    },
    "BUYEO": {
        "primary": [
            "부여", "동부여", "북부여", "옥저", "동예", "삼한",
            "마한", "진한", "변한", "예맥", "영고", "동맹", "무천",
        ],
        "secondary": [
            "철기문화", "순장", "형사취수", "1책12법", "제천행사",
            "소도", "천군", "별읍",
        ],
        "exclude": [],
    },
    "SAMGUK": {
        "primary": [
            "고구려", "백제", "신라", "가야", "삼국시대",
            "광개토대왕", "장수왕", "근초고왕", "진흥왕", "법흥왕",
            "을지문덕", "살수대첩", "계백", "김유신", "연개소문",
        ],
        "secondary": [
            "불교 수용", "삼국사기", "삼국유사", "고분벽화",
            "첨성대", "황룡사", "무령왕릉", "호우명그릇",
            "나제동맹", "삼국통일", "당나라",
        ],
        "exclude": [],
    },
    "NAMBUK": {
        "primary": [
            "통일신라", "발해", "남북국", "대조영", "무왕", "문왕",
            "원성왕", "신문왕", "경덕왕", "해동성국",
        ],
        "secondary": [
            "9주5소경", "골품제", "선종", "화엄종", "석굴암", "불국사",
            "장보고", "청해진", "호족", "6두품", "정혜쌍수",
        ],
        "exclude": [],
    },
    "GORYEO": {
        "primary": [
            "고려", "왕건", "광종", "성종", "현종", "문종",
            "공민왕", "무신정권", "최충헌", "삼별초",
            "몽골침입", "원간섭기", "권문세족",
        ],
        "secondary": [
            "과거제도", "팔만대장경", "직지심체요절", "고려청자",
            "상감청자", "개경", "벽란도", "대몽항쟁",
            "삼국사기", "삼국유사", "묘청의 난",
        ],
        "exclude": [],
    },
    "JOSEON_EARLY": {
        "primary": [
            "조선 건국", "이성계", "태조", "태종", "세종대왕",
            "세조", "성종", "연산군", "중종", "명종",
            "훈민정음", "집현전", "경국대전",
        ],
        "secondary": [
            "사림", "훈구", "사화", "무오사화", "갑자사화", "기묘사화",
            "을사사화", "향약", "서원", "성리학", "조광조",
            "경복궁", "창덕궁", "한양",
        ],
        "exclude": [],
    },
    "JOSEON_LATE": {
        "primary": [
            "임진왜란", "정유재란", "병자호란", "인조반정",
            "영조", "정조", "실학", "정약용", "김정희",
            "세도정치", "흥선대원군", "개화", "강화도조약",
        ],
        "secondary": [
            "이순신", "거북선", "한산도대첩", "명량해전",
            "탕평책", "규장각", "수원화성", "천주교 박해",
            "동학", "갑오개혁", "을미사변",
        ],
        "exclude": [],
    },
    "DAEHAN": {
        "primary": [
            "대한제국", "광무개혁", "고종", "순종",
            "을사조약", "헤이그 특사", "군대 해산",
            "안중근", "의병", "국권피탈", "경술국치",
        ],
        "secondary": [
            "독립협회", "만민공동회", "대한매일신보", "황성신문",
            "신민회", "애국계몽운동", "근대화", "철도", "전기",
            "이토 히로부미", "통감부", "일제강점",
        ],
        "exclude": [],
    },
}


# ============================================================
# 수집 소스 설정 (뉴스가 아닌 전문 자료)
# ============================================================

SOURCE_TYPES = {
    "university": {
        "name": "대학 연구",
        "weight": 2.0,  # 신뢰도 가중치
    },
    "museum": {
        "name": "박물관/문화재청",
        "weight": 2.0,
    },
    "journal": {
        "name": "학술지/논문",
        "weight": 1.8,
    },
    "long_form": {
        "name": "전문 칼럼/분석",
        "weight": 1.5,
    },
    "encyclopedia": {
        "name": "백과사전/위키",
        "weight": 1.0,
    },
}

# 검색 쿼리 템플릿 (Google Custom Search용)
SEARCH_QUERY_TEMPLATES = [
    "{era_name} 역사",
    "{era_name} 연구",
    "{era_name} 유물 발굴",
    "{era_name} 문화재",
    "{keyword} 역사적 의의",
    "{keyword} 연구 논문",
]


# ============================================================
# Google Sheets 시트 구조
# ============================================================

# 시트 접두사 (시대 키와 조합)
SHEET_PREFIXES = {
    "RAW": "원문 수집 데이터",
    "CANDIDATES": "점수화된 후보",
    "OPUS_INPUT": "대본 작성용 입력",
    "ARCHIVE": "아카이브",
}

# 각 시트의 헤더 정의
SHEET_HEADERS = {
    "RAW": [
        "collected_at",      # 수집 시간 (ISO)
        "era",               # 시대 키
        "source_type",       # university/museum/journal/long_form
        "source_name",       # 출처명
        "title",             # 자료 제목
        "url",               # URL
        "content_summary",   # 내용 요약
        "keywords",          # 감지된 키워드
        "hash",              # 중복 방지용 해시
    ],
    "CANDIDATES": [
        "run_id",            # 실행 날짜 (YYYY-MM-DD)
        "rank",              # 순위
        "era",               # 시대
        "topic",             # 주제 분류
        "score_total",       # 총점
        "score_relevance",   # 관련도
        "score_quality",     # 자료 품질
        "score_freshness",   # 신선도 (발굴/연구 최신성)
        "title",             # 제목
        "url",               # URL
        "summary",           # 요약
        "why_selected",      # 선정 근거
    ],
    "OPUS_INPUT": [
        "run_id",            # 실행 날짜
        "selected_rank",     # 선정 순위
        "era",               # 시대
        "topic",             # 주제
        "core_facts",        # 핵심 사실 (LLM 생성)
        "narrative_arc",     # 스토리 아크 제안
        "script_brief",      # 대본 지시문
        "thumbnail_ideas",   # 썸네일 문구 아이디어
        "status",            # NEW/WRITING/DONE
        "opus_script",       # 완성 대본 (사람 입력)
    ],
}


# ============================================================
# 시트 제한 설정
# ============================================================

# 시트 행 제한
MAX_ROWS_PER_SHEET = 3000

# 아카이브 트리거 (이 비율 초과 시 아카이브)
ARCHIVE_THRESHOLD_RATIO = 0.9  # 90% = 2700행

# 아카이브 시 유지할 최신 행 수
ROWS_TO_KEEP_AFTER_ARCHIVE = 500


# ============================================================
# 점수화 설정
# ============================================================

# 관련도 점수 가중치
RELEVANCE_WEIGHTS = {
    "primary_keyword_in_title": 5,   # 제목에 주요 키워드
    "primary_keyword_in_content": 2, # 내용에 주요 키워드
    "secondary_keyword": 1,          # 보조 키워드
}

# 자료 품질 점수
QUALITY_WEIGHTS = {
    "university": 10,
    "museum": 10,
    "journal": 8,
    "long_form": 5,
    "encyclopedia": 3,
}

# TOP K 선정 수
DEFAULT_TOP_K = 5


# ============================================================
# LLM 설정
# ============================================================

# LLM 사용 여부 (환경변수로 오버라이드 가능)
LLM_ENABLED_DEFAULT = False

# LLM 호출 최소 점수 (비용 절감)
LLM_MIN_SCORE_DEFAULT = 0

# 기본 모델
LLM_MODEL_DEFAULT = "gpt-4o-mini"


# ============================================================
# 한국사 전용 대본 지시문 템플릿
# ============================================================

SCRIPT_BRIEF_TEMPLATE = """[대본 지시문]
- 시대: {era_name} ({period})
- 분량: 8~12분 (3,500~4,500자)
- 관점: 시청자가 "왜 이 시대가 중요한가"를 체감하도록
- 구조:
  1. 오프닝: 시대적 배경 + 핵심 질문 던지기
  2. 본론: 핵심 사실 3~5개를 스토리로 연결
  3. 의의: 이 시대가 이후 역사에 미친 영향
  4. 클로징: 다음 시대로의 연결고리

[금지]
- 연도/사건 나열식 설명
- 교과서 문체
- 지나친 민족주의 표현

[권장]
- 인물 중심 스토리텔링
- "만약 ~했다면?" 가정법 활용
- 현대와의 연결점 제시
"""


# ============================================================
# 유틸리티 함수
# ============================================================

def get_era_sheet_name(prefix: str, era: str) -> str:
    """시대별 시트 이름 생성"""
    return f"{era}_{prefix}"


def get_archive_sheet_name(era: str, year: int) -> str:
    """아카이브 시트 이름 생성"""
    return f"{era}_ARCHIVE_{year}"


def get_active_eras() -> List[str]:
    """활성화된 시대 목록 반환"""
    return [era for era in ERA_ORDER if ERAS.get(era, {}).get("active", False)]


def get_era_keywords(era: str) -> Dict[str, List[str]]:
    """시대별 키워드 반환"""
    return ERA_KEYWORDS.get(era, {"primary": [], "secondary": [], "exclude": []})

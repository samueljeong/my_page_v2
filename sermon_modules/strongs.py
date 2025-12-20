"""
strongs.py
Strong's Concordance 원어 분석 모듈

기능:
- 성경 구절에서 Strong's 번호 추출
- Strong's 번호로 헬라어/히브리어 원어 정의 조회
- 한글 성경 책 이름 → 영문 약어 변환
"""

import os
import re
import json
import urllib.request
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

# 데이터 경로
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'strongs')

# GitHub 원본 데이터 URL
GITHUB_URLS = {
    'lexicon.json': 'https://raw.githubusercontent.com/kaiserlik/kjv/master/lexicon.json',
    'books.json': 'https://raw.githubusercontent.com/kaiserlik/kjv/master/books.json',
}


def _ensure_data_dir():
    """데이터 디렉토리 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"[STRONGS] Created data directory: {DATA_DIR}")


def _download_file(filename: str, url: str) -> bool:
    """GitHub에서 파일 다운로드"""
    try:
        _ensure_data_dir()
        filepath = os.path.join(DATA_DIR, filename)
        print(f"[STRONGS] Downloading {filename}...")
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            with open(filepath, 'wb') as f:
                f.write(data)
        print(f"[STRONGS] Downloaded {filename} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"[STRONGS] Download failed for {filename}: {e}")
        return False


def _download_and_convert_strongs(lang: str) -> bool:
    """Strong's 사전 다운로드 및 JSON 변환 (Greek/Hebrew)"""
    try:
        _ensure_data_dir()

        if lang == 'greek':
            url = 'https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongs-greek-dictionary.js'
            output_file = 'greek_dictionary.json'
            marker = 'var strongsGreekDictionary = '
        else:
            url = 'https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.js'
            output_file = 'hebrew_dictionary.json'
            marker = 'var strongsHebrewDictionary = '

        print(f"[STRONGS] Downloading {lang} dictionary...")
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')

        # JS → JSON 변환
        start_idx = content.find(marker)
        if start_idx == -1:
            print(f"[STRONGS] Marker not found in {lang} dictionary")
            return False

        json_start = start_idx + len(marker)
        end_idx = content.rfind('};')
        if end_idx == -1:
            print(f"[STRONGS] End marker not found in {lang} dictionary")
            return False

        json_str = content[json_start:end_idx + 1]
        data = json.loads(json_str)

        filepath = os.path.join(DATA_DIR, output_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

        print(f"[STRONGS] Converted {lang} dictionary: {len(data)} entries")
        return True
    except Exception as e:
        print(f"[STRONGS] Failed to download/convert {lang} dictionary: {e}")
        return False

# 한글 책 이름 → 영문 약어 매핑
BOOK_NAME_MAP = {
    # 구약
    '창세기': 'Gen', '창': 'Gen',
    '출애굽기': 'Exo', '출': 'Exo',
    '레위기': 'Lev', '레': 'Lev',
    '민수기': 'Num', '민': 'Num',
    '신명기': 'Deu', '신': 'Deu',
    '여호수아': 'Jos', '수': 'Jos',
    '사사기': 'Jdg', '삿': 'Jdg',
    '룻기': 'Rth', '룻': 'Rth',
    '사무엘상': '1Sa', '삼상': '1Sa',
    '사무엘하': '2Sa', '삼하': '2Sa',
    '열왕기상': '1Ki', '왕상': '1Ki',
    '열왕기하': '2Ki', '왕하': '2Ki',
    '역대상': '1Ch', '대상': '1Ch',
    '역대하': '2Ch', '대하': '2Ch',
    '에스라': 'Ezr', '스': 'Ezr',
    '느헤미야': 'Neh', '느': 'Neh',
    '에스더': 'Est', '에': 'Est',
    '욥기': 'Job', '욥': 'Job',
    '시편': 'Psa', '시': 'Psa',
    '잠언': 'Pro', '잠': 'Pro',
    '전도서': 'Ecc', '전': 'Ecc',
    '아가': 'Sng', '아': 'Sng',
    '이사야': 'Isa', '사': 'Isa',
    '예레미야': 'Jer', '렘': 'Jer',
    '예레미야애가': 'Lam', '애가': 'Lam', '애': 'Lam',
    '에스겔': 'Eze', '겔': 'Eze',
    '다니엘': 'Dan', '단': 'Dan',
    '호세아': 'Hos', '호': 'Hos',
    '요엘': 'Joe', '욜': 'Joe',
    '아모스': 'Amo', '암': 'Amo',
    '오바댜': 'Oba', '옵': 'Oba',
    '요나': 'Jon', '욘': 'Jon',
    '미가': 'Mic', '미': 'Mic',
    '나훔': 'Nah', '나': 'Nah',
    '하박국': 'Hab', '합': 'Hab',
    '스바냐': 'Zep', '습': 'Zep',
    '학개': 'Hag', '학': 'Hag',
    '스가랴': 'Zec', '슥': 'Zec',
    '말라기': 'Mal', '말': 'Mal',

    # 신약
    '마태복음': 'Mat', '마': 'Mat',
    '마가복음': 'Mar', '막': 'Mar',
    '누가복음': 'Luk', '눅': 'Luk',
    '요한복음': 'Jhn', '요': 'Jhn',
    '사도행전': 'Act', '행': 'Act',
    '로마서': 'Rom', '롬': 'Rom',
    '고린도전서': '1Co', '고전': '1Co',
    '고린도후서': '2Co', '고후': '2Co',
    '갈라디아서': 'Gal', '갈': 'Gal',
    '에베소서': 'Eph', '엡': 'Eph',
    '빌립보서': 'Phl', '빌': 'Phl',
    '골로새서': 'Col', '골': 'Col',
    '데살로니가전서': '1Th', '살전': '1Th',
    '데살로니가후서': '2Th', '살후': '2Th',
    '디모데전서': '1Ti', '딤전': '1Ti',
    '디모데후서': '2Ti', '딤후': '2Ti',
    '디도서': 'Tit', '딛': 'Tit',
    '빌레몬서': 'Phm', '몬': 'Phm',
    '히브리서': 'Heb', '히': 'Heb',
    '야고보서': 'Jas', '약': 'Jas',
    '베드로전서': '1Pe', '벧전': '1Pe',
    '베드로후서': '2Pe', '벧후': '2Pe',
    '요한1서': '1Jo', '요일': '1Jo', '요한일서': '1Jo',
    '요한2서': '2Jo', '요이': '2Jo', '요한이서': '2Jo',
    '요한3서': '3Jo', '요삼': '3Jo', '요한삼서': '3Jo',
    '유다서': 'Jde', '유': 'Jde',
    '요한계시록': 'Rev', '계': 'Rev',
}

# 신약 책 목록 (헬라어 사용)
NT_BOOKS = {
    'Mat', 'Mar', 'Luk', 'Jhn', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph',
    'Phl', 'Col', '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas',
    '1Pe', '2Pe', '1Jo', '2Jo', '3Jo', 'Jde', 'Rev'
}


class StrongsLookup:
    """Strong's Concordance 조회 클래스"""

    def __init__(self):
        self._greek_dict: Optional[Dict] = None
        self._hebrew_dict: Optional[Dict] = None
        self._lexicon: Optional[Dict] = None
        self._kjv_cache: Dict[str, Dict] = {}

    @property
    def greek_dict(self) -> Dict:
        """헬라어 사전 (lazy loading, 자동 다운로드)"""
        if self._greek_dict is None:
            path = os.path.join(DATA_DIR, 'greek_dictionary.json')
            if not os.path.exists(path):
                # 자동 다운로드 시도
                _download_and_convert_strongs('greek')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self._greek_dict = json.load(f)
                print(f"[STRONGS] Greek dictionary loaded: {len(self._greek_dict)} entries")
            else:
                print(f"[STRONGS] Greek dictionary not available")
                self._greek_dict = {}
        return self._greek_dict

    @property
    def hebrew_dict(self) -> Dict:
        """히브리어 사전 (lazy loading, 자동 다운로드)"""
        if self._hebrew_dict is None:
            path = os.path.join(DATA_DIR, 'hebrew_dictionary.json')
            if not os.path.exists(path):
                # 자동 다운로드 시도
                _download_and_convert_strongs('hebrew')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self._hebrew_dict = json.load(f)
                print(f"[STRONGS] Hebrew dictionary loaded: {len(self._hebrew_dict)} entries")
            else:
                print(f"[STRONGS] Hebrew dictionary not available")
                self._hebrew_dict = {}
        return self._hebrew_dict

    @property
    def lexicon(self) -> Dict:
        """상세 렉시콘 (lazy loading, 자동 다운로드)"""
        if self._lexicon is None:
            path = os.path.join(DATA_DIR, 'lexicon.json')
            if not os.path.exists(path):
                # 자동 다운로드 시도
                _download_file('lexicon.json', GITHUB_URLS['lexicon.json'])
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self._lexicon = json.load(f)
                print(f"[STRONGS] Lexicon loaded: {len(self._lexicon)} entries")
            else:
                print(f"[STRONGS] Lexicon not found: {path}")
                self._lexicon = {}
        return self._lexicon

    def parse_reference(self, reference: str) -> Optional[Tuple[str, int, int]]:
        """
        성경 구절 참조 파싱

        Args:
            reference: "요한복음 3:16", "요 3:16", "John 3:16" 등

        Returns:
            (book_abbr, chapter, verse) 또는 None
        """
        # 정규식: 책이름 장:절 (또는 장.절)
        pattern = r'^(.+?)\s*(\d+)\s*[:\.]\s*(\d+)(?:\s*[-~]\s*\d+)?$'
        match = re.match(pattern, reference.strip())

        if not match:
            return None

        book_name = match.group(1).strip()
        chapter = int(match.group(2))
        verse = int(match.group(3))

        # 책 이름 변환
        book_abbr = BOOK_NAME_MAP.get(book_name)

        # 영문 이름 직접 매칭 시도
        if not book_abbr:
            # 영문 약어 직접 사용
            for ko_name, abbr in BOOK_NAME_MAP.items():
                if book_name.lower() == abbr.lower():
                    book_abbr = abbr
                    break
            # John, Matthew 등 전체 이름
            if not book_abbr:
                english_map = {
                    'genesis': 'Gen', 'exodus': 'Exo', 'leviticus': 'Lev',
                    'numbers': 'Num', 'deuteronomy': 'Deu', 'joshua': 'Jos',
                    'judges': 'Jdg', 'ruth': 'Rth', 'psalms': 'Psa', 'psalm': 'Psa',
                    'proverbs': 'Pro', 'ecclesiastes': 'Ecc', 'isaiah': 'Isa',
                    'jeremiah': 'Jer', 'ezekiel': 'Eze', 'daniel': 'Dan',
                    'matthew': 'Mat', 'mark': 'Mar', 'luke': 'Luk', 'john': 'Jhn',
                    'acts': 'Act', 'romans': 'Rom', 'galatians': 'Gal',
                    'ephesians': 'Eph', 'philippians': 'Phl', 'colossians': 'Col',
                    'hebrews': 'Heb', 'james': 'Jas', 'revelation': 'Rev',
                    '1 corinthians': '1Co', '2 corinthians': '2Co',
                    '1 thessalonians': '1Th', '2 thessalonians': '2Th',
                    '1 timothy': '1Ti', '2 timothy': '2Ti', 'titus': 'Tit',
                    'philemon': 'Phm', '1 peter': '1Pe', '2 peter': '2Pe',
                    '1 john': '1Jo', '2 john': '2Jo', '3 john': '3Jo', 'jude': 'Jde'
                }
                book_abbr = english_map.get(book_name.lower())

        if not book_abbr:
            print(f"[STRONGS] Unknown book name: {book_name}")
            return None

        return (book_abbr, chapter, verse)

    def get_verse_with_strongs(self, reference: str) -> Optional[Dict]:
        """
        구절 텍스트와 Strong's 번호 조회

        Args:
            reference: "요한복음 3:16"

        Returns:
            {
                "text": "For God so loved...",
                "strongs_numbers": ["G1063", "G2316", "G3779", ...]
            }
        """
        parsed = self.parse_reference(reference)
        if not parsed:
            return None

        book_abbr, chapter, verse = parsed

        # KJV JSON 로드 (캐시 사용)
        if book_abbr not in self._kjv_cache:
            kjv_path = os.path.join(DATA_DIR, '..', '..', 'data', 'strongs', f'{book_abbr}.json')
            # GitHub에서 직접 다운로드 필요
            kjv_url = f"https://raw.githubusercontent.com/kaiserlik/kjv/master/{book_abbr}.json"

            try:
                import urllib.request
                with urllib.request.urlopen(kjv_url, timeout=10) as response:
                    self._kjv_cache[book_abbr] = json.loads(response.read().decode('utf-8'))
                print(f"[STRONGS] Loaded KJV book: {book_abbr}")
            except Exception as e:
                print(f"[STRONGS] Failed to load KJV {book_abbr}: {e}")
                return None

        kjv_data = self._kjv_cache.get(book_abbr, {})
        verse_key = f"{book_abbr}|{chapter}|{verse}"
        chapter_key = f"{book_abbr}|{chapter}"

        verse_data = kjv_data.get(book_abbr, {}).get(chapter_key, {}).get(verse_key, {})

        if not verse_data:
            print(f"[STRONGS] Verse not found: {verse_key}")
            return None

        en_text = verse_data.get('en', '')

        # Strong's 번호 추출
        strongs_pattern = r'\[([GH]\d+)\]'
        strongs_numbers = re.findall(strongs_pattern, en_text)

        # 태그 제거한 순수 텍스트
        clean_text = re.sub(r'\[([GH]\d+)\]', '', en_text)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)  # HTML 태그 제거
        clean_text = ' '.join(clean_text.split())  # 공백 정리

        return {
            "reference": reference,
            "book": book_abbr,
            "chapter": chapter,
            "verse": verse,
            "text": clean_text,
            "text_with_strongs": en_text,
            "strongs_numbers": strongs_numbers
        }

    def lookup_strongs(self, strongs_number: str) -> Optional[Dict]:
        """
        Strong's 번호로 원어 정의 조회

        Args:
            strongs_number: "G25", "H430" 등

        Returns:
            {
                "strongs": "G25",
                "lemma": "ἀγαπάω",
                "translit": "agapáō",
                "pronunciation": "ag-ap-ah'-o",
                "definition": "to love...",
                "kjv_usage": "love, beloved",
                "derivation": "...",
                "outline": "..."  # lexicon에서 추가 정보
            }
        """
        if not strongs_number:
            return None

        strongs_number = strongs_number.upper()

        # G로 시작 = 헬라어, H로 시작 = 히브리어
        if strongs_number.startswith('G'):
            base_dict = self.greek_dict
        elif strongs_number.startswith('H'):
            base_dict = self.hebrew_dict
        else:
            return None

        entry = base_dict.get(strongs_number)
        if not entry:
            return None

        result = {
            "strongs": strongs_number,
            "lemma": entry.get("lemma", ""),
            "translit": entry.get("translit", entry.get("xlit", "")),
            "pronunciation": entry.get("pron", ""),
            "definition": entry.get("strongs_def", ""),
            "kjv_usage": entry.get("kjv_def", ""),
            "derivation": entry.get("derivation", ""),
        }

        # Lexicon에서 추가 정보 가져오기
        lex_entry = self.lexicon.get(strongs_number, {})
        if lex_entry:
            result["outline"] = lex_entry.get("outline_usage", "")
            result["part_of_speech"] = lex_entry.get("part_of_speech", "")
            result["occurrences"] = lex_entry.get("occurrences", "")
            result["root_word"] = lex_entry.get("root_word", "")

        return result

    def get_key_words_analysis(self, reference: str, top_n: int = 5) -> List[Dict]:
        """
        구절의 핵심 단어 원어 분석

        Args:
            reference: "요한복음 3:16"
            top_n: 반환할 최대 단어 수

        Returns:
            [
                {
                    "english": "loved",
                    "strongs": "G25",
                    "lemma": "ἀγαπάω",
                    "translit": "agapáō",
                    "definition": "to love unconditionally...",
                    ...
                },
                ...
            ]
        """
        verse_data = self.get_verse_with_strongs(reference)
        if not verse_data:
            return []

        strongs_numbers = verse_data.get('strongs_numbers', [])
        text_with_strongs = verse_data.get('text_with_strongs', '')

        # 중복 제거하면서 순서 유지
        seen = set()
        unique_numbers = []
        for num in strongs_numbers:
            if num not in seen:
                seen.add(num)
                unique_numbers.append(num)

        results = []
        for strongs_num in unique_numbers[:top_n * 2]:  # 여유있게 조회
            lookup = self.lookup_strongs(strongs_num)
            if lookup and lookup.get('definition'):
                # 영어 단어 추출 (해당 Strong's 번호 앞의 단어)
                pattern = rf'(\w+)\[{strongs_num}\]'
                match = re.search(pattern, text_with_strongs, re.IGNORECASE)
                english_word = match.group(1) if match else ""

                lookup['english'] = english_word
                results.append(lookup)

                if len(results) >= top_n:
                    break

        return results

    def is_new_testament(self, book_abbr: str) -> bool:
        """신약 책인지 확인"""
        return book_abbr in NT_BOOKS


# 싱글톤 인스턴스
_strongs_lookup: Optional[StrongsLookup] = None


def get_strongs_lookup() -> StrongsLookup:
    """StrongsLookup 싱글톤 인스턴스 반환"""
    global _strongs_lookup
    if _strongs_lookup is None:
        _strongs_lookup = StrongsLookup()
    return _strongs_lookup


# 편의 함수들
def analyze_verse_strongs(reference: str, top_n: int = 5) -> Dict:
    """
    성경 구절 원어 분석 (편의 함수)

    Args:
        reference: "요한복음 3:16"
        top_n: 핵심 단어 수

    Returns:
        {
            "reference": "요한복음 3:16",
            "text": "For God so loved the world...",
            "key_words": [
                {"english": "loved", "lemma": "ἀγαπάω", ...},
                ...
            ],
            "all_strongs": ["G1063", "G2316", ...]
        }
    """
    lookup = get_strongs_lookup()

    verse_data = lookup.get_verse_with_strongs(reference)
    if not verse_data:
        return {
            "reference": reference,
            "error": "구절을 찾을 수 없습니다",
            "text": "",
            "key_words": [],
            "all_strongs": []
        }

    key_words = lookup.get_key_words_analysis(reference, top_n)

    return {
        "reference": reference,
        "book": verse_data.get('book'),
        "chapter": verse_data.get('chapter'),
        "verse": verse_data.get('verse'),
        "text": verse_data.get('text'),
        "text_with_strongs": verse_data.get('text_with_strongs'),
        "key_words": key_words,
        "all_strongs": verse_data.get('strongs_numbers', [])
    }


def format_strongs_for_prompt(strongs_analysis: Dict) -> str:
    """
    Strong's 분석 결과를 Step1 프롬프트용 텍스트로 포맷팅

    Args:
        strongs_analysis: analyze_verse_strongs() 결과

    Returns:
        포맷팅된 텍스트 문자열
    """
    if not strongs_analysis or strongs_analysis.get('error'):
        return ""

    lines = []
    lines.append("【 원어 분석 (Strong's Concordance) 】")
    lines.append(f"본문: {strongs_analysis.get('reference', '')}")
    lines.append(f"영문 (KJV): {strongs_analysis.get('text', '')}")
    lines.append("")

    key_words = strongs_analysis.get('key_words', [])
    if key_words:
        lines.append("▶ 핵심 원어 단어:")
        for i, word in enumerate(key_words, 1):
            lemma = word.get('lemma', '')
            translit = word.get('translit', '')
            strongs_num = word.get('strongs', '')
            english = word.get('english', '')
            definition = word.get('definition', '')
            outline = word.get('outline', '')

            # 정의 정리 (특수문자 제거)
            definition = definition.replace('&#8212;', '—').strip()

            lines.append(f"  {i}. {lemma} ({translit}, {strongs_num})")
            if english:
                lines.append(f"     → 영어: {english}")
            if definition:
                lines.append(f"     → 의미: {definition}")
            if outline:
                # HTML 엔티티 정리
                outline = outline.replace('&quot;', '"').replace('&#8212;', '—')
                if len(outline) > 200:
                    outline = outline[:200] + "..."
                lines.append(f"     → 상세: {outline}")
            lines.append("")

    return "\n".join(lines)

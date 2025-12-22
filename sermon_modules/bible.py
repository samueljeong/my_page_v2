"""
성경 본문 검색 모듈 (개역개정)

사용법:
    from sermon_modules.bible import get_verses, parse_reference, format_verses

    # 구절 가져오기
    verses = get_verses("창세기", 1, 1, 3)  # 창세기 1:1-3
    verses = get_verses("창", 1, 1)          # 창세기 1:1 (약어 지원)

    # 참조 문자열 파싱
    ref = parse_reference("창1:1-3")
    ref = parse_reference("요한복음 3:16")

    # 포맷된 본문 가져오기
    text = format_verses("사9:1-7")
"""

import json
import re
from pathlib import Path
from functools import lru_cache
from typing import Optional, List, Dict, Tuple

# 성경 파일 경로 (루트 디렉토리에 위치)
BIBLE_PATH = Path(__file__).parent.parent / "korean_bible_gae.json"

# 성경 책 이름 매핑 (약어 -> 정식명, ID)
BOOK_MAP = {
    # 구약 39권
    "창세기": ("창세기", 1), "창": ("창세기", 1),
    "출애굽기": ("출애굽기", 2), "출": ("출애굽기", 2),
    "레위기": ("레위기", 3), "레": ("레위기", 3),
    "민수기": ("민수기", 4), "민": ("민수기", 4),
    "신명기": ("신명기", 5), "신": ("신명기", 5),
    "여호수아": ("여호수아", 6), "수": ("여호수아", 6),
    "사사기": ("사사기", 7), "삿": ("사사기", 7),
    "룻기": ("룻기", 8), "룻": ("룻기", 8),
    "사무엘상": ("사무엘상", 9), "삼상": ("사무엘상", 9),
    "사무엘하": ("사무엘하", 10), "삼하": ("사무엘하", 10),
    "열왕기상": ("열왕기상", 11), "왕상": ("열왕기상", 11),
    "열왕기하": ("열왕기하", 12), "왕하": ("열왕기하", 12),
    "역대상": ("역대상", 13), "대상": ("역대상", 13),
    "역대하": ("역대하", 14), "대하": ("역대하", 14),
    "에스라": ("에스라", 15), "스": ("에스라", 15),
    "느헤미야": ("느헤미야", 16), "느": ("느헤미야", 16),
    "에스더": ("에스더", 17), "에": ("에스더", 17),
    "욥기": ("욥기", 18), "욥": ("욥기", 18),
    "시편": ("시편", 19), "시": ("시편", 19),
    "잠언": ("잠언", 20), "잠": ("잠언", 20),
    "전도서": ("전도서", 21), "전": ("전도서", 21),
    "아가": ("아가", 22),
    "이사야": ("이사야", 23), "사": ("이사야", 23),
    "예레미야": ("예레미야", 24), "렘": ("예레미야", 24),
    "예레미야애가": ("예레미야애가", 25), "애": ("예레미야애가", 25),
    "에스겔": ("에스겔", 26), "겔": ("에스겔", 26),
    "다니엘": ("다니엘", 27), "단": ("다니엘", 27),
    "호세아": ("호세아", 28), "호": ("호세아", 28),
    "요엘": ("요엘", 29), "욜": ("요엘", 29),
    "아모스": ("아모스", 30), "암": ("아모스", 30),
    "오바댜": ("오바댜", 31), "옵": ("오바댜", 31),
    "요나": ("요나", 32), "욘": ("요나", 32),
    "미가": ("미가", 33), "미": ("미가", 33),
    "나훔": ("나훔", 34), "나": ("나훔", 34),
    "하박국": ("하박국", 35), "합": ("하박국", 35),
    "스바냐": ("스바냐", 36), "습": ("스바냐", 36),
    "학개": ("학개", 37), "학": ("학개", 37),
    "스가랴": ("스가랴", 38), "슥": ("스가랴", 38),
    "말라기": ("말라기", 39), "말": ("말라기", 39),
    # 신약 27권
    "마태복음": ("마태복음", 40), "마": ("마태복음", 40),
    "마가복음": ("마가복음", 41), "막": ("마가복음", 41),
    "누가복음": ("누가복음", 42), "눅": ("누가복음", 42),
    "요한복음": ("요한복음", 43), "요": ("요한복음", 43),
    "사도행전": ("사도행전", 44), "행": ("사도행전", 44),
    "로마서": ("로마서", 45), "롬": ("로마서", 45),
    "고린도전서": ("고린도전서", 46), "고전": ("고린도전서", 46),
    "고린도후서": ("고린도후서", 47), "고후": ("고린도후서", 47),
    "갈라디아서": ("갈라디아서", 48), "갈": ("갈라디아서", 48),
    "에베소서": ("에베소서", 49), "엡": ("에베소서", 49),
    "빌립보서": ("빌립보서", 50), "빌": ("빌립보서", 50),
    "골로새서": ("골로새서", 51), "골": ("골로새서", 51),
    "데살로니가전서": ("데살로니가전서", 52), "살전": ("데살로니가전서", 52),
    "데살로니가후서": ("데살로니가후서", 53), "살후": ("데살로니가후서", 53),
    "디모데전서": ("디모데전서", 54), "딤전": ("디모데전서", 54),
    "디모데후서": ("디모데후서", 55), "딤후": ("디모데후서", 55),
    "디도서": ("디도서", 56), "딛": ("디도서", 56),
    "빌레몬서": ("빌레몬서", 57), "몬": ("빌레몬서", 57),
    "히브리서": ("히브리서", 58), "히": ("히브리서", 58),
    "야고보서": ("야고보서", 59), "약": ("야고보서", 59),
    "베드로전서": ("베드로전서", 60), "벧전": ("베드로전서", 60),
    "베드로후서": ("베드로후서", 61), "벧후": ("베드로후서", 61),
    "요한일서": ("요한일서", 62), "요일": ("요한일서", 62),
    "요한이서": ("요한이서", 63), "요이": ("요한이서", 63),
    "요한삼서": ("요한삼서", 64), "요삼": ("요한삼서", 64),
    "유다서": ("유다서", 65), "유": ("유다서", 65),
    "요한계시록": ("요한계시록", 66), "계": ("요한계시록", 66),
}


@lru_cache(maxsize=1)
def _load_bible() -> dict:
    """성경 데이터를 로드합니다 (캐싱됨)."""
    if not BIBLE_PATH.exists():
        print(f"[Bible] 성경 파일을 찾을 수 없습니다: {BIBLE_PATH}")
        return {"version": "개역개정", "books": []}

    try:
        with open(BIBLE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Bible] 성경 파일 로드 오류: {e}")
        return {"version": "개역개정", "books": []}


def _get_book_by_id(book_id: int) -> Optional[dict]:
    """책 ID로 책 데이터를 가져옵니다."""
    bible = _load_bible()
    for book in bible.get("books", []):
        if book.get("id") == book_id:
            return book
    return None


def _get_book_by_name(name: str) -> Optional[dict]:
    """책 이름(정식명 또는 약어)으로 책 데이터를 가져옵니다."""
    name = name.strip()
    if name not in BOOK_MAP:
        return None

    _, book_id = BOOK_MAP[name]
    return _get_book_by_id(book_id)


def parse_reference(ref: str) -> Optional[Dict]:
    """
    성경 참조 문자열을 파싱합니다.

    지원 형식:
        - "창세기 1:1-3"
        - "창1:1-3"
        - "창 1:1"
        - "요한복음 3:16"
        - "사9:1-7"
        - "시편 23편" (전체 장)
        - "시23" (전체 장)

    Returns:
        {
            "book_name": "창세기",
            "book_id": 1,
            "chapter": 1,
            "verse_start": 1,
            "verse_end": 3,
            "original": "창세기 1:1-3"
        }
        또는 파싱 실패 시 None
    """
    if not ref or not isinstance(ref, str):
        return None

    ref = ref.strip()
    original = ref

    # "편" -> 장으로 처리 (시편 전용)
    ref = re.sub(r"(\d+)\s*편", r"\1", ref)

    # 패턴: 책이름 장:절-절 또는 책이름 장:절 또는 책이름 장
    # 예: 창세기 1:1-3, 창1:1, 요한복음 3:16, 시23
    pattern = r"^([가-힣]+)\s*(\d+)(?::(\d+)(?:-(\d+))?)?$"
    match = re.match(pattern, ref)

    if not match:
        return None

    book_key = match.group(1)
    chapter = int(match.group(2))
    verse_start = int(match.group(3)) if match.group(3) else None
    verse_end = int(match.group(4)) if match.group(4) else verse_start

    if book_key not in BOOK_MAP:
        return None

    book_name, book_id = BOOK_MAP[book_key]

    return {
        "book_name": book_name,
        "book_id": book_id,
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "original": original
    }


def get_verses(
    book: str,
    chapter: int,
    verse_start: int = None,
    verse_end: int = None
) -> List[Dict]:
    """
    특정 성경 구절들을 가져옵니다.

    Args:
        book: 책 이름 (정식명 또는 약어)
        chapter: 장 번호
        verse_start: 시작 절 (없으면 전체 장)
        verse_end: 끝 절 (없으면 verse_start만)

    Returns:
        [{"verse": 1, "text": "태초에 하나님이 천지를 창조하시니라"}, ...]
    """
    book_data = _get_book_by_name(book)
    if not book_data:
        return []

    chapters = book_data.get("chapters", [])
    if chapter < 1 or chapter > len(chapters):
        return []

    chapter_data = chapters[chapter - 1]
    all_verses = chapter_data.get("verses", [])

    if verse_start is None:
        # 전체 장 반환
        return all_verses

    if verse_end is None:
        verse_end = verse_start

    # 해당 절 범위만 필터링
    return [v for v in all_verses if verse_start <= v.get("verse", 0) <= verse_end]


def get_verses_from_reference(ref: str) -> List[Dict]:
    """
    참조 문자열에서 구절들을 가져옵니다.

    Args:
        ref: "창1:1-3" 형식의 참조 문자열

    Returns:
        [{"verse": 1, "text": "..."}, ...]
    """
    parsed = parse_reference(ref)
    if not parsed:
        return []

    return get_verses(
        parsed["book_name"],
        parsed["chapter"],
        parsed["verse_start"],
        parsed["verse_end"]
    )


def format_verses(
    ref: str,
    include_reference: bool = True,
    separator: str = " "
) -> str:
    """
    참조 문자열에서 포맷된 성경 본문을 반환합니다.

    Args:
        ref: "창1:1-3" 형식의 참조 문자열
        include_reference: 참조 표시 포함 여부
        separator: 구절 사이 구분자

    Returns:
        "창세기 1:1-3\n1 태초에 하나님이 천지를 창조하시니라 2 땅이 혼돈하고..."
    """
    parsed = parse_reference(ref)
    if not parsed:
        return f"[{ref}] 구절을 찾을 수 없습니다."

    verses = get_verses(
        parsed["book_name"],
        parsed["chapter"],
        parsed["verse_start"],
        parsed["verse_end"]
    )

    if not verses:
        return f"[{ref}] 구절을 찾을 수 없습니다."

    # 본문 포맷팅
    verse_texts = []
    for v in verses:
        verse_num = v.get("verse", "")
        text = v.get("text", "")
        verse_texts.append(f"{verse_num} {text}")

    formatted = separator.join(verse_texts)

    if include_reference:
        # 정규화된 참조 문자열 생성
        ref_str = f"{parsed['book_name']} {parsed['chapter']}"
        if parsed["verse_start"]:
            ref_str += f":{parsed['verse_start']}"
            if parsed["verse_end"] and parsed["verse_end"] != parsed["verse_start"]:
                ref_str += f"-{parsed['verse_end']}"

        return f"{ref_str}\n{formatted}"

    return formatted


def format_verses_for_prompt(ref: str) -> str:
    """
    Step3 프롬프트용 성경 본문 포맷팅.

    Args:
        ref: "창1:1-3" 또는 "사9:1-7" 형식의 참조 문자열

    Returns:
        ```
        [창세기 1:1-3 개역개정 본문]
        1 태초에 하나님이 천지를 창조하시니라
        2 땅이 혼돈하고 공허하며 흑암이 깊음 위에 있고 하나님의 영은 수면 위에 운행하시니라
        3 하나님이 이르시되 빛이 있으라 하시니 빛이 있었고
        ```
    """
    parsed = parse_reference(ref)
    if not parsed:
        return f"[{ref}] 성경 구절을 파싱할 수 없습니다."

    verses = get_verses(
        parsed["book_name"],
        parsed["chapter"],
        parsed["verse_start"],
        parsed["verse_end"]
    )

    if not verses:
        return f"[{ref}] 해당 구절을 찾을 수 없습니다."

    # 정규화된 참조 문자열
    ref_str = f"{parsed['book_name']} {parsed['chapter']}"
    if parsed["verse_start"]:
        ref_str += f":{parsed['verse_start']}"
        if parsed["verse_end"] and parsed["verse_end"] != parsed["verse_start"]:
            ref_str += f"-{parsed['verse_end']}"

    # 본문 포맷팅 (각 절을 줄바꿈으로 구분)
    lines = [f"[{ref_str} 개역개정 본문]"]
    for v in verses:
        lines.append(f"{v.get('verse', '')} {v.get('text', '')}")

    return "\n".join(lines)


def get_book_info(book: str) -> Optional[Dict]:
    """
    책 정보를 반환합니다.

    Args:
        book: 책 이름 (정식명 또는 약어)

    Returns:
        {"name": "창세기", "id": 1, "chapters": 50, "abbr": "창"}
    """
    if book not in BOOK_MAP:
        return None

    book_name, book_id = BOOK_MAP[book]
    book_data = _get_book_by_id(book_id)

    if not book_data:
        return None

    # 약어 찾기
    abbr = book
    for key, (name, bid) in BOOK_MAP.items():
        if bid == book_id and len(key) <= 2:
            abbr = key
            break

    return {
        "name": book_name,
        "id": book_id,
        "chapters": len(book_data.get("chapters", [])),
        "abbr": abbr
    }


def search_verses(keyword: str, limit: int = 10) -> List[Dict]:
    """
    키워드로 성경 구절을 검색합니다.

    Args:
        keyword: 검색 키워드
        limit: 최대 결과 수

    Returns:
        [{"book": "창세기", "chapter": 1, "verse": 1, "text": "...", "reference": "창1:1"}, ...]
    """
    if not keyword:
        return []

    bible = _load_bible()
    results = []

    for book in bible.get("books", []):
        book_name = book.get("name", "")

        # 약어 찾기
        abbr = book_name
        for key, (name, _) in BOOK_MAP.items():
            if name == book_name and len(key) <= 2:
                abbr = key
                break

        for chapter_data in book.get("chapters", []):
            chapter_num = chapter_data.get("chapter", 0)

            for verse_data in chapter_data.get("verses", []):
                verse_num = verse_data.get("verse", 0)
                text = verse_data.get("text", "")

                if keyword in text:
                    results.append({
                        "book": book_name,
                        "chapter": chapter_num,
                        "verse": verse_num,
                        "text": text,
                        "reference": f"{abbr}{chapter_num}:{verse_num}"
                    })

                    if len(results) >= limit:
                        return results

    return results


# 테스트용
if __name__ == "__main__":
    # 테스트
    print("=== 성경 본문 검색 테스트 ===\n")

    # 1. 창세기 1:1 테스트
    print("1. 창세기 1:1")
    print(format_verses("창1:1"))
    print()

    # 2. 요한복음 3:16 테스트
    print("2. 요한복음 3:16")
    print(format_verses("요3:16"))
    print()

    # 3. 이사야 9:1-7 테스트
    print("3. 이사야 9:1-7")
    print(format_verses_for_prompt("사9:1-7"))
    print()

    # 4. 검색 테스트
    print("4. '사랑' 검색")
    results = search_verses("사랑", limit=3)
    for r in results:
        print(f"  {r['reference']}: {r['text'][:50]}...")

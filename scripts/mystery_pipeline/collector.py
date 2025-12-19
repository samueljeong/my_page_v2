"""
해외 미스테리 자료 수집 모듈

영어 위키백과에서 미스테리 사건 정보 수집
- Wikipedia API 사용 (무료, 제한 없음)
- 전체 본문 추출
- 한국어 번역은 Opus가 담당
"""

import re
import html
import time
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import quote_plus

from .config import FEATURED_MYSTERIES, MYSTERY_CATEGORIES


# Wikipedia API 기본 설정
WIKI_API_BASE = "https://en.wikipedia.org/w/api.php"
WIKI_USER_AGENT = "MysteryPipelineBot/1.0 (https://drama-s2ns.onrender.com; contact@example.com) Python/3.9"


def search_wikipedia_en(keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    영어 위키백과 검색

    Args:
        keyword: 검색어
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    items = []

    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": keyword,
            "srlimit": max_results,
            "format": "json",
            "utf8": 1,
        }

        headers = {
            "User-Agent": WIKI_USER_AGENT,
            "Accept": "application/json",
        }

        response = requests.get(WIKI_API_BASE, params=params, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"[MYSTERY] Wikipedia 검색 실패: {response.status_code}")
            return items

        data = response.json()
        search_results = data.get("query", {}).get("search", [])

        for result in search_results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # HTML 태그 제거
            snippet = re.sub(r'<[^>]+>', '', snippet)
            snippet = html.unescape(snippet)

            items.append({
                "title": title,
                "snippet": snippet,
                "url": f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}",
            })

        print(f"[MYSTERY] Wikipedia 검색 '{keyword}': {len(items)}개 결과")

    except Exception as e:
        print(f"[MYSTERY] Wikipedia 검색 오류 ({keyword}): {e}")

    return items


def get_wikipedia_content(title: str) -> Optional[Dict[str, Any]]:
    """
    위키백과 문서 전체 내용 가져오기

    Args:
        title: 문서 제목 (예: "Dyatlov_Pass_incident")

    Returns:
        문서 정보 딕셔너리 또는 None
    """
    try:
        headers = {
            "User-Agent": WIKI_USER_AGENT,
            "Accept": "application/json",
        }

        print(f"[MYSTERY] Wikipedia 문서 가져오는 중: {title}")

        # 1) Wikipedia REST API로 전체 내용 가져오기 (더 긴 내용 반환)
        rest_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{quote_plus(title)}"

        try:
            response = requests.get(rest_url, headers=headers, timeout=30)

            if response.status_code == 200:
                # HTML에서 텍스트 추출
                html_content = response.text

                # 스크립트, 스타일 태그 제거
                html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

                # 참조, 각주 제거 (보통 [1], [2] 형태)
                html_content = re.sub(r'<sup[^>]*class="[^"]*reference[^"]*"[^>]*>.*?</sup>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

                # 테이블 제거 (데이터가 복잡해서)
                html_content = re.sub(r'<table[^>]*>.*?</table>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

                # 모든 HTML 태그를 공백으로
                text_content = re.sub(r'<[^>]+>', ' ', html_content)

                # 연속 공백 정리
                text_content = re.sub(r'\s+', ' ', text_content).strip()

                # HTML 엔티티 디코딩
                text_content = html.unescape(text_content)

                if len(text_content) > 5000:
                    print(f"[MYSTERY] REST API 성공: {len(text_content):,}자")

                    return {
                        "title": title.replace("_", " "),
                        "url": f"https://en.wikipedia.org/wiki/{title}",
                        "content": text_content[:50000],  # 최대 50,000자
                        "categories": [],
                        "length": len(text_content[:50000]),
                    }
        except Exception as e:
            print(f"[MYSTERY] REST API 실패, 기본 API로 시도: {e}")

        # 2) 기본 API로 fallback (짧은 내용)
        params = {
            "action": "query",
            "titles": title.replace("_", " "),
            "prop": "extracts|info|categories",
            "exintro": False,  # 전체 내용
            "explaintext": True,  # 평문으로
            "exchars": 50000,  # 최대 문자 수
            "inprop": "url",
            "cllimit": 10,
            "format": "json",
            "utf8": 1,
        }

        response = requests.get(WIKI_API_BASE, params=params, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[MYSTERY] Wikipedia 문서 가져오기 실패: {response.status_code}")
            return None

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if page_id == "-1":
                print(f"[MYSTERY] 문서를 찾을 수 없음: {title}")
                return None

            extract = page_data.get("extract", "")
            full_url = page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{title}")
            categories = [c.get("title", "").replace("Category:", "")
                         for c in page_data.get("categories", [])]

            if not extract:
                print(f"[MYSTERY] 내용이 비어있음: {title}")
                return None

            # 내용 정리 (최대 50,000자 - Opus가 처리할 수 있는 충분한 양)
            extract = extract.strip()
            if len(extract) > 50000:
                extract = extract[:50000] + "\n\n[... 내용 생략 ...]"

            print(f"[MYSTERY] 문서 가져오기 성공: {title} ({len(extract):,}자)")

            return {
                "title": page_data.get("title", title),
                "url": full_url,
                "content": extract,
                "categories": categories,
                "length": len(extract),
            }

        return None

    except Exception as e:
        print(f"[MYSTERY] Wikipedia 문서 가져오기 오류 ({title}): {e}")
        return None


def collect_mystery_article(
    title: str,
    title_ko: str = None,
    category: str = None,
) -> Dict[str, Any]:
    """
    미스테리 사건 자료 수집

    Args:
        title: 위키백과 문서 제목 (영문)
        title_ko: 한국어 제목 (있으면)
        category: 카테고리 키

    Returns:
        수집된 자료 딕셔너리
    """
    result = {
        "success": False,
        "title_en": title,
        "title_ko": title_ko or "",
        "category": category or "",
        "url": "",
        "content": "",
        "summary": "",
        "error": None,
    }

    try:
        # 위키백과에서 내용 가져오기
        wiki_data = get_wikipedia_content(title)

        if not wiki_data:
            result["error"] = "위키백과에서 문서를 찾을 수 없습니다"
            return result

        result["success"] = True
        result["url"] = wiki_data["url"]
        result["content"] = wiki_data["content"]

        # 요약 생성 (첫 500자)
        content = wiki_data["content"]
        first_para_end = content.find("\n\n")
        if first_para_end > 0 and first_para_end < 1000:
            result["summary"] = content[:first_para_end].strip()
        else:
            result["summary"] = content[:500].strip() + "..."

        print(f"[MYSTERY] 자료 수집 완료: {title}")
        print(f"[MYSTERY] - 전체 내용: {len(result['content']):,}자")
        print(f"[MYSTERY] - 요약: {len(result['summary'])}자")

    except Exception as e:
        result["error"] = str(e)
        print(f"[MYSTERY] 자료 수집 오류 ({title}): {e}")

    return result


def get_featured_mystery(index: int = 0) -> Optional[Dict[str, Any]]:
    """
    추천 미스테리 사건 가져오기 (초기 콘텐츠용)

    Args:
        index: FEATURED_MYSTERIES 인덱스

    Returns:
        미스테리 정보 딕셔너리
    """
    if index < 0 or index >= len(FEATURED_MYSTERIES):
        print(f"[MYSTERY] 인덱스 범위 초과: {index} (전체 {len(FEATURED_MYSTERIES)}개)")
        return None

    mystery = FEATURED_MYSTERIES[index]

    # 위키백과에서 내용 수집
    collected = collect_mystery_article(
        title=mystery["title"],
        title_ko=mystery.get("title_ko"),
        category=mystery.get("category"),
    )

    if collected["success"]:
        # 추가 정보 병합
        collected["year"] = mystery.get("year", "")
        collected["country"] = mystery.get("country", "")
        collected["hook"] = mystery.get("hook", "")

    return collected


def get_next_mystery(
    used_titles: List[str] = None,
    category: str = None,
) -> Optional[Dict[str, Any]]:
    """
    다음 미스테리 사건 가져오기 (사용하지 않은 것 중에서)

    Args:
        used_titles: 이미 사용한 제목 리스트
        category: 특정 카테고리만 (없으면 전체)

    Returns:
        미스테리 정보 딕셔너리
    """
    used_titles = used_titles or []

    for mystery in FEATURED_MYSTERIES:
        # 이미 사용한 것은 스킵
        if mystery["title"] in used_titles:
            continue

        # 카테고리 필터
        if category and mystery.get("category") != category:
            continue

        # 위키백과에서 내용 수집
        collected = collect_mystery_article(
            title=mystery["title"],
            title_ko=mystery.get("title_ko"),
            category=mystery.get("category"),
        )

        if collected["success"]:
            collected["year"] = mystery.get("year", "")
            collected["country"] = mystery.get("country", "")
            collected["hook"] = mystery.get("hook", "")
            return collected

        # 실패하면 다음으로
        time.sleep(0.5)

    print(f"[MYSTERY] 사용 가능한 미스테리가 없습니다")
    return None


def list_available_mysteries(used_titles: List[str] = None) -> List[Dict[str, str]]:
    """
    사용 가능한 미스테리 목록 반환 (간략 정보만)

    Args:
        used_titles: 이미 사용한 제목 리스트

    Returns:
        사용 가능한 미스테리 목록
    """
    used_titles = used_titles or []
    available = []

    for mystery in FEATURED_MYSTERIES:
        if mystery["title"] not in used_titles:
            available.append({
                "title": mystery["title"],
                "title_ko": mystery.get("title_ko", ""),
                "category": mystery.get("category", ""),
                "year": mystery.get("year", ""),
                "hook": mystery.get("hook", ""),
            })

    return available

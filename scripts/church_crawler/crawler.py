#!/usr/bin/env python3
"""
교적 크롤링 스크립트
- god4u.dimode.co.kr 사이트에서 교적 데이터를 크롤링합니다.
- 브라우저에서 로그인 후 쿠키를 복사하여 사용합니다.

사용법:
1. 브라우저에서 god4u.dimode.co.kr 로그인
2. F12 → Application → Cookies에서 쿠키 값 복사
3. 아래 COOKIES 딕셔너리에 붙여넣기
4. python crawler.py 실행
"""

import requests
import json
import csv
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# 설정: 브라우저에서 복사한 쿠키를 여기에 붙여넣으세요
# ============================================================
COOKIES = {
    "ASP.NET_SessionId": "xgsyv0zp5q0b14znzorohsk2",
    "pastorinfo": "sUser=%c1%a4%bb%e7%b9%ab%bf%a4&sID=5700&sUserName=%c1%a4%bb%e7%b9%ab%bf%a4&sIsAdmin=1&churchid=god4u&chname=%c0%c7%c1%a4%ba%ce%c1%df%be%d3%b1%b3%c8%b8&sChurchAuth=OK&sCashAuth=OK&sSCashAuth=&sRangeAuth=OK&sSchoolAuth=OK&sYouthAuth=OK",
    "AUTOLOGIN": "YES",
}

# API 설정
BASE_URL = "http://god4u.dimode.co.kr"
API_URL = f"{BASE_URL}/Handler/GetPersonListMobileJSon.asmx/GetPersonSearchListDefault"

# 페이지 설정
PAGE_SIZE = 100  # 한 번에 가져올 개수 (최대 100 권장)
DELAY_BETWEEN_PAGES = 0.5  # 페이지 간 딜레이 (초)

# 출력 필드 설정 (원하는 필드만 선택)
OUTPUT_FIELDS = [
    ("id", "교적번호"),
    ("name", "이름"),
    ("sex", "성별"),
    ("birth", "생년월일"),
    ("age", "나이"),
    ("cvname", "직분1"),
    ("cvname1", "직분2"),
    ("handphone", "핸드폰"),
    ("tel", "전화"),
    ("addr", "주소"),
    ("zipcode", "우편번호"),
    ("sido", "시도"),
    ("gugun", "구군"),
    ("dong", "동"),
    ("email", "이메일"),
    ("state", "상태"),
    ("state1", "그룹"),
    ("state3", "출석상태"),
    ("regday", "등록일"),
    ("ran1", "가족"),
    ("carnum", "차량번호"),
    ("etc", "기타"),
]


def create_payload(page: int = 1, page_size: int = PAGE_SIZE, search_name: str = "") -> dict:
    """API 요청 페이로드 생성"""
    return {
        "paramName": search_name,
        "paramEName": "",
        "paramIds": "",
        "paramFree1": "",
        "paramFree2": "",
        "paramFree3": "",
        "paramFree4": "",
        "paramFree5": "",
        "paramFree6": "",
        "paramFree7": "",
        "paramFree8": "",
        "paramFree9": "",
        "paramFree10": "",
        "paramFree11": "",
        "paramFree12": "",
        "paramRange": "",
        "paramRange1": "",
        "paramRange2": "",
        "paramRange3": "",
        "paramRvname": "",
        "paramSection1": "",
        "paramSection2": "",
        "paramSection3": "",
        "paramSection4": "",
        "paramRvname2": "",
        "paramCoreChk": "",
        "paramCarNum": "",
        "paramGJeon": "",
        "paramLastSchool": "",
        "paramOffName": "",
        "paramGJeon1": "",
        "paramCvname": "",
        "paramCvname1": "",
        "paramState": "",
        "paramState1": "",
        "paramState3": "",
        "encryptOpt": "ALL",
        "rangeLimitUse": "false",  # false로 설정하여 전체 조회
        "paramPage": str(page),
        "paramPageSize": str(page_size),
        "paramOrder": "NAME",
        "paramOrder2": "",
        "paramOrderAsc": "ASC",
        "paramOrder2Asc": "ASC",
        "paramPType": "P",
        "paramAddr": "",
        "paramRegDateS": "",
        "paramRegDateE": "",
    }


def fetch_page(session: requests.Session, page: int, page_size: int = PAGE_SIZE) -> dict:
    """한 페이지 데이터 가져오기"""
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/WebMobile/WebChurch/RangeList.cshtml",
    }

    payload = create_payload(page=page, page_size=page_size)

    response = session.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()

    # "d" 필드 안에 JSON 문자열이 들어있음
    if "d" in data:
        inner_data = json.loads(data["d"])
        return inner_data

    return data


def crawl_all(cookies: dict = None) -> list:
    """전체 교적 크롤링"""
    if cookies is None:
        cookies = COOKIES

    # 쿠키 검증
    if "여기에" in str(cookies.values()):
        print("❌ 오류: 쿠키를 설정해주세요!")
        print("   브라우저 F12 → Application → Cookies에서 쿠키 값을 복사하세요.")
        return []

    session = requests.Session()
    session.cookies.update(cookies)

    all_persons = []
    page = 1

    # 첫 페이지로 전체 개수 확인
    print("🔍 전체 교인 수 확인 중...")
    first_page = fetch_page(session, page=1, page_size=PAGE_SIZE)

    total_count = int(first_page.get("totalcount", 0))
    total_pages = int(first_page.get("totalpage", 1))

    print(f"📊 전체 교인: {total_count}명, 총 페이지: {total_pages}")

    # 첫 페이지 데이터 추가
    persons = first_page.get("personInfo", [])
    all_persons.extend(persons)
    print(f"   페이지 1/{total_pages} 완료 ({len(persons)}명)")

    # 나머지 페이지 크롤링
    for page in range(2, total_pages + 1):
        time.sleep(DELAY_BETWEEN_PAGES)

        try:
            page_data = fetch_page(session, page=page, page_size=PAGE_SIZE)
            persons = page_data.get("personInfo", [])
            all_persons.extend(persons)
            print(f"   페이지 {page}/{total_pages} 완료 ({len(persons)}명)")
        except Exception as e:
            print(f"   ⚠️ 페이지 {page} 오류: {e}")
            continue

    print(f"\n✅ 크롤링 완료: 총 {len(all_persons)}명")
    return all_persons


def save_to_csv(persons: list, filename: str = None) -> str:
    """CSV 파일로 저장"""
    if not persons:
        print("❌ 저장할 데이터가 없습니다.")
        return None

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"교적_{timestamp}.csv"

    output_path = Path(__file__).parent / filename

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # 헤더 작성
        headers = [display_name for _, display_name in OUTPUT_FIELDS]
        writer.writerow(headers)

        # 데이터 작성
        for person in persons:
            row = [person.get(field_name, "") or "" for field_name, _ in OUTPUT_FIELDS]
            writer.writerow(row)

    print(f"💾 저장 완료: {output_path}")
    return str(output_path)


def save_to_json(persons: list, filename: str = None) -> str:
    """JSON 파일로 저장"""
    if not persons:
        print("❌ 저장할 데이터가 없습니다.")
        return None

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"교적_{timestamp}.json"

    output_path = Path(__file__).parent / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(persons, f, ensure_ascii=False, indent=2)

    print(f"💾 저장 완료: {output_path}")
    return str(output_path)


def main():
    """메인 실행"""
    print("=" * 50)
    print("🏛️  교적 크롤링 시작")
    print("=" * 50)

    # 크롤링 실행
    persons = crawl_all()

    if persons:
        # CSV 저장
        save_to_csv(persons)

        # JSON도 저장 (선택)
        save_to_json(persons)

    print("\n" + "=" * 50)
    print("🎉 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()

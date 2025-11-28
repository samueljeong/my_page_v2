"""
Validate Step 1 Script Output
Step1 대본 출력 JSON 검증
"""

import json
import re
from pathlib import Path
from typing import Tuple, List

import jsonschema
from jsonschema import validate, ValidationError


def load_schema():
    """Step1 스키마 로드"""
    schema_path = Path(__file__).parent.parent / "config" / "step1_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_script(script: dict) -> Tuple[bool, List[str]]:
    """
    대본 JSON 검증

    Args:
        script: 검증할 대본 JSON

    Returns:
        Tuple[bool, List[str]]: (검증 성공 여부, 오류 메시지 목록)
    """
    errors = []

    # 1. JSON 스키마 검증
    schema = load_schema()
    try:
        validate(instance=script, schema=schema)
    except ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")

    # 2. 비즈니스 규칙 검증
    business_errors = validate_business_rules(script)
    errors.extend(business_errors)

    # 3. 콘텐츠 품질 검증
    quality_errors = validate_content_quality(script)
    errors.extend(quality_errors)

    return len(errors) == 0, errors


def validate_business_rules(script: dict) -> List[str]:
    """
    비즈니스 규칙 검증

    Args:
        script: 검증할 대본 JSON

    Returns:
        List[str]: 오류 메시지 목록
    """
    errors = []

    # 주인공 나이 검증
    characters = script.get("characters", [])
    for char in characters:
        if char.get("role") == "주인공":
            age_str = char.get("age", "")
            age = extract_age_number(age_str)
            if age and (age < 60 or age > 85):
                errors.append(f"주인공 나이가 60-85세 범위를 벗어남: {age_str}")

    # 금지된 이름 검증
    forbidden_names = ["지선", "민수", "영희", "철수", "수진", "민지", "현수", "지영", "준호", "미영", "영수", "정희", "미숙", "순자", "옥순", "말자", "길동"]
    for char in characters:
        name = char.get("name", "")
        for forbidden in forbidden_names:
            if forbidden in name:
                errors.append(f"금지된 이름 사용: {name}")

    # 하이라이트 존재 검증
    highlight = script.get("highlight", {})
    if not highlight.get("scenes"):
        errors.append("하이라이트 씬이 없습니다")

    # 씬 개수 검증
    metadata = script.get("metadata", {})
    scenes = script.get("script", {}).get("scenes", [])
    if len(scenes) != metadata.get("total_scenes", 0):
        errors.append(f"씬 개수 불일치: metadata={metadata.get('total_scenes')}, actual={len(scenes)}")

    return errors


def validate_content_quality(script: dict) -> List[str]:
    """
    콘텐츠 품질 검증

    Args:
        script: 검증할 대본 JSON

    Returns:
        List[str]: 오류 메시지 목록
    """
    errors = []

    # 전체 나레이션 추출
    all_narration = ""
    scenes = script.get("script", {}).get("scenes", [])
    for scene in scenes:
        all_narration += scene.get("narration", "") + "\n"

    highlight = script.get("highlight", {})
    for hl_scene in highlight.get("scenes", []):
        all_narration += hl_scene.get("preview_text", "") + "\n"

    # 글자수 검증
    metadata = script.get("metadata", {})
    target_length = metadata.get("target_length", 3000)
    actual_length = len(all_narration.replace(" ", "").replace("\n", ""))

    # 허용 범위: 목표의 80% ~ 120%
    if actual_length < target_length * 0.8:
        errors.append(f"글자수 부족: 목표={target_length}, 실제={actual_length}")
    elif actual_length > target_length * 1.2:
        errors.append(f"글자수 초과: 목표={target_length}, 실제={actual_length}")

    # 숫자 표현 검증 (아라비아 숫자 사용 여부)
    arabic_numbers = re.findall(r'\d+', all_narration)
    # 일부 허용되는 숫자 (연도 등)는 제외
    problematic_numbers = [n for n in arabic_numbers if len(n) < 4]  # 4자리 미만 숫자
    if len(problematic_numbers) > 5:  # 5개 초과 시 경고
        errors.append(f"아라비아 숫자 과다 사용: {problematic_numbers[:5]}...")

    # 금지 패턴 검증
    forbidden_patterns = [
        (r'#+ ', "마크다운 헤더"),
        (r'\*\*', "마크다운 볼드"),
        (r'^\s*[-*]\s', "마크다운 리스트"),
        (r'했다\.', "문어체 종결어미")
    ]

    for pattern, name in forbidden_patterns:
        if re.search(pattern, all_narration, re.MULTILINE):
            errors.append(f"금지 패턴 발견: {name}")

    # 구체적 요소 개수 검증
    # 장소명 (시/군/구/동 패턴)
    locations = re.findall(r'[가-힣]+(?:시|군|구|동|면|읍|리)', all_narration)
    if len(set(locations)) < 2:
        errors.append(f"구체적 장소명 부족: {len(set(locations))}개")

    return errors


def extract_age_number(age_str: str) -> int:
    """
    나이 문자열에서 숫자 추출

    Args:
        age_str: 나이 문자열 (예: "일흔여섯 살", "76세")

    Returns:
        int: 나이 숫자
    """
    # 아라비아 숫자
    match = re.search(r'(\d+)', age_str)
    if match:
        return int(match.group(1))

    # 한글 숫자 변환
    korean_to_num = {
        "열": 10, "스물": 20, "서른": 30, "마흔": 40, "쉰": 50,
        "예순": 60, "일흔": 70, "여든": 80, "아흔": 90,
        "하나": 1, "둘": 2, "셋": 3, "넷": 4, "다섯": 5,
        "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9,
        "한": 1, "두": 2, "세": 3, "네": 4
    }

    total = 0
    for korean, num in korean_to_num.items():
        if korean in age_str:
            total += num

    return total if total > 0 else None


def validate_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    파일에서 대본을 로드하여 검증

    Args:
        file_path: 대본 JSON 파일 경로

    Returns:
        Tuple[bool, List[str]]: (검증 성공 여부, 오류 메시지 목록)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    return validate_script(script)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        is_valid, errors = validate_file(file_path)

        if is_valid:
            print("Validation passed!")
        else:
            print("Validation failed:")
            for error in errors:
                print(f"  - {error}")
    else:
        print("Usage: python validate_step1.py <script_file.json>")

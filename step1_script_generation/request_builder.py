"""
Request Builder for Step 1 Script Generation
카테고리와 영상 길이를 입력받아 대본 생성 요청 JSON을 구성
"""

import json
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def load_categories():
    """카테고리 설정 로드"""
    with open(CONFIG_DIR / "categories.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt_template():
    """Step1 프롬프트 템플릿 로드"""
    prompt_path = Path(__file__).parent / "step1_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_script_request(
    category1: str,
    category2: str,
    duration: str,
    protagonist_info: dict = None,
    custom_theme: str = None,
    test_mode: bool = False
) -> dict:
    """
    대본 생성 요청 JSON 구성

    Args:
        category1: 대분류 (testimony/drama/nostalgia)
        category2: 소분류 (faith_recovery/family_reconciliation 등)
        duration: 영상 길이 (2min/5min/10min/20min/30min)
        protagonist_info: 주인공 정보 (선택)
        custom_theme: 커스텀 테마/주제 (선택)
        test_mode: 테스트 모드 여부

    Returns:
        dict: 대본 생성 요청 JSON
    """
    categories = load_categories()

    # 유효성 검사
    if category1 not in categories["category1"]["options"]:
        raise ValueError(f"Invalid category1: {category1}")

    if category2 not in categories["category2"]["options"]:
        raise ValueError(f"Invalid category2: {category2}")

    if duration not in categories["duration_options"]:
        raise ValueError(f"Invalid duration: {duration}")

    # 카테고리 정보
    cat1_info = categories["category1"]["options"][category1]
    cat2_info = categories["category2"]["options"][category2]
    duration_info = categories["duration_options"][duration]

    # 요청 ID 생성
    request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 요청 JSON 구성
    request = {
        "request_id": request_id,
        "created_at": datetime.now().isoformat(),
        "test_mode": test_mode,

        "content_config": {
            "category1": {
                "code": category1,
                "korean": cat1_info["korean"],
                "description": cat1_info["description"]
            },
            "category2": {
                "code": category2,
                "korean": cat2_info["korean"],
                "description": cat2_info["description"]
            },
            "duration": {
                "code": duration,
                "minutes": duration_info["minutes"],
                "target_length": duration_info["target_length"]
            }
        },

        "script_requirements": {
            "target_length": duration_info["target_length"],
            "max_characters": get_max_characters(duration),
            "max_scenes": get_max_scenes(duration),
            "highlight_scenes": get_highlight_scenes(duration),
            "images_per_scene": get_images_per_scene(duration)
        },

        "protagonist_info": protagonist_info or {
            "age_range": "60-85",
            "gender": "random",
            "generate_automatically": True
        },

        "custom_theme": custom_theme,

        "output_format": "json",
        "schema_version": "1.0"
    }

    return request


def get_max_characters(duration: str) -> int:
    """영상 길이에 따른 최대 등장인물 수"""
    mapping = {
        "2min": 1,
        "5min": 2,
        "10min": 2,
        "20min": 3,
        "30min": 4
    }
    return mapping.get(duration, 2)


def get_max_scenes(duration: str) -> int:
    """영상 길이에 따른 최대 씬 수"""
    mapping = {
        "2min": 2,
        "5min": 3,
        "10min": 4,
        "20min": 6,
        "30min": 8
    }
    return mapping.get(duration, 4)


def get_highlight_scenes(duration: str) -> int:
    """영상 길이에 따른 하이라이트 씬 수"""
    mapping = {
        "2min": 1,
        "5min": 1,
        "10min": 2,
        "20min": 3,
        "30min": 3
    }
    return mapping.get(duration, 2)


def get_images_per_scene(duration: str) -> str:
    """영상 길이에 따른 씬당 이미지 수"""
    mapping = {
        "2min": "1",
        "5min": "1-2",
        "10min": "1-2",
        "20min": "1-2",
        "30min": "1-2"
    }
    return mapping.get(duration, "1-2")


def build_user_prompt(request: dict) -> str:
    """
    사용자 프롬프트 생성

    Args:
        request: build_script_request로 생성된 요청 JSON

    Returns:
        str: Claude API에 전달할 사용자 프롬프트
    """
    config = request["content_config"]
    reqs = request["script_requirements"]
    protagonist = request.get("protagonist_info", {})

    prompt_parts = [
        f"## 콘텐츠 요청",
        f"",
        f"**대분류**: {config['category1']['korean']} ({config['category1']['code']})",
        f"**소분류**: {config['category2']['korean']} ({config['category2']['code']})",
        f"**영상 길이**: {config['duration']['minutes']}분",
        f"**목표 글자수**: {reqs['target_length']}자",
        f"",
        f"## 대본 요구사항",
        f"",
        f"- 최대 등장인물: {reqs['max_characters']}명",
        f"- 최대 씬 개수: {reqs['max_scenes']}개",
        f"- 하이라이트 씬: {reqs['highlight_scenes']}개",
        f"",
    ]

    # 주인공 정보 추가
    if protagonist and not protagonist.get("generate_automatically"):
        prompt_parts.extend([
            f"## 주인공 정보",
            f"",
            f"- 나이: {protagonist.get('age', '60-85세')}",
            f"- 성별: {protagonist.get('gender', '지정 안 함')}",
            f"- 직업: {protagonist.get('occupation', '자동 생성')}",
            f"- 거주지: {protagonist.get('location', '자동 생성')}",
            f"",
        ])

    # 커스텀 테마 추가
    if request.get("custom_theme"):
        prompt_parts.extend([
            f"## 커스텀 테마/주제",
            f"",
            f"{request['custom_theme']}",
            f"",
        ])

    prompt_parts.extend([
        f"위 요구사항에 맞는 대본을 JSON 형식으로 생성해주세요.",
        f"반드시 지정된 스키마를 따라주세요."
    ])

    return "\n".join(prompt_parts)


if __name__ == "__main__":
    # 테스트
    request = build_script_request(
        category1="testimony",
        category2="faith_recovery",
        duration="10min",
        test_mode=True
    )
    print(json.dumps(request, ensure_ascii=False, indent=2))

"""
Call Sonnet API for Script Generation
Claude Sonnet 4.5를 사용하여 대본 생성
"""

import os
import json
import anthropic
from pathlib import Path
from datetime import datetime
from typing import Optional

from .request_builder import build_script_request, build_user_prompt, load_prompt_template


def get_model_config():
    """모델 설정 로드"""
    config_path = Path(__file__).parent.parent / "config" / "model_presets.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["step1_script_generation"]


def generate_script(
    category1: str,
    category2: str,
    duration: str,
    protagonist_info: dict = None,
    custom_theme: str = None,
    model: str = "sonnet",
    test_mode: bool = False,
    api_key: str = None
) -> dict:
    """
    대본 생성 메인 함수

    Args:
        category1: 대분류 (testimony/drama/nostalgia)
        category2: 소분류
        duration: 영상 길이
        protagonist_info: 주인공 정보 (선택)
        custom_theme: 커스텀 테마 (선택)
        model: 사용할 모델 (sonnet/opus)
        test_mode: 테스트 모드 여부
        api_key: Anthropic API 키 (없으면 환경변수 사용)

    Returns:
        dict: 생성된 대본 JSON
    """
    # 요청 빌드
    request = build_script_request(
        category1=category1,
        category2=category2,
        duration=duration,
        protagonist_info=protagonist_info,
        custom_theme=custom_theme,
        test_mode=test_mode
    )

    # 모델 설정
    model_config = get_model_config()
    model_info = model_config["models"].get(model, model_config["models"]["sonnet"])

    # API 클라이언트 초기화
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # 프롬프트 로드
    system_prompt = load_prompt_template()
    user_prompt = build_user_prompt(request)

    # API 호출
    response = client.messages.create(
        model=model_info["model_id"],
        max_tokens=model_info["max_tokens"],
        temperature=model_info["temperature"],
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    # 응답 파싱
    content = response.content[0].text

    # JSON 추출
    script_json = extract_json_from_response(content)

    # 결과 구성
    result = {
        "request": request,
        "response": {
            "model": model_info["model_id"],
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "generated_at": datetime.now().isoformat()
        },
        "script": script_json
    }

    return result


def extract_json_from_response(content: str) -> dict:
    """
    API 응답에서 JSON 추출

    Args:
        content: API 응답 텍스트

    Returns:
        dict: 추출된 JSON
    """
    import re

    # JSON 블록 찾기
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)

    if json_match:
        json_str = json_match.group(1)
    else:
        # JSON 블록이 없으면 전체 내용에서 JSON 찾기
        # { 로 시작하고 } 로 끝나는 부분
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No JSON found in response")

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")


async def generate_script_async(
    category1: str,
    category2: str,
    duration: str,
    protagonist_info: dict = None,
    custom_theme: str = None,
    model: str = "sonnet",
    test_mode: bool = False,
    api_key: str = None
) -> dict:
    """
    대본 생성 비동기 버전

    Args:
        (generate_script와 동일)

    Returns:
        dict: 생성된 대본 JSON
    """
    import asyncio

    # 동기 함수를 스레드에서 실행
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: generate_script(
            category1=category1,
            category2=category2,
            duration=duration,
            protagonist_info=protagonist_info,
            custom_theme=custom_theme,
            model=model,
            test_mode=test_mode,
            api_key=api_key
        )
    )
    return result


def generate_script_streaming(
    category1: str,
    category2: str,
    duration: str,
    protagonist_info: dict = None,
    custom_theme: str = None,
    model: str = "sonnet",
    test_mode: bool = False,
    api_key: str = None
):
    """
    대본 생성 스트리밍 버전 (제너레이터)

    Args:
        (generate_script와 동일)

    Yields:
        str: 스트리밍 텍스트 청크
    """
    # 요청 빌드
    request = build_script_request(
        category1=category1,
        category2=category2,
        duration=duration,
        protagonist_info=protagonist_info,
        custom_theme=custom_theme,
        test_mode=test_mode
    )

    # 모델 설정
    model_config = get_model_config()
    model_info = model_config["models"].get(model, model_config["models"]["sonnet"])

    # API 클라이언트 초기화
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # 프롬프트 로드
    system_prompt = load_prompt_template()
    user_prompt = build_user_prompt(request)

    # 스트리밍 API 호출
    with client.messages.stream(
        model=model_info["model_id"],
        max_tokens=model_info["max_tokens"],
        temperature=model_info["temperature"],
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    ) as stream:
        for text in stream.text_stream:
            yield text


if __name__ == "__main__":
    # 테스트
    result = generate_script(
        category1="testimony",
        category2="faith_recovery",
        duration="10min",
        test_mode=True
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

"""
Call Sonnet for Step 1
Claude Sonnet 4.5 API 호출 모듈
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


def load_system_prompt() -> str:
    """step1_prompt.txt에서 시스템 프롬프트 로드"""
    prompt_path = Path(__file__).parent / "step1_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"System prompt not found: {prompt_path}")


def generate_script(step1_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Claude Sonnet 4.5를 사용하여 대본 생성

    Args:
        step1_input: Step1 입력 JSON

    Returns:
        Step1 출력 JSON (대본 데이터)
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    category = step1_input.get("category", "category1")
    mode = step1_input.get("mode", "test")
    length_minutes = step1_input.get("length_minutes", 1)

    print(f"[Step1] Category: {category}")
    print(f"[Step1] Mode: {mode}")
    print(f"[Step1] Length: {length_minutes} minutes")

    if not api_key:
        print("[WARNING] ANTHROPIC_API_KEY not set. Using mock data.")
        print(f"[SONNET] Would generate script for category: {category}")
        print(f"[SONNET] Mode: {mode}, Length: {length_minutes} min")
        return _generate_mock_output(step1_input)

    # 실제 API 호출
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = load_system_prompt()

        print("[SONNET] Calling Claude Sonnet 4.5...")

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(step1_input, ensure_ascii=False)
                }
            ]
        )

        # 응답에서 JSON 추출
        response_text = response.content[0].text
        print(f"[SONNET] Response received ({len(response_text)} chars)")

        # JSON 파싱
        result = _parse_json_response(response_text)

        # 파이프라인 호환성을 위한 필드 보정
        result = _ensure_pipeline_compatibility(result, step1_input)

        print(f"[SONNET] Script generated: {result.get('titles', {}).get('main_title', 'Unknown')}")
        return result

    except ImportError:
        print("[ERROR] anthropic package not installed. Using mock data.")
        return _generate_mock_output(step1_input)
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        print("[FALLBACK] Using mock data.")
        return _generate_mock_output(step1_input)


def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """응답 텍스트에서 JSON 추출 및 파싱"""
    text = response_text.strip()

    # 마크다운 코드블록 제거
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # JSON 파싱
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing failed: {e}")
        print(f"[DEBUG] Response text: {text[:500]}...")
        raise


def _ensure_pipeline_compatibility(result: Dict[str, Any], step1_input: Dict[str, Any]) -> Dict[str, Any]:
    """파이프라인 호환성을 위한 필드 보정"""
    # step 필드 추가
    if "step" not in result:
        result["step"] = "step1_script"

    # category_key 매핑
    category = result.get("category", step1_input.get("category", "category1"))
    if "category_key" not in result:
        result["category_key"] = "nostalgia_story" if category == "category1" else "wisdom_quotes"

    # narrator 필드 확인
    if "narrator" not in result:
        result["narrator"] = {"gender": "male", "style": "warm"}
    elif "gender" not in result["narrator"]:
        result["narrator"]["gender"] = "male"
    elif "style" not in result["narrator"]:
        result["narrator"]["style"] = "warm"

    # scenes 필드 확인 및 보정
    if "scenes" in result:
        for i, scene in enumerate(result["scenes"]):
            if "id" not in scene:
                scene["id"] = f"scene{i + 1}"
            if "order" not in scene:
                scene["order"] = i + 1
            if "emotion" not in scene:
                scene["emotion"] = "nostalgic"

    # checks 필드 추가
    if "checks" not in result:
        result["checks"] = {
            "total_scenes": len(result.get("scenes", [])),
            "estimated_duration_minutes": step1_input.get("length_minutes", 1),
            "narrator_consistency": True
        }

    return result


def _generate_mock_output(step1_input: Dict[str, Any]) -> Dict[str, Any]:
    """테스트용 Mock 출력 생성"""
    category = step1_input.get("category", "category1")
    length_minutes = step1_input.get("length_minutes", 1)
    scene_count = step1_input.get("force_scene_count", 4)

    # Mock scenes 생성
    scenes = []
    for i in range(scene_count):
        scenes.append({
            "id": f"scene{i + 1}",
            "order": i + 1,
            "narration": f"이것은 씬 {i + 1}의 나레이션입니다. 옛날 시골 마을의 따뜻한 이야기가 펼쳐집니다.",
            "visual_description": f"씬 {i + 1}: 1970년대 시골 마을 풍경",
            "emotion": "nostalgic",
            "narrator": {"gender": "male"}
        })

    return {
        "step": "step1_script",
        "category": category,
        "category_key": "nostalgia_story" if category == "category1" else "wisdom_quotes",
        "meta": {
            "episode_theme": "옛날 시골 마을의 따뜻한 추억 이야기",
            "total_duration_minutes": length_minutes
        },
        "titles": {
            "main_title": "그 시절, 우리 마을의 작은 구멍가게",
            "sub_title": "아버지의 손때 묻은 가게"
        },
        "thumbnail": {
            "description": "1970년대 시골 구멍가게 앞에 서 있는 노인",
            "text_overlay": "그 시절 구멍가게"
        },
        "hook": {
            "text": "여러분은 어린 시절 동네 구멍가게를 기억하시나요?",
            "duration_seconds": 5
        },
        "episode": {
            "number": 1,
            "theme": "향수와 추억"
        },
        "narrator": {
            "gender": "male",
            "style": "warm"
        },
        "scenes": scenes,
        "highlight_preview": {
            "quote": "그때 그 시절이 그립습니다",
            "hashtags": ["향수", "추억", "시골", "옛날이야기", "구멍가게"]
        },
        "checks": {
            "total_scenes": scene_count,
            "estimated_duration_minutes": length_minutes,
            "narrator_consistency": True
        }
    }


if __name__ == "__main__":
    test_input = {
        "step": "step1_script_generation",
        "category": "category1",
        "mode": "test",
        "length_minutes": 1,
        "force_scene_count": 4
    }

    result = generate_script(test_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))

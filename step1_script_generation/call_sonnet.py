"""
Call Sonnet for Step 1
Claude Sonnet 4.5 API 호출 모듈
"""

import os
from typing import Dict, Any


def generate_script(step1_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Claude Sonnet 4.5를 사용하여 대본 생성

    Args:
        step1_input: Step1 입력 JSON

    Returns:
        Step1 출력 JSON (대본 데이터)
    """
    # TODO: 실제 Anthropic API 호출 구현
    # import anthropic
    # client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # response = client.messages.create(
    #     model="claude-sonnet-4-5-20250929",
    #     max_tokens=8192,
    #     system=load_system_prompt(),
    #     messages=[{"role": "user", "content": json.dumps(step1_input)}]
    # )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[WARNING] ANTHROPIC_API_KEY not set. Using mock data.")

    # Mock 데이터 반환
    category = step1_input.get("category", "category1")
    mode = step1_input.get("mode", "test")
    length_minutes = step1_input.get("length_minutes", 1)

    print(f"[SONNET] Would generate script for category: {category}")
    print(f"[SONNET] Mode: {mode}, Length: {length_minutes} min")

    return _generate_mock_output(step1_input)


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
    import json

    test_input = {
        "category": "category1",
        "mode": "test",
        "length_minutes": 1,
        "force_scene_count": 4
    }

    result = generate_script(test_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))

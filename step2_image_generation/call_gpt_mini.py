"""
Call GPT-4o-mini for Step 2
Image prompt generation module - converts visual_description to English prompts
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List


def load_system_prompt() -> str:
    """Load system prompt from step2_prompt.txt"""
    prompt_path = Path(__file__).parent / "step2_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"System prompt not found: {prompt_path}")


def generate_image_prompts(step1_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use GPT-4o-mini to convert Korean visual_description to English image prompts

    Args:
        step1_output: Step1 script generation result

    Returns:
        Step2 output with scenes_for_image array
    """
    api_key = os.getenv("OPENAI_API_KEY")
    scenes = step1_output.get("scenes", [])

    print(f"[Step2] Processing {len(scenes)} scenes for image prompts")

    if not api_key:
        print("[WARNING] OPENAI_API_KEY not set. Using rule-based conversion.")
        return _generate_rule_based_prompts(step1_output)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        system_prompt = load_system_prompt()

        print("[GPT-MINI] Calling GPT-4o-mini for image prompt generation...")

        input_for_gpt = {
            "scenes": [
                {
                    "id": scene.get("id"),
                    "visual_description": scene.get("visual_description", ""),
                    "emotion": scene.get("emotion", "nostalgic")
                }
                for scene in scenes
            ]
        }

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(input_for_gpt, ensure_ascii=False)}
            ],
            max_tokens=4096,
            temperature=0.7
        )

        response_text = response.choices[0].message.content
        print(f"[GPT-MINI] Response received ({len(response_text)} chars)")

        result = _parse_json_response(response_text)
        return _ensure_pipeline_compatibility(result, step1_output)

    except ImportError:
        print("[ERROR] openai package not installed. Using rule-based conversion.")
        return _generate_rule_based_prompts(step1_output)
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        print("[FALLBACK] Using rule-based conversion.")
        return _generate_rule_based_prompts(step1_output)


def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """Extract and parse JSON from response text"""
    text = response_text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing failed: {e}")
        print(f"[DEBUG] Response text: {text[:500]}...")
        raise


def _ensure_pipeline_compatibility(result: Dict[str, Any], step1_output: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure pipeline compatibility by adding required fields"""
    result["step"] = "step2_images"
    result["category"] = step1_output.get("category", "category1")
    result["category_key"] = step1_output.get("category_key", "nostalgia_story")
    result["title"] = step1_output.get("titles", {}).get("main_title", "Untitled")

    if "scenes_for_image" not in result:
        result["scenes_for_image"] = []

    for scene in result.get("scenes_for_image", []):
        if "scene_id" not in scene and "id" in scene:
            scene["scene_id"] = scene.pop("id")
        if "image_prompt" not in scene:
            scene["image_prompt"] = ""
        if "style" not in scene:
            scene["style"] = "warm retro color palette"
        if "is_key_scene" not in scene:
            scene["is_key_scene"] = True

    result["max_cuts"] = len(result.get("scenes_for_image", []))
    return result


def _generate_rule_based_prompts(step1_output: Dict[str, Any]) -> Dict[str, Any]:
    """Generate image prompts using rule-based conversion (fallback when no API)"""
    scenes = step1_output.get("scenes", [])
    titles = step1_output.get("titles", {})

    scenes_for_image: List[Dict[str, Any]] = []

    for scene in scenes[:4]:
        scene_id = scene.get("id", f"scene{len(scenes_for_image) + 1}")
        visual_desc = scene.get("visual_description", "")
        emotion = scene.get("emotion", "nostalgic")

        image_prompt = _convert_to_english_prompt(visual_desc, emotion)
        style = _get_style_tag(emotion)
        seed_hint = f"{scene_id} {emotion} korea 1970s warm tone"

        scenes_for_image.append({
            "scene_id": scene_id,
            "image_prompt": image_prompt,
            "style": style,
            "seed_hint": seed_hint,
            "is_key_scene": True
        })

    return {
        "step": "step2_images",
        "category": step1_output.get("category", "category1"),
        "category_key": step1_output.get("category_key", "nostalgia_story"),
        "title": titles.get("main_title", "Untitled"),
        "scenes_for_image": scenes_for_image,
        "max_cuts": len(scenes_for_image)
    }


def _convert_to_english_prompt(visual_desc: str, emotion: str) -> str:
    """Convert Korean visual_description to English prompt (rule-based)"""
    base_elements = [
        "1970s Korean village scene",
        "warm nostalgic atmosphere",
        "soft film grain",
        "cinematic wide shot"
    ]

    lighting_map = {
        "nostalgia": "soft warm lighting, sunset glow",
        "warmth": "golden-hour light, diffused soft shadows",
        "bittersweet": "cool ambient light mixed with warm highlights",
        "comfort": "warm indoor lighting, gentle shadows"
    }

    lighting = lighting_map.get(emotion, "soft warm lighting")

    keyword_map = {
        "시골": "rural Korean village",
        "마을": "small Korean town",
        "골목": "narrow Korean alley",
        "버스": "old Korean bus",
        "학교": "old Korean school",
        "시장": "traditional Korean market",
        "구멍가게": "old Korean general store",
        "연탄": "coal briquettes stacked near doorsteps",
        "겨울": "winter scene with visible breath in cold air",
        "새벽": "early dawn, quiet streets",
        "저녁": "evening twilight",
        "1970": "1970s Korea",
        "1980": "1980s Korea"
    }

    matched_elements = []
    for kor, eng in keyword_map.items():
        if kor in visual_desc:
            matched_elements.append(eng)

    if matched_elements:
        scene_desc = ", ".join(matched_elements[:3])
    else:
        scene_desc = "nostalgic 1970s Korean neighborhood"

    prompt = f"{scene_desc}, {lighting}, {', '.join(base_elements)}"
    return prompt


def _get_style_tag(emotion: str) -> str:
    """Get style tag based on emotion"""
    style_map = {
        "nostalgia": "soft nostalgic illustration",
        "warmth": "warm retro color palette",
        "bittersweet": "film still aesthetic",
        "comfort": "vintage Korean realism"
    }
    return style_map.get(emotion, "warm retro color palette")


if __name__ == "__main__":
    mock_step1 = {
        "category": "category1",
        "category_key": "nostalgia_story",
        "titles": {"main_title": "Test Title"},
        "scenes": [
            {
                "id": "scene1",
                "visual_description": "1970s rural village store",
                "emotion": "nostalgia"
            }
        ]
    }

    result = generate_image_prompts(mock_step1)
    print(json.dumps(result, ensure_ascii=False, indent=2))

"""
한국사 파이프라인 - 이미지 생성 모듈 (Gemini Imagen)

- 씬 배경 이미지 생성
- 썸네일 이미지 생성
- 독립 실행 가능 (외부 의존성 없음)
"""

import os
import base64
import requests
from typing import Dict, Any, List


# Gemini 모델
GEMINI_FLASH = "gemini-2.0-flash-exp"  # 빠르고 저렴
GEMINI_PRO = "imagen-3.0-generate-002"  # 고품질 이미지


def generate_image(
    prompt: str,
    output_path: str = None,
    style: str = "realistic",
    aspect_ratio: str = "16:9",
    model: str = GEMINI_PRO,
) -> Dict[str, Any]:
    """
    Gemini Imagen으로 이미지 생성

    Args:
        prompt: 이미지 프롬프트 (영문 권장)
        output_path: 저장 경로 (없으면 base64 반환)
        style: 스타일 힌트
        aspect_ratio: 비율 (16:9, 1:1, 9:16)
        model: 모델 ID

    Returns:
        {"ok": True, "image_path": "...", "image_data": bytes}
    """
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return {"ok": False, "error": "GOOGLE_API_KEY 환경변수가 설정되지 않았습니다."}

    # Imagen API URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateImages?key={api_key}"

    # 스타일 힌트 추가
    style_hints = {
        "realistic": "photorealistic, highly detailed, 8k resolution",
        "illustration": "digital illustration, artistic, detailed",
        "cinematic": "cinematic lighting, dramatic atmosphere, film quality",
        "historical": "historical illustration, traditional art style, detailed",
    }
    style_suffix = style_hints.get(style, style_hints["realistic"])
    enhanced_prompt = f"{prompt}, {style_suffix}"

    payload = {
        "prompt": enhanced_prompt,
        "config": {
            "numberOfImages": 1,
            "aspectRatio": aspect_ratio,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=120)

        if response.status_code == 200:
            result = response.json()

            # 이미지 데이터 추출
            images = result.get("generatedImages", [])
            if images:
                image_data = base64.b64decode(images[0].get("image", {}).get("imageBytes", ""))

                if output_path:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"[HISTORY-IMAGE] 저장: {output_path}")
                    return {"ok": True, "image_path": output_path, "image_data": image_data}
                else:
                    return {"ok": True, "image_data": image_data}
            else:
                return {"ok": False, "error": "이미지 생성 결과 없음"}
        else:
            error_text = response.text[:300]
            print(f"[HISTORY-IMAGE] API 오류: {response.status_code} - {error_text}")
            return {"ok": False, "error": f"API 오류: {response.status_code}"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def generate_scene_images(
    episode_id: str,
    prompts: List[Dict[str, Any]],
    output_dir: str,
    style: str = "historical",
) -> Dict[str, Any]:
    """
    여러 씬 이미지 일괄 생성

    Args:
        episode_id: 에피소드 ID (예: "ep019")
        prompts: [{"scene_index": 1, "prompt": "..."}, ...]
        output_dir: 출력 디렉토리
        style: 스타일

    Returns:
        {"ok": True, "images": [{"scene_index": 1, "path": "..."}], "failed": [...]}
    """
    os.makedirs(output_dir, exist_ok=True)

    results = {"ok": True, "images": [], "failed": []}

    for i, item in enumerate(prompts):
        scene_index = item.get("scene_index", i + 1)
        prompt = item.get("prompt", "")

        if not prompt:
            continue

        output_path = os.path.join(output_dir, f"{episode_id}_scene_{scene_index:02d}.png")

        print(f"[HISTORY-IMAGE] 씬 {scene_index}/{len(prompts)} 생성 중...")
        result = generate_image(
            prompt=prompt,
            output_path=output_path,
            style=style,
        )

        if result.get("ok"):
            results["images"].append({
                "scene_index": scene_index,
                "path": result["image_path"],
            })
        else:
            results["failed"].append({
                "scene_index": scene_index,
                "error": result.get("error"),
            })

    if results["failed"]:
        results["ok"] = len(results["images"]) > 0  # 부분 성공 허용

    print(f"[HISTORY-IMAGE] 완료: {len(results['images'])}개 성공, {len(results['failed'])}개 실패")
    return results


def generate_thumbnail(
    episode_id: str,
    title: str,
    subtitle: str = "",
    output_dir: str = None,
    background_prompt: str = None,
) -> Dict[str, Any]:
    """
    썸네일 이미지 생성

    Args:
        episode_id: 에피소드 ID
        title: 메인 타이틀
        subtitle: 서브 타이틀
        output_dir: 출력 디렉토리
        background_prompt: 배경 이미지 프롬프트

    Returns:
        {"ok": True, "image_path": "..."}
    """
    if not background_prompt:
        background_prompt = f"Epic historical scene for YouTube thumbnail about {title}, dramatic lighting, cinematic composition"

    output_path = os.path.join(output_dir or ".", f"{episode_id}_thumbnail.png")

    return generate_image(
        prompt=background_prompt,
        output_path=output_path,
        style="cinematic",
        aspect_ratio="16:9",
    )


if __name__ == "__main__":
    print("history_pipeline/image_gen.py 로드 완료")

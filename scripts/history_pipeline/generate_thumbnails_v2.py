"""
한국사 썸네일 생성 스크립트 (B스타일: 호기심형)

스타일 특징:
- 흰색 제목 + 검정 테두리(stroke)
- 노란색 부제
- 친근한 캐릭터 (호기심/당황 표정)
"""

import os
import sys

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PIL import Image, ImageDraw, ImageFont
from image.gemini import generate_image


# 폰트 설정
FONT_PATH = "assets/fonts/black_han_sans.ttf"

# 색상 설정
TITLE_COLOR = (255, 255, 255)  # 흰색
STROKE_COLOR = (0, 0, 0)  # 검정
SUBTITLE_COLOR = (255, 220, 80)  # 노란색/금색


def add_text_with_stroke(draw, text, position, font, fill_color, stroke_color, stroke_width=8):
    """텍스트에 테두리(stroke) 효과 추가"""
    x, y = position

    # 테두리 그리기 (8방향)
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)

    # 본문 텍스트
    draw.text(position, text, font=font, fill=fill_color)


def create_thumbnail_v2(
    background_path: str,
    title: str,
    subtitle: str,
    output_path: str,
    title_size_ratio: float = 0.13,
    subtitle_size_ratio: float = 0.06,
):
    """B스타일 썸네일 생성"""

    # 배경 이미지 로드
    img = Image.open(background_path).convert("RGBA")
    width, height = img.size

    draw = ImageDraw.Draw(img)

    # 폰트 크기 계산
    title_font_size = int(height * title_size_ratio)
    subtitle_font_size = int(height * subtitle_size_ratio)

    title_font = ImageFont.truetype(FONT_PATH, title_font_size)
    subtitle_font = ImageFont.truetype(FONT_PATH, subtitle_font_size)

    # 제목 위치 (왼쪽 상단)
    title_x = int(width * 0.05)
    title_y = int(height * 0.15)

    # 제목이 2줄인 경우 처리
    title_lines = title.split("\n") if "\n" in title else [title]

    current_y = title_y
    for line in title_lines:
        add_text_with_stroke(
            draw, line, (title_x, current_y),
            title_font, TITLE_COLOR, STROKE_COLOR, stroke_width=8
        )
        bbox = title_font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        current_y += line_height + int(height * 0.02)

    # 부제 위치 (제목 아래)
    subtitle_y = current_y + int(height * 0.02)
    add_text_with_stroke(
        draw, subtitle, (title_x, subtitle_y),
        subtitle_font, SUBTITLE_COLOR, STROKE_COLOR, stroke_width=5
    )

    # 저장
    img = img.convert("RGB")
    img.save(output_path, "JPEG", quality=95)
    print(f"[THUMBNAIL] 저장 완료: {output_path}")

    return output_path


def generate_thumbnail_background(prompt: str, output_dir: str, filename: str) -> str:
    """Gemini로 썸네일 배경 이미지 생성"""

    os.makedirs(output_dir, exist_ok=True)

    result = generate_image(
        prompt=prompt,
        size="1280x720",
        output_dir=output_dir,
        add_aspect_instruction=True
    )

    if result.get("ok"):
        # 파일명 변경
        original_path = result["image_url"].replace("/static/", "static/")
        new_path = os.path.join(output_dir, filename)

        if os.path.exists(original_path):
            os.rename(original_path, new_path)
            print(f"[GEMINI] 배경 생성 완료: {new_path}")
            return new_path
        else:
            print(f"[ERROR] 파일 없음: {original_path}")
            return None
    else:
        print(f"[ERROR] 이미지 생성 실패: {result.get('error')}")
        return None


# 에피소드별 썸네일 설정
THUMBNAILS = {
    19: {
        "title": "발해\n고구려를 잇다",
        "subtitle": "해동성국의 228년",
        "prompt": """Korean webtoon style illustration for YouTube thumbnail, 16:9 aspect ratio.
Scene: Heroic young Korean general (Dae Jo-young) in Goguryeo-style armor standing on mountain peak, looking determined at sunrise.
Background: Vast Manchurian plains with fortress in distance, morning mist.
Character on right side of image, left side should have space for text overlay.
Style: Clean line art, warm colors, Studio Ghibli meets modern illustration, friendly and accessible.
Character should have curious/determined expression, NOT scary or aggressive."""
    },
    20: {
        "title": "후삼국\n셋으로 갈라지다",
        "subtitle": "궁예, 견훤, 왕건의 시대",
        "prompt": """Korean webtoon style illustration for YouTube thumbnail, 16:9 aspect ratio.
Scene: Three Korean historical figures (warriors/kings) facing each other in dramatic standoff, Korean traditional clothing and armor.
Background: Korean mountain landscape at sunset, ancient fortress visible.
Characters positioned on right side, left side should have space for text overlay.
Style: Clean line art, warm colors, Studio Ghibli meets modern illustration, friendly and accessible.
One character in center should have surprised/curious expression, creating intrigue."""
    }
}


def main():
    """19-20화 썸네일 생성"""

    output_dir = "static/images/thumbnails"
    os.makedirs(output_dir, exist_ok=True)

    for ep_num, config in THUMBNAILS.items():
        print(f"\n{'='*50}")
        print(f"에피소드 {ep_num}화 썸네일 생성")
        print(f"{'='*50}")

        # 1. 배경 이미지 생성
        bg_filename = f"ep{ep_num:03d}_bg.jpg"
        bg_path = os.path.join(output_dir, bg_filename)

        if not os.path.exists(bg_path):
            bg_path = generate_thumbnail_background(
                prompt=config["prompt"],
                output_dir=output_dir,
                filename=bg_filename
            )

            if not bg_path:
                print(f"[ERROR] {ep_num}화 배경 생성 실패")
                continue
        else:
            print(f"[SKIP] 배경 이미지 이미 존재: {bg_path}")

        # 2. 텍스트 오버레이
        final_filename = f"ep{ep_num:03d}_thumbnail_v2.jpg"
        final_path = os.path.join(output_dir, final_filename)

        create_thumbnail_v2(
            background_path=bg_path,
            title=config["title"],
            subtitle=config["subtitle"],
            output_path=final_path
        )

        print(f"[완료] {ep_num}화 썸네일: {final_path}")


if __name__ == "__main__":
    main()

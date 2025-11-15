"""
묵상 비디오 생성 테스트
"""

from PIL import Image, ImageDraw
from shorts_maker import ShortsMaker

# 1. 간단한 그라데이션 배경 생성
def create_gradient_background(width, height, color1, color2):
    """세로 그라데이션 배경 생성"""
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

# 2. 배경 이미지 생성
print("Creating gradient background...")
bg = create_gradient_background(
    1080,
    1920,
    (30, 60, 90),     # 어두운 파란색
    (150, 100, 150)   # 보라색
)
bg.save("output/images/video_bg.jpg", quality=95)
print("✅ Background saved: output/images/video_bg.jpg")

# 3. 묵상 비디오 생성
print("\nCreating devotional video (10 seconds)...")
maker = ShortsMaker()

test_message = "주님의 은혜가 오늘도 함께 하시기를 기도합니다. 평안한 하루 되세요."
test_ref = "시편 23:1"

result = maker.create_devotional_video(
    "output/images/video_bg.jpg",
    test_message,
    "output/videos/test_devotional.mp4",
    test_ref,
    duration=10  # 10초
)

if result:
    import os
    file_size = os.path.getsize(result) / 1024  # KB
    print(f"✅ Devotional video created: {result}")
    print(f"   File size: {file_size:.1f} KB")
    print(f"\n🎬 비디오가 생성되었습니다!")
    print(f"   경로: {result}")
else:
    print("❌ Failed to create devotional video")

"""
이세계 파이프라인 - TTS 모듈 (Chirp3 HD - API Key 방식)

- Google Cloud TTS Chirp3 HD (고품질 한국어)
- GOOGLE_API_KEY 또는 GOOGLE_CLOUD_API_KEY 환경변수 사용
- REST API 방식 (서비스 계정 불필요)
- 씬/감정별 속도 조절 지원
"""

import os
import re
import json
import base64
import subprocess
import tempfile
import time
import requests
from typing import Dict, Any, List, Tuple, Optional


# TTS 설정
DEFAULT_VOICE = "ko-KR-Chirp3-HD-Charon"  # Chirp3 HD 남성
TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

# 감정별 TTS 속도 설정 (0.25 ~ 4.0)
EMOTION_SPEED = {
    "nostalgic": 0.92,    # 회상: 느리고 감성적
    "sad": 0.88,          # 슬픔: 천천히
    "calm": 0.95,         # 평화: 여유롭게
    "romantic": 0.90,     # 로맨스: 부드럽게
    "tense": 1.05,        # 긴장: 약간 빠르게
    "fight": 1.10,        # 전투: 빠르게
    "epic": 1.02,         # 웅장: 약간 빠르게
    "dramatic": 0.95,     # 극적: 느리게
    "mysterious": 0.93,   # 신비: 느리게
    "hopeful": 0.98,      # 희망: 보통
    "default": 1.0,       # 기본
}

# 씬 마커 정규식: [SCENE:씬이름:감정:BGM]
SCENE_MARKER_PATTERN = re.compile(r'\[SCENE:([^:]+):([^:]+):([^\]]+)\]')


def parse_scenes(script: str) -> List[Dict[str, Any]]:
    """
    대본에서 씬 마커를 파싱하여 씬 목록 반환

    씬 마커 형식: [SCENE:씬이름:감정:BGM]
    예: [SCENE:오프닝:nostalgic:nostalgic]

    Returns:
        [{"name": "오프닝", "emotion": "nostalgic", "bgm": "nostalgic", "text": "..."}]
    """
    scenes = []
    parts = SCENE_MARKER_PATTERN.split(script)

    # parts: [텍스트전, 씬이름1, 감정1, BGM1, 텍스트1, 씬이름2, ...]
    if len(parts) == 1:
        # 씬 마커 없음 - 전체를 하나의 기본 씬으로
        return [{"name": "default", "emotion": "default", "bgm": "calm", "text": script.strip()}]

    # 첫 번째 텍스트 (마커 이전)
    if parts[0].strip():
        scenes.append({
            "name": "intro",
            "emotion": "default",
            "bgm": "calm",
            "text": parts[0].strip()
        })

    # 나머지 파싱 (4개씩: 씬이름, 감정, BGM, 텍스트)
    i = 1
    while i + 3 <= len(parts):
        scene_name = parts[i].strip()
        emotion = parts[i + 1].strip().lower()
        bgm = parts[i + 2].strip().lower()
        text = parts[i + 3].strip() if i + 3 < len(parts) else ""

        if text:
            scenes.append({
                "name": scene_name,
                "emotion": emotion,
                "bgm": bgm,
                "text": text
            })
        i += 4

    return scenes


def split_into_sentences(text: str) -> List[str]:
    """텍스트를 문장 단위로 분할"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def get_audio_duration(audio_path: str) -> float:
    """오디오 파일의 재생 시간(초) 반환"""
    # mutagen 사용 (ffprobe 불필요)
    try:
        from mutagen.mp3 import MP3
        audio = MP3(audio_path)
        return audio.info.length
    except Exception:
        pass

    # fallback: ffprobe
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip()) if result.stdout.strip() else 0.0
    except Exception:
        return 0.0


def merge_audio_files(audio_paths: List[str], output_path: str) -> bool:
    """여러 오디오 파일을 하나로 합침"""
    if not audio_paths:
        return False

    if len(audio_paths) == 1:
        import shutil
        shutil.copy(audio_paths[0], output_path)
        return True

    # 방법 1: pydub 사용 (권장)
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for path in audio_paths:
            audio = AudioSegment.from_mp3(path)
            combined += audio
        combined.export(output_path, format="mp3", bitrate="128k")
        return os.path.exists(output_path)
    except Exception:
        pass

    # 방법 2: ffmpeg concat
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")
            list_path = f.name

        subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_path,
             '-c:a', 'libmp3lame', '-b:a', '128k', output_path],
            capture_output=True, timeout=300
        )
        os.unlink(list_path)
        return os.path.exists(output_path)
    except Exception:
        pass

    # 방법 3: 단순 바이너리 병합 (fallback)
    try:
        with open(output_path, 'wb') as outfile:
            for path in audio_paths:
                with open(path, 'rb') as infile:
                    outfile.write(infile.read())
        return os.path.exists(output_path)
    except Exception:
        return False


def generate_srt(timeline: List[Tuple[float, float, str]], output_path: str):
    """타임라인으로 SRT 파일 생성"""
    def format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (start, end, text) in enumerate(timeline, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")


def generate_chirp3_tts_chunk(
    text: str,
    voice_name: str,
    api_key: str,
    speaking_rate: float = 1.0
) -> Dict[str, Any]:
    """
    Google Cloud TTS REST API로 Chirp3 HD 청크 생성

    Args:
        text: TTS 변환할 텍스트
        voice_name: 음성 이름 (ko-KR-Chirp3-HD-Charon)
        api_key: Google API Key
        speaking_rate: 말하기 속도 (0.25 ~ 4.0, 기본 1.0)

    Returns:
        {"ok": True, "audio_data": bytes} 또는 {"ok": False, "error": "..."}
    """
    url = f"{TTS_API_URL}?key={api_key}"

    # 언어 코드 추출 (ko-KR-Chirp3-HD-Charon → ko-KR)
    lang_code = "-".join(voice_name.split("-")[:2])

    # speaking_rate 범위 제한
    speaking_rate = max(0.25, min(4.0, speaking_rate))

    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": lang_code,
            "name": voice_name
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "sampleRateHertz": 24000,
            "speakingRate": speaking_rate,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            audio_content = result.get("audioContent", "")
            if audio_content:
                audio_data = base64.b64decode(audio_content)
                return {"ok": True, "audio_data": audio_data}
            return {"ok": False, "error": "오디오 데이터 없음"}
        else:
            error_msg = response.text[:300] if response.text else f"HTTP {response.status_code}"
            return {"ok": False, "error": f"TTS API 오류: {error_msg}"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def generate_tts(
    episode_id: str,
    script: str,
    output_dir: str,
    voice: str = "Charon",
    speed: float = 1.0,
) -> Dict[str, Any]:
    """
    대본에 대해 TTS 생성 (Chirp3 HD REST API)
    씬 마커가 있으면 씬별로 감정에 따른 속도 조절

    Args:
        episode_id: 에피소드 ID (예: "ep001")
        script: 대본 텍스트 (씬 마커 포함 가능)
        output_dir: 출력 디렉토리
        voice: 음성 (Charon, Kore, Puck, Fenrir, Aoede)
        speed: 기본 속도 배율 (감정 속도에 곱해짐)

    Returns:
        {
            "ok": True,
            "audio_path": "...",
            "srt_path": "...",
            "duration": 900.5,
            "timeline": [...],
            "scene_timeline": [{"name": "...", "bgm": "...", "start": 0.0, "end": 120.0}]
        }
    """
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GOOGLE_CLOUD_API_KEY')
    if not api_key:
        return {"ok": False, "error": "GOOGLE_API_KEY 환경변수가 필요합니다"}

    os.makedirs(output_dir, exist_ok=True)

    # 음성 이름 생성 (Charon → ko-KR-Chirp3-HD-Charon)
    voice_short = voice.split(":")[-1] if ":" in voice else voice
    valid_voices = ["Kore", "Charon", "Puck", "Fenrir", "Aoede", "Orus", "Leda", "Zephyr"]
    if voice_short not in valid_voices:
        voice_short = "Charon"

    voice_name = f"ko-KR-Chirp3-HD-{voice_short}"
    print(f"[ISEKAI-TTS] 음성: {voice_name}")

    # 씬 파싱
    scenes = parse_scenes(script)
    print(f"[ISEKAI-TTS] {len(scenes)}개 씬 감지")
    for scene in scenes:
        emotion_speed = EMOTION_SPEED.get(scene["emotion"], 1.0)
        print(f"  - {scene['name']}: 감정={scene['emotion']}, BGM={scene['bgm']}, 속도={emotion_speed}")

    audio_paths = []
    timeline = []
    scene_timeline = []
    current_time = 0.0
    failed_count = 0
    chunk_index = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        for scene in scenes:
            scene_start = current_time
            scene_text = scene["text"]
            emotion = scene["emotion"]
            bgm = scene["bgm"]

            # 감정별 속도 계산
            emotion_speed = EMOTION_SPEED.get(emotion, 1.0) * speed
            print(f"[ISEKAI-TTS] 씬 '{scene['name']}' 처리 중 (속도: {emotion_speed:.2f})")

            # 문장 분할
            sentences = split_into_sentences(scene_text)

            # 청크 병합 (5000바이트 ≈ 1400자)
            MAX_CHARS = 1400
            chunks = []
            current_chunk = ""
            current_sentences = []

            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= MAX_CHARS:
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_sentences.append(sentence)
                else:
                    if current_chunk:
                        chunks.append((current_chunk.strip(), list(current_sentences)))
                    current_chunk = sentence
                    current_sentences = [sentence]

            if current_chunk:
                chunks.append((current_chunk.strip(), list(current_sentences)))

            # 씬의 청크들 처리
            for chunk, chunk_sentences in chunks:
                if not chunk:
                    continue

                # TTS 생성 (재시도 포함)
                result = None
                for retry in range(3):
                    result = generate_chirp3_tts_chunk(
                        chunk, voice_name, api_key,
                        speaking_rate=emotion_speed
                    )
                    if result.get("ok"):
                        break
                    time.sleep(1)

                if not result.get("ok"):
                    print(f"[ISEKAI-TTS] 청크 {chunk_index+1} 실패: {result.get('error')}")
                    failed_count += 1
                    if failed_count >= 3:
                        return {"ok": False, "error": f"TTS 연속 실패: {result.get('error')}"}
                    continue

                # MP3 저장
                mp3_path = os.path.join(temp_dir, f"chunk_{chunk_index:04d}.mp3")
                with open(mp3_path, 'wb') as f:
                    f.write(result["audio_data"])

                duration = get_audio_duration(mp3_path)
                if duration > 0:
                    audio_paths.append(mp3_path)

                    total_chars = sum(len(s) for s in chunk_sentences)
                    chunk_start = current_time

                    for sentence in chunk_sentences:
                        sentence_ratio = len(sentence) / total_chars if total_chars > 0 else 1
                        sentence_duration = duration * sentence_ratio
                        timeline.append((chunk_start, chunk_start + sentence_duration, sentence))
                        chunk_start += sentence_duration

                    current_time += duration
                    failed_count = 0

                chunk_index += 1

            # 씬 타임라인 기록
            scene_timeline.append({
                "name": scene["name"],
                "emotion": emotion,
                "bgm": bgm,
                "start": scene_start,
                "end": current_time,
            })

        if not audio_paths:
            return {"ok": False, "error": "TTS 생성 실패"}

        audio_output = os.path.join(output_dir, f"{episode_id}.mp3")
        if not merge_audio_files(audio_paths, audio_output):
            return {"ok": False, "error": "오디오 병합 실패"}

        srt_dir = os.path.join(os.path.dirname(output_dir), "subtitles")
        os.makedirs(srt_dir, exist_ok=True)
        srt_output = os.path.join(srt_dir, f"{episode_id}.srt")
        generate_srt(timeline, srt_output)

        total_duration = get_audio_duration(audio_output)

        # 씬 타임라인 출력
        print(f"[ISEKAI-TTS] 완료: {total_duration:.1f}초, {len(timeline)}개 자막")
        print(f"[ISEKAI-TTS] 씬 타임라인:")
        for st in scene_timeline:
            print(f"  - {st['name']}: {st['start']:.1f}s ~ {st['end']:.1f}s (BGM: {st['bgm']})")

        return {
            "ok": True,
            "audio_path": audio_output,
            "srt_path": srt_output,
            "duration": total_duration,
            "timeline": timeline,
            "scene_timeline": scene_timeline,
        }


if __name__ == "__main__":
    print("isekai_pipeline/tts.py - Chirp3 HD (API Key)")

"""
이세계 파이프라인 - TTS 모듈 (Chirp3 HD - API Key 방식)

- Google Cloud TTS Chirp3 HD (고품질 한국어)
- GOOGLE_API_KEY 또는 GOOGLE_CLOUD_API_KEY 환경변수 사용
- REST API 방식 (서비스 계정 불필요)
- 감정 태그 기반 속도 조절 지원
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
DEFAULT_SPEED = 0.9  # 기본 속도 (약간 느리게)

# 감정 태그 → 속도 매핑
EMOTION_SPEED_MAP = {
    # 빠르게 (긴장, 급박)
    "긴장": 1.05,
    "급박": 1.1,
    "전투": 1.05,
    "충격": 1.0,
    "분노": 1.0,

    # 느리게 (슬픔, 여운, 회상)
    "슬픔": 0.8,
    "여운": 0.85,
    "회상": 0.85,
    "고요": 0.85,
    "비장": 0.9,

    # 기본 속도
    "담담": 0.9,
    "서술": 0.9,
}


def parse_emotion_tag(text: str) -> Tuple[Optional[str], str]:
    """
    문장에서 감정 태그 추출

    예: "[긴장] 무영은 검을 들었다." → ("긴장", "무영은 검을 들었다.")
    예: "무영은 검을 들었다." → (None, "무영은 검을 들었다.")
    """
    match = re.match(r'^\[([^\]]+)\]\s*(.+)$', text.strip())
    if match:
        return match.group(1), match.group(2)
    return None, text


def get_speed_for_emotion(emotion: Optional[str], base_speed: float = DEFAULT_SPEED) -> float:
    """감정에 따른 속도 반환"""
    if emotion is None:
        return base_speed
    return EMOTION_SPEED_MAP.get(emotion, base_speed)


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
    speaking_rate: float = DEFAULT_SPEED
) -> Dict[str, Any]:
    """
    Google Cloud TTS REST API로 Chirp3 HD 청크 생성

    Args:
        text: 읽을 텍스트
        voice_name: 음성 이름 (예: ko-KR-Chirp3-HD-Charon)
        api_key: Google Cloud API 키
        speaking_rate: 속도 (0.25 ~ 4.0, 기본 0.9)
    """
    url = f"{TTS_API_URL}?key={api_key}"

    # 언어 코드 추출 (ko-KR-Chirp3-HD-Charon → ko-KR)
    lang_code = "-".join(voice_name.split("-")[:2])

    # 속도 범위 제한 (0.25 ~ 4.0)
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
            "speakingRate": speaking_rate
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
    speed: float = DEFAULT_SPEED,
) -> Dict[str, Any]:
    """
    대본에 대해 TTS 생성 (Chirp3 HD REST API)

    감정 태그 지원:
        [긴장] 무영은 검을 들었다. → 속도 1.05로 읽음
        [슬픔] 설하를 떠올렸다. → 속도 0.8로 읽음
        태그 없는 문장 → 기본 속도 0.9로 읽음

    Args:
        episode_id: 에피소드 ID (예: "ep001")
        script: 대본 텍스트 (감정 태그 포함 가능)
        output_dir: 출력 디렉토리
        voice: 음성 (Charon, Kore, Puck, Fenrir, Aoede)
        speed: 기본 속도 (0.9 권장)

    Returns:
        {"ok": True, "audio_path": "...", "srt_path": "...", "duration": 900.5}
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
    print(f"[ISEKAI-TTS] 음성: {voice_name}, 기본 속도: {speed}")

    # 문장 분할
    raw_sentences = split_into_sentences(script)
    print(f"[ISEKAI-TTS] {len(raw_sentences)}개 문장 처리 중...")

    # 감정 태그 파싱 및 문장별 속도 결정
    # 같은 속도의 연속 문장들을 청크로 묶음
    parsed_sentences = []
    for sentence in raw_sentences:
        emotion, clean_text = parse_emotion_tag(sentence)
        sentence_speed = get_speed_for_emotion(emotion, speed)
        parsed_sentences.append({
            "text": clean_text,
            "emotion": emotion,
            "speed": sentence_speed
        })

    # 같은 속도의 연속 문장들을 청크로 병합
    MAX_CHARS = 1400
    chunks = []  # [(text, speed, [sentences])]
    current_chunk = ""
    current_speed = speed
    current_sentences = []

    for item in parsed_sentences:
        text = item["text"]
        sentence_speed = item["speed"]

        # 속도가 다르면 새 청크 시작
        if sentence_speed != current_speed and current_chunk:
            chunks.append((current_chunk.strip(), current_speed, list(current_sentences)))
            current_chunk = ""
            current_sentences = []

        current_speed = sentence_speed

        # 길이 초과하면 새 청크 시작
        if len(current_chunk) + len(text) + 1 > MAX_CHARS and current_chunk:
            chunks.append((current_chunk.strip(), current_speed, list(current_sentences)))
            current_chunk = ""
            current_sentences = []

        current_chunk += " " + text if current_chunk else text
        current_sentences.append(text)

    if current_chunk:
        chunks.append((current_chunk.strip(), current_speed, list(current_sentences)))

    print(f"[ISEKAI-TTS] {len(chunks)}개 청크로 병합 (감정별 속도 적용)")

    audio_paths = []
    timeline = []
    current_time = 0.0
    failed_count = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        for i, (chunk, chunk_speed, chunk_sentences) in enumerate(chunks):
            if not chunk:
                continue

            # TTS 생성 (재시도 포함)
            result = None
            for retry in range(3):
                result = generate_chirp3_tts_chunk(chunk, voice_name, api_key, chunk_speed)
                if result.get("ok"):
                    break
                time.sleep(1)

            if not result.get("ok"):
                print(f"[ISEKAI-TTS] 청크 {i+1} 실패: {result.get('error')}")
                failed_count += 1
                if failed_count >= 3:
                    return {"ok": False, "error": f"TTS 연속 실패: {result.get('error')}"}
                continue

            # MP3 저장
            mp3_path = os.path.join(temp_dir, f"chunk_{i:04d}.mp3")
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

            if (i + 1) % 3 == 0 or i == len(chunks) - 1:
                print(f"[ISEKAI-TTS] {i+1}/{len(chunks)} 완료 ({current_time:.1f}초)")

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
        print(f"[ISEKAI-TTS] 완료: {total_duration:.1f}초, {len(timeline)}개 자막")

        return {
            "ok": True,
            "audio_path": audio_output,
            "srt_path": srt_output,
            "duration": total_duration,
            "timeline": timeline,
        }


if __name__ == "__main__":
    print("isekai_pipeline/tts.py - Chirp3 HD (API Key)")

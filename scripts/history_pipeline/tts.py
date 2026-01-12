"""
한국사 파이프라인 - TTS 모듈 (Gemini + ElevenLabs 폴백)

- 1순위: Gemini TTS (GOOGLE_API_KEY)
- 2순위: ElevenLabs TTS (ELEVENLABS_API_KEY)
- 문장 단위 자막 생성
- 독립 실행 가능
"""

import os
import re
import tempfile
import subprocess
import time
import requests
from typing import Dict, Any, List, Tuple


# ElevenLabs 설정
DEFAULT_VOICE_ID = "aurnUodFzOtofecLd3T1"  # Jung_Narrative (이세계와 동일)
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# 기본 음성 설정
DEFAULT_STABILITY = 0.50
DEFAULT_SIMILARITY_BOOST = 0.75
DEFAULT_SPEED = 0.95  # 0.7 ~ 1.2 (한국사 다큐용 차분한 톤)


def split_into_sentences(text: str) -> List[str]:
    """텍스트를 문장 단위로 분할"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def get_audio_duration(audio_path: str) -> float:
    """오디오 파일의 재생 시간(초) 반환"""
    # mutagen 먼저 시도 (더 정확)
    try:
        from mutagen.mp3 import MP3
        audio = MP3(audio_path)
        return audio.info.length
    except Exception:
        pass

    # ffprobe 시도
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True, text=True, timeout=30
        )
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0.0
        if duration > 0:
            return duration
    except Exception:
        pass

    # 파일 크기로 추정 (MP3 128kbps 기준)
    try:
        file_size = os.path.getsize(audio_path)
        if file_size > 0:
            return file_size / 16000.0
    except Exception:
        pass

    return 0.0


def merge_audio_files(audio_paths: List[str], output_path: str) -> bool:
    """여러 오디오 파일을 하나로 합침"""
    if not audio_paths:
        return False

    if len(audio_paths) == 1:
        import shutil
        shutil.copy(audio_paths[0], output_path)
        return True

    # pydub 먼저 시도
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

    # ffmpeg 시도
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
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
    except Exception:
        pass

    # 순수 Python 바이너리 병합 (폴백)
    try:
        print("[HISTORY-TTS] 순수 Python으로 MP3 병합...")
        with open(output_path, 'wb') as outfile:
            for path in audio_paths:
                with open(path, 'rb') as infile:
                    outfile.write(infile.read())
        return os.path.exists(output_path)
    except Exception:
        return False


def generate_gemini_tts_chunk(
    text: str,
    voice_name: str = "Charon",
    api_key: str = None
) -> Dict[str, Any]:
    """Gemini TTS API로 청크 생성"""
    if not api_key:
        api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        return {"ok": False, "error": "GOOGLE_API_KEY 없음"}

    valid_voices = ["Kore", "Charon", "Puck", "Fenrir", "Aoede"]
    if voice_name not in valid_voices:
        voice_name = "Charon"

    model = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        }
    }

    try:
        import base64
        response = requests.post(url, json=payload, timeout=120)

        if response.status_code == 429:
            return {"ok": False, "error": "Gemini Rate limit"}

        if response.status_code != 200:
            return {"ok": False, "error": f"Gemini API 오류: {response.status_code}"}

        result = response.json()
        candidates = result.get("candidates", [])
        if not candidates:
            return {"ok": False, "error": "응답 없음"}

        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            inline_data = part.get("inlineData", {})
            if inline_data.get("mimeType", "").startswith("audio/"):
                audio_b64 = inline_data.get("data", "")
                if audio_b64:
                    audio_data = base64.b64decode(audio_b64)
                    return {
                        "ok": True,
                        "audio_data": audio_data,
                        "format": "wav"
                    }

        return {"ok": False, "error": "오디오 데이터 없음"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def extract_sentence_timing_from_alignment(
    chunk_text: str,
    sentences: List[str],
    alignment: Dict[str, Any],
    time_offset: float = 0.0
) -> List[Tuple[float, float, str]]:
    """
    ElevenLabs alignment 데이터에서 문장별 타이밍 추출

    Args:
        chunk_text: 청크 전체 텍스트
        sentences: 문장 리스트
        alignment: ElevenLabs alignment 데이터
            - characters: 문자 리스트
            - character_start_times_seconds: 각 문자 시작 시간
            - character_end_times_seconds: 각 문자 종료 시간
        time_offset: 이전 청크들의 누적 시간

    Returns:
        [(start, end, text), ...] 타이밍 리스트
    """
    if not alignment:
        return []

    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])

    if not chars or not starts or not ends:
        return []

    timeline = []
    char_idx = 0

    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue

        # 문장의 첫 글자 찾기 (공백 건너뛰기)
        sentence_start = None
        sentence_end = None

        # 청크 내에서 문장 위치 찾기
        found_start = False
        match_count = 0

        for i in range(char_idx, len(chars)):
            c = chars[i]

            # 문장의 첫 글자와 매칭 시작
            if not found_start:
                if match_count < len(sentence_clean) and c == sentence_clean[match_count]:
                    if match_count == 0:
                        sentence_start = starts[i] if i < len(starts) else None
                    match_count += 1
                    if match_count >= len(sentence_clean):
                        sentence_end = ends[i] if i < len(ends) else None
                        char_idx = i + 1
                        found_start = True
                        break
                elif c in ' \n\t':
                    # 공백은 건너뛰기
                    continue
                else:
                    # 매칭 실패, 리셋
                    match_count = 0
                    sentence_start = None

        if sentence_start is not None and sentence_end is not None:
            timeline.append((
                time_offset + sentence_start,
                time_offset + sentence_end,
                sentence_clean
            ))

    return timeline


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


def generate_elevenlabs_tts_chunk(
    text: str,
    voice_id: str,
    api_key: str,
    stability: float = DEFAULT_STABILITY,
    similarity_boost: float = DEFAULT_SIMILARITY_BOOST,
    speed: float = DEFAULT_SPEED,
    with_timestamps: bool = True,
) -> Dict[str, Any]:
    """ElevenLabs TTS API로 청크 생성 (타임스탬프 포함)"""
    url = f"{ELEVENLABS_API_URL}/{voice_id}/with-timestamps"

    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    # 속도 범위 제한 (0.7 ~ 1.2)
    speed = max(0.7, min(1.2, speed))

    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "speed": speed,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)

        if response.status_code == 200:
            data = response.json()
            # audio_base64와 alignment 정보 반환
            import base64
            audio_data = base64.b64decode(data.get("audio_base64", ""))
            alignment = data.get("alignment", {})
            return {
                "ok": True,
                "audio_data": audio_data,
                "alignment": alignment,  # characters, character_start_times_seconds, character_end_times_seconds
            }
        else:
            error_msg = response.text[:300] if response.text else f"HTTP {response.status_code}"
            return {"ok": False, "error": f"ElevenLabs API 오류: {error_msg}"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def generate_tts(
    episode_id: str,
    script: str,
    output_dir: str,
    voice: str = None,
    speed: float = 1.0,
) -> Dict[str, Any]:
    """
    대본에 대해 TTS 생성 (Gemini 우선, ElevenLabs 폴백)

    Args:
        episode_id: 에피소드 ID (예: "ep019")
        script: 대본 텍스트
        output_dir: 출력 디렉토리
        voice: 음성 이름 (gemini:Charon 또는 ElevenLabs ID)
        speed: 속도 (현재 미사용)

    Returns:
        {"ok": True, "audio_path": "...", "srt_path": "...", "duration": 900.5}
    """
    os.makedirs(output_dir, exist_ok=True)

    # TTS 엔진 선택
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')

    use_gemini = bool(google_api_key)

    # gemini: 프리픽스가 있으면 Gemini 사용
    gemini_voice = "Charon"  # 기본값
    if voice and voice.startswith("gemini:"):
        use_gemini = True
        gemini_voice = voice.split(":")[1] if ":" in voice else "Charon"
    elif voice and voice.startswith("chirp3:"):
        use_gemini = True
        gemini_voice = voice.split(":")[1] if ":" in voice else "Charon"

    if use_gemini:
        print(f"[HISTORY-TTS] 음성: Gemini - {gemini_voice}")
    else:
        voice_id = voice if voice and len(voice) > 15 else DEFAULT_VOICE_ID
        print(f"[HISTORY-TTS] 음성: ElevenLabs - {voice_id}")

    # 문장 분할
    sentences = split_into_sentences(script)
    print(f"[HISTORY-TTS] {len(sentences)}개 문장 처리 중...")

    # 청크 병합 (API 제한 대응) - 타임아웃 방지를 위해 작게
    MAX_CHARS = 2000
    chunks = []
    current_chunk = ""
    current_sentences = []

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= MAX_CHARS:
            current_chunk += " " + sentence if current_chunk else sentence
            current_sentences.append(sentence)
        else:
            if current_chunk:
                chunks.append((current_chunk.strip(), current_sentences))
            current_chunk = sentence
            current_sentences = [sentence]

    if current_chunk:
        chunks.append((current_chunk.strip(), current_sentences))

    print(f"[HISTORY-TTS] {len(chunks)}개 청크로 병합")

    audio_paths = []
    timeline = []
    current_time = 0.0
    failed_count = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        for i, (chunk, chunk_sentences) in enumerate(chunks):
            if not chunk:
                continue

            # TTS 생성 (Gemini 또는 ElevenLabs)
            result = None
            for retry in range(3):
                if use_gemini:
                    result = generate_gemini_tts_chunk(chunk, gemini_voice, google_api_key)
                else:
                    result = generate_elevenlabs_tts_chunk(chunk, voice_id, elevenlabs_key, speed=speed)

                if result.get("ok"):
                    break
                error_msg = result.get('error', '')
                if 'Rate limit' in error_msg or '429' in error_msg:
                    wait_time = 45 if use_gemini else 2
                    print(f"[HISTORY-TTS] 청크 {i+1} Rate limit, {wait_time}초 대기 ({retry+1}/3)...")
                    time.sleep(wait_time)
                elif 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                    print(f"[HISTORY-TTS] 청크 {i+1} 타임아웃, 재시도 {retry+1}/3...")
                    time.sleep(2)
                else:
                    time.sleep(1)

            if not result.get("ok"):
                print(f"[HISTORY-TTS] 청크 {i+1} 실패: {result.get('error')}")
                failed_count += 1
                if failed_count >= 3:
                    return {"ok": False, "error": f"TTS 생성 연속 실패: {result.get('error')}"}
                continue

            # 오디오 파일 저장 (Gemini=WAV, ElevenLabs=MP3)
            audio_format = result.get("format", "mp3")
            audio_ext = "wav" if audio_format == "wav" else "mp3"
            audio_path = os.path.join(temp_dir, f"chunk_{i:04d}.{audio_ext}")

            with open(audio_path, 'wb') as f:
                f.write(result["audio_data"])

            # 형식 확인 (첫 청크만)
            if i == 0:
                print(f"[HISTORY-TTS] 오디오 형식: {audio_ext.upper()}, 크기: {len(result['audio_data'])} bytes")

            # 길이 확인
            duration = get_audio_duration(audio_path)
            if duration > 0:
                audio_paths.append(audio_path)

                # ElevenLabs alignment 데이터 사용 (정확한 타이밍)
                alignment = result.get("alignment")
                if alignment and not use_gemini:
                    chunk_timeline = extract_sentence_timing_from_alignment(
                        chunk, chunk_sentences, alignment, current_time
                    )
                    if chunk_timeline:
                        timeline.extend(chunk_timeline)
                        if i == 0:
                            print(f"[HISTORY-TTS] alignment 데이터 사용 (정확한 싱크)")
                    else:
                        # alignment 추출 실패 시 폴백
                        print(f"[HISTORY-TTS] 청크 {i+1} alignment 추출 실패, 비례 계산 사용")
                        total_chars = sum(len(s) for s in chunk_sentences)
                        chunk_start = current_time
                        for sentence in chunk_sentences:
                            sentence_ratio = len(sentence) / total_chars if total_chars > 0 else 1
                            sentence_duration = duration * sentence_ratio
                            timeline.append((chunk_start, chunk_start + sentence_duration, sentence))
                            chunk_start += sentence_duration
                else:
                    # Gemini 또는 alignment 없음: 글자 수 비례 계산 (폴백)
                    total_chars = sum(len(s) for s in chunk_sentences)
                    chunk_start = current_time
                    for sentence in chunk_sentences:
                        sentence_ratio = len(sentence) / total_chars if total_chars > 0 else 1
                        sentence_duration = duration * sentence_ratio
                        timeline.append((chunk_start, chunk_start + sentence_duration, sentence))
                        chunk_start += sentence_duration

                current_time += duration
                failed_count = 0

            # 진행률 표시
            if (i + 1) % 3 == 0 or i == len(chunks) - 1:
                print(f"[HISTORY-TTS] {i+1}/{len(chunks)} 완료 ({current_time:.1f}초)")

        if not audio_paths:
            return {"ok": False, "error": "TTS 생성 실패 - 오디오 없음"}

        # 오디오 합치기
        audio_output = os.path.join(output_dir, f"{episode_id}.mp3")
        if not merge_audio_files(audio_paths, audio_output):
            return {"ok": False, "error": "오디오 병합 실패"}

        # SRT 생성
        srt_dir = os.path.join(os.path.dirname(output_dir), "subtitles")
        os.makedirs(srt_dir, exist_ok=True)
        srt_output = os.path.join(srt_dir, f"{episode_id}.srt")
        generate_srt(timeline, srt_output)

        total_duration = get_audio_duration(audio_output)
        print(f"[HISTORY-TTS] 완료: {total_duration:.1f}초, {len(timeline)}개 자막")

        return {
            "ok": True,
            "audio_path": audio_output,
            "srt_path": srt_output,
            "duration": total_duration,
            "timeline": timeline,
            "provider": "elevenlabs",
        }


if __name__ == "__main__":
    print("history_pipeline/tts.py 로드 완료")
    print(f"기본 음성: ElevenLabs - {DEFAULT_VOICE_ID}")

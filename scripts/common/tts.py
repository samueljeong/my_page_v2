"""
공통 TTS 모듈
모든 파이프라인에서 공유하는 TTS 기능

지원하는 TTS 엔진:
- Gemini TTS (gemini:Kore, gemini:pro:Charon)
- Google Cloud TTS Chirp3 HD (chirp3:Charon)
- Google Cloud TTS Neural2 (ko-KR-Neural2-C)

사용법:
    from scripts.common.tts import generate_chirp3_tts, is_chirp3_voice

    # Chirp3 TTS
    if is_chirp3_voice("chirp3:Charon"):
        config = parse_chirp3_voice("chirp3:Charon")
        result = generate_chirp3_tts(text, voice_name=config['voice'])

    # Gemini TTS
    if is_gemini_voice("gemini:Kore"):
        config = parse_gemini_voice("gemini:Kore")
        result = generate_gemini_tts(text, voice_name=config['voice'], model=config['model'])
"""

import os
import re
import io
import wave
import json
import base64
import time
import tempfile
import subprocess
from typing import Dict, Any, Optional

import requests


# ============================================================
# TTS 텍스트 전처리
# ============================================================

def preprocess_tts_text(text: str) -> str:
    """
    TTS용 텍스트 전처리 - 영문 인명 괄호 제거

    자막: 니콜라이 티보-브리뇰(Nikolay Thibeaux-Brignolle)
    TTS: "니콜라이 티보-브리뇰" (영문 부분은 읽지 않음)

    Args:
        text: 원본 텍스트

    Returns:
        영문 인명 괄호가 제거된 텍스트
    """
    # 영문 인명 패턴: (대문자로 시작하는 영문 이름)
    pattern = r'\([A-Z][a-zA-Z\-\s\'\.]+\)'
    result = re.sub(pattern, '', text)

    # 연속 공백 정리
    result = re.sub(r'  +', ' ', result)

    return result


def preprocess_tts_extended(text: str) -> str:
    """
    TTS용 확장 텍스트 전처리

    처리 항목:
    1. 영문 약어 → 발음 (CEO → 씨이오)
    2. 특수 기호 → 한글 (& → 앤드, @ → 앳)
    3. 통화 기호 → 한글 ($ → 달러, € → 유로)
    4. 온도 기호 → 한글 (℃ → 도씨)
    5. URL/이메일 → 제거
    6. 이모지 → 제거
    7. 특수 문장부호 → 정리
    """
    if not text:
        return text

    # 1. URL 제거
    text = re.sub(r'https?://[^\s<>\"\']+', '', text)
    text = re.sub(r'www\.[^\s<>\"\']+', '', text)

    # 2. 이메일 제거
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)

    # 3. 이모지 제거
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U0001F200-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    # 4. 통화 기호 → 한글
    currency_map = {
        '$': '달러', '€': '유로', '¥': '엔',
        '£': '파운드', '₩': '원', '₿': '비트코인',
    }
    for symbol, korean in currency_map.items():
        text = re.sub(rf'\{symbol}(\d)', rf'\1{korean}', text)
        text = re.sub(rf'(\d)\{symbol}', rf'\1{korean}', text)
        text = text.replace(symbol, korean)

    # 5. 온도 기호 → 한글
    text = text.replace('℃', '도씨')
    text = text.replace('℉', '화씨')
    text = text.replace('°C', '도씨')
    text = text.replace('°F', '화씨')
    text = re.sub(r'(\d)°(?![CF])', r'\1도', text)

    # 6. 특수 기호 → 한글/제거
    symbol_map = {
        '&': '앤드', '@': '앳', '#': '해시',
        '※': '', '★': '', '☆': '', '●': '', '○': '',
        '◆': '', '◇': '', '■': '', '□': '',
        '▶': '', '◀': '', '→': '', '←': '', '↑': '', '↓': '',
        '—': ' ', '–': ' ', '…': '...', '·': ' ',
        '「': '', '」': '', '『': '', '』': '',
        '〈': '', '〉': '', '《': '', '》': '',
    }
    for symbol, replacement in symbol_map.items():
        text = text.replace(symbol, replacement)

    # 7. 수학 기호 → 한글
    math_map = {
        '±': '플러스마이너스', '∞': '무한대', '√': '루트',
        '≤': '이하', '≥': '이상', '≠': '같지않음',
        '≈': '약', '∴': '따라서', '∵': '왜냐하면',
    }
    for symbol, korean in math_map.items():
        text = text.replace(symbol, korean)

    # 8. 영문 약어 → 발음
    abbreviation_map = {
        # 기관/조직
        'CEO': '씨이오', 'CFO': '씨에프오', 'CTO': '씨티오',
        'UN': '유엔', 'UNESCO': '유네스코', 'WHO': '더블유에이치오',
        'NATO': '나토', 'OECD': '오이씨디', 'IMF': '아이엠에프',
        'FBI': '에프비아이', 'CIA': '씨아이에이', 'NASA': '나사',
        'EU': '이유', 'ASEAN': '아세안', 'OPEC': '오펙',
        # 기술
        'AI': '에이아이', 'IT': '아이티', 'PC': '피씨',
        'USB': '유에스비', 'URL': '유알엘', 'API': '에이피아이',
        'CPU': '씨피유', 'GPU': '지피유', 'RAM': '램', 'ROM': '롬',
        'SSD': '에스에스디', 'LED': '엘이디', 'LCD': '엘씨디',
        'VR': '브이알', 'AR': '에이알', 'IoT': '아이오티',
        'GPS': '지피에스', 'WIFI': '와이파이', 'LTE': '엘티이',
        '5G': '오지', '4G': '사지', '3G': '삼지',
        'QR': '큐알', 'PDF': '피디에프', 'MP3': '엠피쓰리', 'MP4': '엠피포',
        # 경제/금융
        'GDP': '지디피', 'GNP': '지엔피', 'ETF': '이티에프',
        'IPO': '아이피오', 'M&A': '엠앤에이', 'ESG': '이에스지',
        # 의료
        'CT': '씨티', 'MRI': '엠알아이', 'DNA': '디엔에이',
        'RNA': '알엔에이', 'PCR': '피씨알', 'ICU': '아이씨유',
        # 기타
        'TV': '티비', 'SNS': '에스엔에스', 'PR': '피알',
        'OK': '오케이', 'VS': '버서스', 'DIY': '디아이와이',
        'VIP': '브이아이피', 'MVP': '엠브이피', 'OTT': '오티티',
        'BTS': '비티에스', 'K-POP': '케이팝', 'KPOP': '케이팝',
    }

    for abbr, korean in abbreviation_map.items():
        pattern = rf'(?<![가-힣a-zA-Z]){re.escape(abbr)}(?![가-힣a-zA-Z])'
        text = re.sub(pattern, korean, text, flags=re.IGNORECASE)

    # 사전에 없는 대문자 약어 → 개별 알파벳 발음
    def spell_out_abbreviation(match):
        abbr = match.group(0)
        if abbr.upper() in abbreviation_map:
            return abbr
        letter_sounds = {
            'A': '에이', 'B': '비', 'C': '씨', 'D': '디', 'E': '이',
            'F': '에프', 'G': '지', 'H': '에이치', 'I': '아이', 'J': '제이',
            'K': '케이', 'L': '엘', 'M': '엠', 'N': '엔', 'O': '오',
            'P': '피', 'Q': '큐', 'R': '알', 'S': '에스', 'T': '티',
            'U': '유', 'V': '브이', 'W': '더블유', 'X': '엑스', 'Y': '와이',
            'Z': '제트'
        }
        return ''.join(letter_sounds.get(c.upper(), c) for c in abbr)

    text = re.sub(r'(?<![가-힣a-zA-Z])[A-Z]{2,6}(?![가-힣a-zA-Z])', spell_out_abbreviation, text)

    # 9. 연속 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# ============================================================
# 음성 타입 체크 및 파싱
# ============================================================

def is_gemini_voice(voice_name: str) -> bool:
    """Gemini TTS 음성인지 확인 (gemini: 접두사)"""
    return voice_name.lower().startswith("gemini:")


def is_chirp3_voice(voice_name: str) -> bool:
    """Chirp 3 HD 음성인지 확인 (chirp3: 접두사)"""
    return voice_name.lower().startswith("chirp3:")


def parse_gemini_voice(voice_name: str) -> Dict[str, str]:
    """
    Gemini 음성 설정 파싱

    Args:
        voice_name: "gemini:Kore" 또는 "gemini:pro:Charon" 형식

    Returns:
        dict: {"voice": "Kore", "model": "gemini-2.5-flash-preview-tts"}
    """
    parts = voice_name.split(":")

    if len(parts) == 2:
        # "gemini:Kore" -> Flash 모델 사용
        return {
            "voice": parts[1],
            "model": "gemini-2.5-flash-preview-tts"
        }
    elif len(parts) == 3:
        # "gemini:pro:Kore" -> Pro 모델 사용
        model_type = parts[1].lower()
        voice = parts[2]
        if model_type == "pro":
            return {
                "voice": voice,
                "model": "gemini-2.5-pro-preview-tts"
            }
        else:
            return {
                "voice": voice,
                "model": "gemini-2.5-flash-preview-tts"
            }
    else:
        # 기본값
        return {
            "voice": "Kore",
            "model": "gemini-2.5-flash-preview-tts"
        }


def parse_chirp3_voice(voice_name: str, language_code: str = "ko-KR") -> Dict[str, str]:
    """
    Chirp 3 HD 음성 설정 파싱

    Args:
        voice_name: "chirp3:Charon" 형식
        language_code: 언어 코드 (기본: ko-KR)

    Returns:
        dict: {"voice": "ko-KR-Chirp3-HD-Charon", "voice_short": "Charon"}
    """
    parts = voice_name.split(":")
    voice_short = parts[1] if len(parts) >= 2 else "Charon"

    # 유효한 Chirp 3 HD 음성
    valid_voices = ["Charon", "Puck", "Fenrir", "Orus", "Aoede", "Kore", "Leda", "Zephyr"]
    if voice_short not in valid_voices:
        print(f"[CHIRP3] 잘못된 음성: {voice_short}, 기본값 Charon 사용")
        voice_short = "Charon"

    full_voice_name = f"{language_code}-Chirp3-HD-{voice_short}"

    return {
        "voice": full_voice_name,
        "voice_short": voice_short
    }


# ============================================================
# Gemini TTS
# ============================================================

def generate_gemini_tts(
    text: str,
    voice_name: str = "Kore",
    model: str = "gemini-2.5-flash-preview-tts"
) -> Dict[str, Any]:
    """
    Gemini TTS API를 사용하여 음성 생성

    Args:
        text: 변환할 텍스트
        voice_name: 음성 이름 (Kore, Charon, Puck, Fenrir, Aoede)
        model: 모델명 (gemini-2.5-flash-preview-tts 또는 gemini-2.5-pro-preview-tts)

    Returns:
        dict: {"ok": True, "audio_data": bytes, "duration": float, "format": "wav"}
              또는 {"ok": False, "error": str}
    """
    # 텍스트 전처리
    text = preprocess_tts_text(text)
    text = preprocess_tts_extended(text)

    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("[GEMINI-TTS] GOOGLE_API_KEY 환경변수가 설정되지 않았습니다")
        return {"ok": False, "error": "GOOGLE_API_KEY 환경변수가 설정되지 않았습니다"}

    # 유효한 음성 확인
    valid_voices = ["Kore", "Charon", "Puck", "Fenrir", "Aoede"]
    if voice_name not in valid_voices:
        print(f"[GEMINI-TTS] 잘못된 음성: {voice_name}, 기본값 Kore 사용")
        voice_name = "Kore"

    print(f"[GEMINI-TTS] 시작 - 모델: {model}, 음성: {voice_name}, 텍스트: {len(text)}자")

    try:
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

        # 429 Rate Limit 재시도 로직
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(url, json=payload, timeout=120)

            if response.status_code == 429:
                retry_match = re.search(r'retry in (\d+\.?\d*)', response.text)
                wait_time = float(retry_match.group(1)) if retry_match else 45.0
                wait_time = min(wait_time + 5, 60)

                if attempt < max_retries - 1:
                    print(f"[GEMINI-TTS] Rate limit (429), {wait_time:.0f}초 대기 후 재시도 ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"ok": False, "error": "Gemini TTS Rate limit 초과 (재시도 실패)"}

            elif response.status_code != 200:
                error_text = response.text[:500]
                print(f"[GEMINI-TTS] API 오류: {response.status_code} - {error_text}")
                return {"ok": False, "error": f"Gemini TTS API 오류: {response.status_code}"}

            break

        result = response.json()

        # 오디오 데이터 추출
        candidates = result.get("candidates", [])
        if not candidates:
            return {"ok": False, "error": "응답에 candidates가 없습니다"}

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        audio_data = None
        for part in parts:
            inline_data = part.get("inlineData", {})
            if inline_data.get("mimeType", "").startswith("audio/"):
                audio_data = base64.b64decode(inline_data.get("data", ""))
                break

        if not audio_data:
            return {"ok": False, "error": "응답에 오디오 데이터가 없습니다"}

        # PCM을 WAV로 변환 (24kHz, 16bit, mono)
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)

        wav_data = wav_buffer.getvalue()
        duration = len(audio_data) / (24000 * 2)

        print(f"[GEMINI-TTS] 완료 - 크기: {len(wav_data)}bytes, 길이: {duration:.1f}초")

        return {
            "ok": True,
            "audio_data": wav_data,
            "duration": duration,
            "format": "wav"
        }

    except requests.exceptions.Timeout:
        print("[GEMINI-TTS] 타임아웃")
        return {"ok": False, "error": "Gemini TTS 타임아웃 (120초)"}
    except Exception as e:
        print(f"[GEMINI-TTS] 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


def convert_gemini_wav_to_mp3(wav_data: bytes) -> Optional[bytes]:
    """Gemini TTS의 WAV 출력을 MP3로 변환"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_file.write(wav_data)
            wav_path = wav_file.name

        mp3_path = wav_path.replace('.wav', '.mp3')

        cmd = [
            'ffmpeg', '-y', '-i', wav_path,
            '-acodec', 'libmp3lame', '-b:a', '128k',
            mp3_path
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode == 0 and os.path.exists(mp3_path):
            with open(mp3_path, 'rb') as f:
                mp3_data = f.read()
            os.unlink(wav_path)
            os.unlink(mp3_path)
            return mp3_data
        else:
            os.unlink(wav_path)
            print(f"[GEMINI-TTS] MP3 변환 실패: {result.stderr.decode()[:200]}")
            return None

    except Exception as e:
        print(f"[GEMINI-TTS] MP3 변환 오류: {e}")
        return None


# ============================================================
# Google Cloud TTS Chirp3 HD
# ============================================================

def generate_chirp3_tts(
    text: str,
    voice_name: str = "ko-KR-Chirp3-HD-Charon",
    language_code: str = "ko-KR"
) -> Dict[str, Any]:
    """
    Google Cloud TTS Chirp 3 HD를 사용하여 음성 생성

    긴 텍스트는 자동으로 청크로 분할하여 처리 (5,000바이트 제한)

    Args:
        text: 변환할 텍스트
        voice_name: 전체 음성 이름 (예: ko-KR-Chirp3-HD-Charon)
        language_code: 언어 코드 (예: ko-KR)

    Returns:
        dict: {"ok": True, "audio_data": bytes} 또는 {"ok": False, "error": str}
    """
    # 텍스트 전처리
    text = preprocess_tts_text(text)
    text = preprocess_tts_extended(text)

    try:
        from google.cloud import texttospeech
        from google.oauth2 import service_account

        print(f"[CHIRP3-TTS] 시작 - 음성: {voice_name}, 텍스트: {len(text)}자", flush=True)

        # 서비스 계정 인증
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            print("[CHIRP3-TTS] 오류: GOOGLE_SERVICE_ACCOUNT_JSON 환경변수 없음", flush=True)
            return {"ok": False, "error": "GOOGLE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다"}

        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            print(f"[CHIRP3-TTS] 오류: JSON 파싱 실패 - {e}", flush=True)
            return {"ok": False, "error": f"서비스 계정 JSON 파싱 실패: {e}"}

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        client = texttospeech.TextToSpeechClient(credentials=credentials)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # 청크 분할 설정
        MAX_CHARS = 1400
        MAX_SENTENCE_CHARS = 350

        def split_long_sentence(sentence, max_len=MAX_SENTENCE_CHARS):
            """긴 문장을 쉼표/공백에서 분할"""
            if len(sentence) <= max_len:
                return [sentence]

            result = []
            parts = re.split(r'(?<=[,，、])\s*', sentence)
            current = ""

            for part in parts:
                if len(current) + len(part) <= max_len:
                    current += part
                else:
                    if current:
                        result.append(current.strip())
                    if len(part) > max_len:
                        words = part.split(' ')
                        word_chunk = ""
                        for word in words:
                            if len(word_chunk) + len(word) + 1 <= max_len:
                                word_chunk += " " + word if word_chunk else word
                            else:
                                if word_chunk:
                                    result.append(word_chunk.strip())
                                if len(word) > max_len:
                                    for i in range(0, len(word), max_len):
                                        result.append(word[i:i+max_len])
                                    word_chunk = ""
                                else:
                                    word_chunk = word
                        if word_chunk:
                            current = word_chunk
                        else:
                            current = ""
                    else:
                        current = part

            if current:
                result.append(current.strip())

            return [r for r in result if r]

        def split_text_into_chunks(text, max_chars=MAX_CHARS):
            """문장 단위로 텍스트를 청크로 분할"""
            sentences = re.split(r'(?<=[.!?。])\s*', text)

            final_sentences = []
            for sentence in sentences:
                if not sentence.strip():
                    continue
                final_sentences.extend(split_long_sentence(sentence))

            chunks = []
            current_chunk = ""

            for sentence in final_sentences:
                if len(current_chunk) + len(sentence) + 1 <= max_chars:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence

            if current_chunk:
                chunks.append(current_chunk.strip())

            return chunks

        # 짧은 텍스트는 바로 처리
        if len(text.encode('utf-8')) <= 4500:
            input_text = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config,
            )
            print(f"[CHIRP3-TTS] 성공 - {len(response.audio_content)} bytes", flush=True)
            return {"ok": True, "audio_data": response.audio_content}

        # 긴 텍스트는 청크로 분할
        chunks = split_text_into_chunks(text)
        print(f"[CHIRP3-TTS] 긴 텍스트 - {len(chunks)}개 청크로 분할", flush=True)

        all_audio = []
        for i, chunk in enumerate(chunks):
            print(f"[CHIRP3-TTS] 청크 {i+1}/{len(chunks)} 처리 중... ({len(chunk)}자)", flush=True)

            input_text = texttospeech.SynthesisInput(text=chunk)
            response = client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config,
            )
            all_audio.append(response.audio_content)

            if i < len(chunks) - 1:
                time.sleep(0.2)

        # MP3 오디오 연결 (pydub 사용)
        try:
            from pydub import AudioSegment

            combined = AudioSegment.empty()
            for audio_data in all_audio:
                segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                combined += segment

            output_buffer = io.BytesIO()
            combined.export(output_buffer, format="mp3")
            final_audio = output_buffer.getvalue()

            print(f"[CHIRP3-TTS] 성공 - {len(chunks)}개 청크 연결, {len(final_audio)} bytes", flush=True)
            return {"ok": True, "audio_data": final_audio}

        except ImportError:
            # pydub 없으면 FFmpeg로 연결
            print("[CHIRP3-TTS] pydub 없음 - FFmpeg로 연결", flush=True)
            import shutil

            temp_dir = tempfile.mkdtemp()
            try:
                temp_files = []
                for i, audio_data in enumerate(all_audio):
                    temp_path = os.path.join(temp_dir, f"chunk_{i:03d}.mp3")
                    with open(temp_path, "wb") as f:
                        f.write(audio_data)
                    temp_files.append(temp_path)

                list_path = os.path.join(temp_dir, "concat_list.txt")
                with open(list_path, "w") as f:
                    for temp_path in temp_files:
                        f.write(f"file '{temp_path}'\n")

                output_path = os.path.join(temp_dir, "merged.mp3")
                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", list_path, "-c", "copy", output_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=300)

                if result.returncode == 0 and os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        final_audio = f.read()
                    print(f"[CHIRP3-TTS] 성공 - FFmpeg로 {len(chunks)}개 청크 연결", flush=True)
                    return {"ok": True, "audio_data": final_audio}
                else:
                    print(f"[CHIRP3-TTS] FFmpeg 실패 - 첫 청크만 반환", flush=True)
                    return {"ok": True, "audio_data": all_audio[0]}
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"[CHIRP3-TTS] 오류: {e}", flush=True)
        return {"ok": False, "error": str(e)}


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("공통 TTS 모듈 테스트")
    print("=" * 60)

    # 음성 타입 체크 테스트
    test_voices = [
        "gemini:Kore",
        "gemini:pro:Charon",
        "chirp3:Charon",
        "ko-KR-Neural2-C",
    ]

    for voice in test_voices:
        print(f"\n{voice}:")
        print(f"  - is_gemini_voice: {is_gemini_voice(voice)}")
        print(f"  - is_chirp3_voice: {is_chirp3_voice(voice)}")

        if is_gemini_voice(voice):
            print(f"  - parse: {parse_gemini_voice(voice)}")
        elif is_chirp3_voice(voice):
            print(f"  - parse: {parse_chirp3_voice(voice)}")

    # 텍스트 전처리 테스트
    test_text = "CEO가 $100만 달러의 AI 투자를 발표했다. 이메일: test@example.com"
    print(f"\n원본: {test_text}")
    print(f"전처리 후: {preprocess_tts_extended(test_text)}")

    print("\n테스트 완료!")

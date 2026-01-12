"""
공통 알림 모듈 - Telegram 푸시 알림

사용법:
    from scripts.common.notify import send_error, send_success

    send_error("ElevenLabs 크레딧 초과", episode="ep021")
    send_success("영상 생성 완료", episode="ep021", duration="23:45")
"""

import os
import urllib.request
import urllib.parse
import json
from typing import Optional, Dict, Any


TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _get_credentials() -> tuple:
    """환경변수에서 Telegram 자격 증명 가져오기"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return token, chat_id


def send_telegram(
    message: str,
    parse_mode: str = "HTML",
    disable_notification: bool = False,
) -> Dict[str, Any]:
    """
    Telegram 메시지 전송

    Args:
        message: 전송할 메시지 (HTML 태그 지원)
        parse_mode: "HTML" 또는 "Markdown"
        disable_notification: True면 무음 알림

    Returns:
        {"ok": True/False, "error": "..."}
    """
    token, chat_id = _get_credentials()

    if not token or not chat_id:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 미설정"}

    url = TELEGRAM_API_URL.format(token=token)

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_notification": str(disable_notification).lower(),
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            return {"ok": result.get("ok", False)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_error(
    error_msg: str,
    episode: Optional[str] = None,
    pipeline: str = "history",
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """
    에러 알림 전송

    Args:
        error_msg: 에러 메시지
        episode: 에피소드 ID (예: "ep021")
        pipeline: 파이프라인 이름
        details: 추가 상세 정보
    """
    lines = [f"<b>[ERROR] {pipeline.upper()}</b>"]

    if episode:
        lines.append(f"Episode: {episode}")

    lines.append(f"\n{error_msg}")

    if details:
        lines.append(f"\n<code>{details[:500]}</code>")

    message = "\n".join(lines)
    return send_telegram(message)


def send_success(
    msg: str,
    episode: Optional[str] = None,
    pipeline: str = "history",
    **kwargs,
) -> Dict[str, Any]:
    """
    성공 알림 전송

    Args:
        msg: 성공 메시지
        episode: 에피소드 ID
        pipeline: 파이프라인 이름
        **kwargs: 추가 정보 (duration, url 등)
    """
    lines = [f"<b>[OK] {pipeline.upper()}</b>"]

    if episode:
        lines.append(f"Episode: {episode}")

    lines.append(f"\n{msg}")

    # 추가 정보
    for key, value in kwargs.items():
        if value:
            lines.append(f"{key}: {value}")

    message = "\n".join(lines)
    return send_telegram(message, disable_notification=True)


def send_warning(
    msg: str,
    episode: Optional[str] = None,
    pipeline: str = "history",
) -> Dict[str, Any]:
    """경고 알림 전송"""
    lines = [f"<b>[WARN] {pipeline.upper()}</b>"]

    if episode:
        lines.append(f"Episode: {episode}")

    lines.append(f"\n{msg}")

    message = "\n".join(lines)
    return send_telegram(message, disable_notification=True)


if __name__ == "__main__":
    # 테스트
    from dotenv import load_dotenv
    load_dotenv()

    result = send_error("테스트 에러 메시지", episode="ep021", details="상세 에러 내용")
    print(f"Error 전송: {result}")

    result = send_success("영상 생성 완료", episode="ep021", duration="23:45")
    print(f"Success 전송: {result}")

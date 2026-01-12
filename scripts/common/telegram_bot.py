"""
Telegram Bot 명령어 처리 모듈

지원 명령어:
- /help - 도움말
- /status - 현재 상태 확인
- /run history <episode> - 한국사 에피소드 생성
- /run isekai <episode> - 이세계 에피소드 생성
- /run bible - 성경 파이프라인 실행
- /run shorts - 숏츠 파이프라인 실행
- /quota - ElevenLabs 크레딧 확인
"""

import os
import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, Callable
from datetime import datetime

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}"

# 실행 중인 작업 추적
_running_tasks: Dict[str, dict] = {}

# 명령어 핸들러 등록
_command_handlers: Dict[str, Callable] = {}


def get_bot_token() -> Optional[str]:
    return os.environ.get("TELEGRAM_BOT_TOKEN")


def get_chat_id() -> Optional[str]:
    return os.environ.get("TELEGRAM_CHAT_ID")


def send_message(text: str, chat_id: str = None, parse_mode: str = "HTML") -> dict:
    """텔레그램 메시지 전송"""
    token = get_bot_token()
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN 미설정"}

    chat_id = chat_id or get_chat_id()
    if not chat_id:
        return {"ok": False, "error": "TELEGRAM_CHAT_ID 미설정"}

    url = f"{TELEGRAM_API_URL.format(token=token)}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def register_command(command: str, handler: Callable):
    """명령어 핸들러 등록"""
    _command_handlers[command] = handler


def handle_message(message: dict) -> Optional[str]:
    """
    텔레그램 메시지 처리

    Args:
        message: Telegram message object

    Returns:
        응답 메시지 또는 None
    """
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    # 허용된 chat_id 확인
    allowed_chat_id = get_chat_id()
    if allowed_chat_id and str(chat_id) != str(allowed_chat_id):
        return None  # 권한 없는 사용자 무시

    if not text.startswith("/"):
        return None  # 명령어가 아니면 무시

    # 명령어 파싱
    parts = text.split()
    command = parts[0].lower().replace("@", " ").split()[0]  # @botname 제거
    args = parts[1:] if len(parts) > 1 else []

    # 내장 명령어 처리
    if command == "/help":
        return cmd_help()
    elif command == "/status":
        return cmd_status()
    elif command == "/run":
        return cmd_run(args)
    elif command == "/quota":
        return cmd_quota()
    elif command == "/stop":
        return cmd_stop(args)

    # 등록된 커스텀 핸들러 확인
    if command in _command_handlers:
        return _command_handlers[command](args)

    return f"알 수 없는 명령어: {command}\n/help 로 도움말 확인"


def cmd_help() -> str:
    """도움말"""
    return """<b>YouTube Automation Bot</b>

<b>명령어:</b>
/help - 이 도움말
/status - 현재 상태 확인
/quota - ElevenLabs 크레딧 확인

<b>파이프라인 실행:</b>
/run history &lt;episode&gt; - 한국사 (예: /run history 21)
/run isekai &lt;episode&gt; - 이세계 (예: /run isekai 15)
/run bible - 성경 파이프라인
/run shorts - 숏츠 파이프라인

<b>작업 중지:</b>
/stop &lt;task_id&gt; - 작업 중지"""


def cmd_status() -> str:
    """현재 상태"""
    if not _running_tasks:
        return "실행 중인 작업 없음"

    lines = ["<b>실행 중인 작업:</b>"]
    for task_id, info in _running_tasks.items():
        elapsed = (datetime.now() - info["started"]).total_seconds()
        lines.append(f"• {info['name']} ({elapsed:.0f}초)")

    return "\n".join(lines)


def cmd_quota() -> str:
    """ElevenLabs 크레딧 확인"""
    try:
        import requests
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            return "ELEVENLABS_API_KEY 미설정"

        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": api_key},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            remaining = limit - used
            reset_date = data.get("next_character_count_reset_unix", 0)

            from datetime import datetime
            reset_str = datetime.fromtimestamp(reset_date).strftime("%m/%d %H:%M") if reset_date else "알 수 없음"

            return f"""<b>ElevenLabs 크레딧</b>
사용: {used:,} / {limit:,}
남은 크레딧: {remaining:,}
리셋: {reset_str}"""
        else:
            return f"API 오류: {response.status_code}"
    except Exception as e:
        return f"확인 실패: {e}"


def cmd_run(args: list) -> str:
    """파이프라인 실행"""
    if not args:
        return "사용법: /run <pipeline> [episode]\n예: /run history 21"

    pipeline = args[0].lower()
    episode = args[1] if len(args) > 1 else None

    if pipeline == "history":
        if not episode:
            return "에피소드 번호 필요: /run history <episode>"
        return run_history_pipeline(episode)

    elif pipeline == "isekai":
        if not episode:
            return "에피소드 번호 필요: /run isekai <episode>"
        return run_isekai_pipeline(episode)

    elif pipeline == "bible":
        return run_bible_pipeline()

    elif pipeline == "shorts":
        return run_shorts_pipeline()

    else:
        return f"알 수 없는 파이프라인: {pipeline}\n지원: history, isekai, bible, shorts"


def cmd_stop(args: list) -> str:
    """작업 중지"""
    # TODO: 실제 작업 중지 구현
    return "작업 중지 기능은 아직 구현되지 않았습니다."


# ============================================================
# 파이프라인 실행 함수
# ============================================================

def run_history_pipeline(episode: str) -> str:
    """한국사 파이프라인 실행"""
    try:
        episode_num = int(episode)
    except ValueError:
        return f"잘못된 에피소드 번호: {episode}"

    task_id = f"history_{episode_num}"
    if task_id in _running_tasks:
        return f"이미 실행 중: {task_id}"

    # 백그라운드 실행을 위해 API 호출
    try:
        import requests
        port = os.environ.get("PORT", "5059")
        base_url = f"http://127.0.0.1:{port}"

        # 비동기 실행 (타임아웃 짧게)
        response = requests.post(
            f"{base_url}/api/history/execute-episode",
            json={"episode": episode_num, "generate_video": True, "upload": False},
            timeout=5
        )

        _running_tasks[task_id] = {
            "name": f"History EP{episode_num:03d}",
            "started": datetime.now(),
        }

        return f"한국사 EP{episode_num:03d} 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except requests.exceptions.Timeout:
        # 타임아웃은 정상 (백그라운드 실행 중)
        _running_tasks[task_id] = {
            "name": f"History EP{episode_num:03d}",
            "started": datetime.now(),
        }
        return f"한국사 EP{episode_num:03d} 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except Exception as e:
        return f"실행 실패: {e}"


def run_isekai_pipeline(episode: str) -> str:
    """이세계 파이프라인 실행"""
    try:
        episode_num = int(episode)
    except ValueError:
        return f"잘못된 에피소드 번호: {episode}"

    task_id = f"isekai_{episode_num}"
    if task_id in _running_tasks:
        return f"이미 실행 중: {task_id}"

    try:
        import requests
        port = os.environ.get("PORT", "5059")
        base_url = f"http://127.0.0.1:{port}"

        response = requests.post(
            f"{base_url}/api/isekai/execute-episode",
            json={"episode": episode_num, "generate_video": True, "upload": False},
            timeout=5
        )

        _running_tasks[task_id] = {
            "name": f"Isekai EP{episode_num:03d}",
            "started": datetime.now(),
        }

        return f"이세계 EP{episode_num:03d} 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except requests.exceptions.Timeout:
        _running_tasks[task_id] = {
            "name": f"Isekai EP{episode_num:03d}",
            "started": datetime.now(),
        }
        return f"이세계 EP{episode_num:03d} 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except Exception as e:
        return f"실행 실패: {e}"


def run_bible_pipeline() -> str:
    """성경 파이프라인 실행"""
    try:
        import requests
        port = os.environ.get("PORT", "5059")
        base_url = f"http://127.0.0.1:{port}"

        response = requests.post(
            f"{base_url}/api/bible/check-and-process",
            timeout=5
        )

        _running_tasks["bible"] = {
            "name": "Bible Pipeline",
            "started": datetime.now(),
        }

        return "성경 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except requests.exceptions.Timeout:
        _running_tasks["bible"] = {
            "name": "Bible Pipeline",
            "started": datetime.now(),
        }
        return "성경 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except Exception as e:
        return f"실행 실패: {e}"


def run_shorts_pipeline() -> str:
    """숏츠 파이프라인 실행"""
    try:
        import requests
        port = os.environ.get("PORT", "5059")
        base_url = f"http://127.0.0.1:{port}"

        response = requests.post(
            f"{base_url}/api/shorts/check-and-process",
            timeout=5
        )

        _running_tasks["shorts"] = {
            "name": "Shorts Pipeline",
            "started": datetime.now(),
        }

        return "숏츠 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except requests.exceptions.Timeout:
        _running_tasks["shorts"] = {
            "name": "Shorts Pipeline",
            "started": datetime.now(),
        }
        return "숏츠 파이프라인 시작됨\n완료 시 알림이 전송됩니다."

    except Exception as e:
        return f"실행 실패: {e}"


def clear_task(task_id: str):
    """완료된 작업 제거"""
    if task_id in _running_tasks:
        del _running_tasks[task_id]


if __name__ == "__main__":
    # 테스트
    from dotenv import load_dotenv
    load_dotenv()

    print(cmd_help())
    print("\n" + cmd_quota())

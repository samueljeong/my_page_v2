"""
Telegram Bot Webhook Blueprint

텔레그램 봇 명령어 처리 API

Routes:
- POST /api/telegram/webhook - Telegram webhook 수신
- GET /api/telegram/set-webhook - Webhook URL 설정
- GET /api/telegram/info - Bot 정보 확인
"""

import os
import json
import urllib.request
import urllib.parse
from flask import Blueprint, request, jsonify

# Blueprint 생성
telegram_bp = Blueprint('telegram', __name__)

# Bot 모듈 import
try:
    from scripts.common.telegram_bot import (
        handle_message,
        send_message,
        get_bot_token,
        get_chat_id,
    )
except ImportError:
    handle_message = None
    send_message = None
    get_bot_token = lambda: None
    get_chat_id = lambda: None


@telegram_bp.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """
    Telegram Webhook 수신 엔드포인트

    Telegram이 메시지를 보내면 이 엔드포인트로 전달됨
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"ok": False, "error": "No data"}), 400

        # 메시지 처리
        message = data.get("message")
        if message and handle_message:
            response_text = handle_message(message)

            if response_text:
                chat_id = message.get("chat", {}).get("id")
                send_message(response_text, chat_id=str(chat_id))

        return jsonify({"ok": True})

    except Exception as e:
        print(f"[TELEGRAM] Webhook 오류: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@telegram_bp.route('/api/telegram/set-webhook', methods=['GET', 'POST'])
def set_telegram_webhook():
    """
    Telegram Webhook URL 설정

    Query params:
    - url: Webhook URL (선택, 없으면 현재 서버 URL 사용)
    - delete: true면 webhook 삭제
    """
    token = get_bot_token()
    if not token:
        return jsonify({"ok": False, "error": "TELEGRAM_BOT_TOKEN 미설정"}), 400

    # Webhook 삭제
    if request.args.get("delete") == "true":
        api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        try:
            req = urllib.request.Request(api_url, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return jsonify(result)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # Webhook URL 설정
    webhook_url = request.args.get("url")
    if not webhook_url:
        # Render 환경에서 자동으로 URL 생성
        render_url = os.environ.get("RENDER_EXTERNAL_URL")
        if render_url:
            webhook_url = f"{render_url}/api/telegram/webhook"
        else:
            return jsonify({
                "ok": False,
                "error": "URL 파라미터 필요 또는 RENDER_EXTERNAL_URL 환경변수 설정 필요"
            }), 400

    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    data = urllib.parse.urlencode({"url": webhook_url}).encode("utf-8")

    try:
        req = urllib.request.Request(api_url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            result["webhook_url"] = webhook_url
            return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@telegram_bp.route('/api/telegram/info', methods=['GET'])
def telegram_bot_info():
    """Bot 정보 및 Webhook 상태 확인"""
    token = get_bot_token()
    if not token:
        return jsonify({"ok": False, "error": "TELEGRAM_BOT_TOKEN 미설정"}), 400

    result = {
        "bot_token_set": True,
        "chat_id_set": get_chat_id() is not None,
    }

    # Bot 정보 가져오기
    try:
        api_url = f"https://api.telegram.org/bot{token}/getMe"
        req = urllib.request.Request(api_url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            bot_info = json.loads(response.read().decode("utf-8"))
            if bot_info.get("ok"):
                result["bot"] = bot_info.get("result")
    except Exception as e:
        result["bot_error"] = str(e)

    # Webhook 정보 가져오기
    try:
        api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        req = urllib.request.Request(api_url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            webhook_info = json.loads(response.read().decode("utf-8"))
            if webhook_info.get("ok"):
                result["webhook"] = webhook_info.get("result")
    except Exception as e:
        result["webhook_error"] = str(e)

    return jsonify(result)


@telegram_bp.route('/api/telegram/send', methods=['POST'])
def telegram_send():
    """
    텔레그램 메시지 직접 전송 API

    Body:
    - text: 전송할 메시지
    - chat_id: (선택) 대상 채팅 ID
    """
    data = request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({"ok": False, "error": "text 필요"}), 400

    chat_id = data.get("chat_id")
    result = send_message(text, chat_id=chat_id)

    return jsonify(result)

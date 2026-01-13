"""
Dashboard Blueprint
대시보드 API 및 페이지

Routes:
- GET /dashboard - 대시보드 페이지
- GET /api/dashboard/quota - ElevenLabs 크레딧 조회
- GET /api/dashboard/tasks - 실행 중인 작업 조회
- GET /api/dashboard/videos - 최근 업로드 영상 조회
- GET /api/dashboard/logs - 최근 로그 조회
- POST /api/dashboard/run - 파이프라인 실행
"""

import os
import requests
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request

# Blueprint 생성
dashboard_bp = Blueprint('dashboard', __name__)

# 실행 중인 작업 추적 (telegram_bot과 공유)
try:
    from scripts.common.telegram_bot import _running_tasks, clear_task
except Exception:
    _running_tasks = {}
    clear_task = lambda x: None

# 최근 로그 저장 (메모리)
_recent_logs = []
MAX_LOGS = 100


def add_log(message: str):
    """로그 추가"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    _recent_logs.insert(0, f"[{timestamp}] {message}")
    if len(_recent_logs) > MAX_LOGS:
        _recent_logs.pop()


@dashboard_bp.route('/dashboard')
def dashboard_page():
    """대시보드 페이지"""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/quota')
def api_quota():
    """ElevenLabs 크레딧 조회"""
    try:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            return jsonify({"ok": False, "error": "API key not set"})

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
            reset_unix = data.get("next_character_count_reset_unix", 0)
            reset_date = datetime.fromtimestamp(reset_unix).strftime("%m/%d %H:%M") if reset_unix else None

            return jsonify({
                "ok": True,
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "reset_date": reset_date
            })
        else:
            return jsonify({"ok": False, "error": f"API error: {response.status_code}"})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@dashboard_bp.route('/api/dashboard/tasks')
def api_tasks():
    """실행 중인 작업 조회"""
    tasks = []
    now = datetime.now()

    for task_id, info in list(_running_tasks.items()):
        elapsed = (now - info["started"]).total_seconds()

        # 1시간 이상 된 작업은 자동 제거
        if elapsed > 3600:
            clear_task(task_id)
            continue

        # 경과 시간 포맷
        if elapsed < 60:
            elapsed_str = f"{int(elapsed)}s"
        elif elapsed < 3600:
            elapsed_str = f"{int(elapsed/60)}m"
        else:
            elapsed_str = f"{int(elapsed/3600)}h {int((elapsed%3600)/60)}m"

        tasks.append({
            "id": task_id,
            "name": info["name"],
            "elapsed": elapsed_str,
            "started": info["started"].isoformat()
        })

    return jsonify({"ok": True, "tasks": tasks})


@dashboard_bp.route('/api/dashboard/videos')
def api_videos():
    """최근 업로드 영상 조회"""
    videos = []

    # outputs 디렉토리에서 최근 영상 파일 검색
    output_dirs = [
        ("history", "outputs/history/videos"),
        ("isekai", "outputs/isekai/videos"),
        ("bible", "outputs/bible/videos"),
        ("shorts", "outputs/shorts/videos"),
    ]

    for pipeline, dir_path in output_dirs:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), dir_path)
        if not os.path.exists(full_path):
            continue

        try:
            for filename in os.listdir(full_path):
                if filename.endswith('.mp4'):
                    filepath = os.path.join(full_path, filename)
                    mtime = os.path.getmtime(filepath)
                    date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

                    videos.append({
                        "title": f"[{pipeline.upper()}] {filename}",
                        "date": date_str,
                        "pipeline": pipeline,
                        "url": None  # YouTube URL은 별도 조회 필요
                    })
        except Exception:
            continue

    # 최신순 정렬, 최대 20개
    videos.sort(key=lambda x: x["date"], reverse=True)
    return jsonify({"ok": True, "videos": videos[:20]})


@dashboard_bp.route('/api/dashboard/logs')
def api_logs():
    """최근 로그 조회"""
    return jsonify({"ok": True, "logs": _recent_logs[:50]})


@dashboard_bp.route('/api/dashboard/run', methods=['POST'])
def api_run():
    """파이프라인 실행"""
    data = request.get_json()
    pipeline = data.get("pipeline")
    episode = data.get("episode")

    if not pipeline:
        return jsonify({"ok": False, "error": "Pipeline required"})

    # 이미 실행 중인지 확인
    task_id = f"{pipeline}_{episode}" if episode else pipeline
    if task_id in _running_tasks:
        return jsonify({"ok": False, "error": f"Already running: {task_id}"})

    try:
        port = os.environ.get("PORT", "5059")
        base_url = f"http://127.0.0.1:{port}"

        if pipeline == "history":
            if not episode:
                return jsonify({"ok": False, "error": "Episode required for history"})
            endpoint = f"{base_url}/api/history/execute-episode"
            payload = {"episode": episode, "generate_video": True, "upload": False}

        elif pipeline == "isekai":
            if not episode:
                return jsonify({"ok": False, "error": "Episode required for isekai"})
            endpoint = f"{base_url}/api/isekai/execute-episode"
            payload = {"episode": episode, "generate_video": True, "upload": False}

        elif pipeline == "bible":
            endpoint = f"{base_url}/api/bible/check-and-process"
            payload = {}

        elif pipeline == "shorts":
            endpoint = f"{base_url}/api/shorts/check-and-process"
            payload = {}

        else:
            return jsonify({"ok": False, "error": f"Unknown pipeline: {pipeline}"})

        # 비동기 실행 (짧은 타임아웃)
        try:
            requests.post(endpoint, json=payload, timeout=2)
        except requests.exceptions.Timeout:
            pass  # 타임아웃은 정상 (백그라운드 실행)

        # 작업 등록
        _running_tasks[task_id] = {
            "name": f"{pipeline.capitalize()} EP{episode}" if episode else pipeline.capitalize(),
            "started": datetime.now(),
        }

        add_log(f"Started: {pipeline}" + (f" EP{episode}" if episode else ""))

        return jsonify({
            "ok": True,
            "message": f"{pipeline.capitalize()} pipeline started"
        })

    except Exception as e:
        add_log(f"Error starting {pipeline}: {e}")
        return jsonify({"ok": False, "error": str(e)})


# 외부에서 로그 추가할 수 있도록 export
def log_to_dashboard(message: str):
    """대시보드 로그에 추가 (외부 모듈용)"""
    add_log(message)

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
import json
import time
import glob
import requests
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, send_from_directory, Response

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


@dashboard_bp.route('/dashboard/scripts')
def dashboard_scripts_page():
    """대본 상세 페이지"""
    return render_template('dashboard_scripts.html')


@dashboard_bp.route('/dashboard/tts')
def dashboard_tts_page():
    """TTS 상세 페이지"""
    return render_template('dashboard_tts.html')


@dashboard_bp.route('/dashboard/images')
def dashboard_images_page():
    """이미지 상세 페이지"""
    return render_template('dashboard_images.html')


@dashboard_bp.route('/dashboard/script-writer')
def dashboard_script_writer_page():
    """대본 작성 페이지"""
    return render_template('dashboard_script_writer.html')


@dashboard_bp.route('/static/outputs/<path:filepath>')
def serve_output_file(filepath):
    """outputs 디렉토리 파일 서빙"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    outputs_dir = os.path.join(base_dir, "outputs")
    return send_from_directory(outputs_dir, filepath)


@dashboard_bp.route('/api/dashboard/script-content')
def api_script_content():
    """스크립트 내용 조회"""
    pipeline = request.args.get('pipeline')
    name = request.args.get('name')

    if not pipeline or not name:
        return jsonify({"ok": False, "error": "pipeline and name required"})

    base_dir = os.path.dirname(os.path.dirname(__file__))
    script_dirs = {
        "history": ["scripts/history_pipeline/episodes", "outputs/history/scripts"],
        "isekai": ["scripts/isekai_pipeline/episodes", "outputs/isekai/scripts"],
        "bible": ["outputs/bible/scripts"],
    }

    dirs = script_dirs.get(pipeline)
    if not dirs:
        return jsonify({"ok": False, "error": "Invalid pipeline"})

    # 여러 디렉토리에서 파일 찾기
    filepath = None
    for dir_path in dirs:
        check_path = os.path.join(base_dir, dir_path, name)
        if os.path.exists(check_path):
            filepath = check_path
            break

    if not filepath:
        return jsonify({"ok": False, "error": "Script not found"})

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"ok": True, "content": content})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@dashboard_bp.route('/api/dashboard/script-workspace')
def api_script_workspace():
    """Claude Code 작업 현황 조회 (파일 기반)"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    workspace_file = os.path.join(base_dir, "outputs/workspace/current_script.json")

    try:
        if os.path.exists(workspace_file):
            with open(workspace_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({"ok": True, **data})
        else:
            return jsonify({
                "ok": True,
                "status": "idle",
                "message": "Workspace not initialized"
            })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


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


@dashboard_bp.route('/api/dashboard/scripts')
def api_scripts():
    """최근 대본 파일 조회"""
    limit = request.args.get('limit', 15, type=int)
    scripts = []
    base_dir = os.path.dirname(os.path.dirname(__file__))

    script_dirs = [
        ("history", "scripts/history_pipeline/episodes"),
        ("history", "outputs/history/scripts"),  # 최종 대본
        ("isekai", "scripts/isekai_pipeline/episodes"),
        ("isekai", "outputs/isekai/scripts"),  # 최종 대본
        ("bible", "outputs/bible/scripts"),
    ]

    for pipeline, dir_path in script_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            continue

        try:
            for filename in os.listdir(full_path):
                # history/isekai는 .py 파일, bible은 .txt/.json 파일
                # 보조 파일 제외: _image_prompts, _data, _scene 등
                if filename.endswith(('.txt', '.json', '.py')) and not filename.startswith('__'):
                    # 보조 파일 스킵
                    if any(x in filename for x in ['_image_prompts', '_data', '_scene']):
                        continue
                    filepath = os.path.join(full_path, filename)
                    mtime = os.path.getmtime(filepath)
                    date_str = datetime.fromtimestamp(mtime).strftime("%m/%d %H:%M")
                    size_kb = os.path.getsize(filepath) / 1024

                    scripts.append({
                        "name": filename,
                        "date": date_str,
                        "size": f"{size_kb:.1f}KB",
                        "pipeline": pipeline,
                        "mtime": mtime
                    })
        except Exception:
            continue

    scripts.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify({"ok": True, "scripts": scripts[:limit]})


@dashboard_bp.route('/api/dashboard/tts')
def api_tts():
    """최근 TTS 파일 조회"""
    limit = request.args.get('limit', 15, type=int)
    tts_files = []
    base_dir = os.path.dirname(os.path.dirname(__file__))

    tts_dirs = [
        ("history", "outputs/history/tts"),
        ("isekai", "outputs/isekai/tts"),
        ("bible", "outputs/bible/tts"),
    ]

    for pipeline, dir_path in tts_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            continue

        try:
            for filename in os.listdir(full_path):
                if filename.endswith(('.mp3', '.wav')):
                    filepath = os.path.join(full_path, filename)
                    mtime = os.path.getmtime(filepath)
                    date_str = datetime.fromtimestamp(mtime).strftime("%m/%d %H:%M")
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)

                    # URL 생성
                    rel_path = os.path.relpath(filepath, os.path.join(base_dir, "outputs"))
                    url = f"/static/outputs/{rel_path}"

                    tts_files.append({
                        "name": filename,
                        "date": date_str,
                        "duration": f"{size_mb:.1f}MB",
                        "pipeline": pipeline,
                        "url": url,
                        "mtime": mtime
                    })
        except Exception:
            continue

    tts_files.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify({"ok": True, "tts": tts_files[:limit]})


@dashboard_bp.route('/api/dashboard/images')
def api_images():
    """최근 이미지 파일 조회 (썸네일, 씬)"""
    limit = request.args.get('limit', 20, type=int)
    images = []
    base_dir = os.path.dirname(os.path.dirname(__file__))

    image_dirs = [
        ("history", "outputs/history/thumbnails", "thumb"),
        ("history", "outputs/history/scenes", "scene"),
        ("isekai", "outputs/isekai/thumbnails", "thumb"),
        ("isekai", "outputs/isekai/scenes", "scene"),
        ("bible", "outputs/bible/thumbnails", "thumb"),
        ("bible", "outputs/bible/scenes", "scene"),
    ]

    for pipeline, dir_path, img_type in image_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            continue

        try:
            for filename in os.listdir(full_path):
                if filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    filepath = os.path.join(full_path, filename)
                    mtime = os.path.getmtime(filepath)

                    # 상대 URL 생성 (outputs 기준)
                    rel_path = os.path.relpath(filepath, os.path.join(base_dir, "outputs"))
                    url = f"/static/outputs/{rel_path}"

                    images.append({
                        "name": filename,
                        "type": img_type,
                        "pipeline": pipeline,
                        "url": url,
                        "mtime": mtime
                    })
        except Exception:
            continue

    images.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify({"ok": True, "images": images[:limit]})


# 외부에서 로그 추가할 수 있도록 export
def log_to_dashboard(message: str):
    """대시보드 로그에 추가 (외부 모듈용)"""
    add_log(message)

"""
History Pipeline Blueprint
한국사 자동화 파이프라인 API

Routes:
- /api/history/run-pipeline: 파이프라인 실행
- /api/history/test: 테스트 (시트 저장 없이)
- /api/history/test-topic: 주제 기반 테스트
- /api/history/auto-generate: 대본 자동 생성
- /api/history/status: 전체 현황 조회
- /api/history/execute-episode: 에피소드 파일로 영상 생성
- /api/history/execute-background: 백그라운드 실행 (대시보드용)
- /api/history/job-status: 작업 상태 조회
"""

import os
import threading
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

# Blueprint 생성
history_bp = Blueprint('history', __name__)


@history_bp.route('/history')
def history_dashboard_page():
    """History Pipeline 대시보드 페이지"""
    return render_template('history_dashboard.html')


@history_bp.route('/script-editor')
def script_image_editor_page():
    """Script-Image Editor 페이지 (대본-이미지 프롬프트 매칭)"""
    return render_template('script_image_editor.html')

# 백그라운드 작업 추적
_history_jobs = {}  # {job_id: {status, episode_id, started_at, result, error}}

# 의존성 주입
_get_sheets_service = None


def set_sheets_service_getter(func):
    """Google Sheets 서비스 getter 함수 주입"""
    global _get_sheets_service
    _get_sheets_service = func


@history_bp.route('/api/history/run-pipeline', methods=['GET', 'POST'])
def api_history_run_pipeline():
    """
    한국사 자동화 파이프라인 실행 (에피소드 자동 관리)
    브라우저에서 직접 호출 가능 (GET 지원)

    ★ 자동으로 PENDING 10개 유지
    ★ 시대 순서: 고조선 → 부여 → 삼국 → 남북국 → 고려 → 조선전기 → 조선후기 → 대한제국
    ★ AI가 시대별 에피소드 수 결정

    파라미터:
    - force: "1"이면 PENDING 10개 이상이어도 1개 추가

    환경변수:
    - NEWS_SHEET_ID: 뉴스 파이프라인과 같은 시트 사용 (권장)
    - HISTORY_SHEET_ID: 한국사 전용 시트 (선택)
    """
    print("[HISTORY] ===== run-pipeline 호출됨 =====")

    try:
        from scripts.history_pipeline import run_history_pipeline

        if not _get_sheets_service:
            return jsonify({"ok": False, "error": "Sheets 서비스가 설정되지 않았습니다"}), 500

        service = _get_sheets_service()
        if not service:
            return jsonify({
                "ok": False,
                "error": "Google Sheets 서비스 계정이 설정되지 않았습니다"
            }), 400

        sheet_id = (
            os.environ.get('HISTORY_SHEET_ID') or
            os.environ.get('NEWS_SHEET_ID') or
            os.environ.get('AUTOMATION_SHEET_ID')
        )
        if not sheet_id:
            return jsonify({
                "ok": False,
                "error": "HISTORY_SHEET_ID, NEWS_SHEET_ID, 또는 AUTOMATION_SHEET_ID 환경변수가 필요합니다"
            }), 400

        force = request.args.get('force', '0') == '1'
        print(f"[HISTORY] force: {force}, 시트 ID: {sheet_id}")

        result = run_history_pipeline(
            sheet_id=sheet_id,
            service=service,
            force=force
        )

        if result.get("success"):
            return jsonify({
                "ok": True,
                "pending_before": result.get("pending_before", 0),
                "pending_after": result.get("pending_after", 0),
                "episodes_added": result.get("episodes_added", 0),
                "current_era": result.get("current_era"),
                "current_episode": result.get("current_episode", 0),
                "all_complete": result.get("all_complete", False),
                "details": result.get("details", []),
                "message": f"{result.get('episodes_added', 0)}개 에피소드 추가, PENDING {result.get('pending_after', 0)}개"
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.get("error", "알 수 없는 오류"),
                "details": result.get("details", [])
            }), 500

    except ImportError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": f"모듈 로드 실패: {e}"
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/test', methods=['GET'])
def api_history_test():
    """
    [DEPRECATED] 주제 기반 수집으로 전환되었습니다.
    대신 /api/history/test-topic?era={era}&episode=1 사용하세요.
    """
    era = request.args.get('era', 'GOJOSEON').upper()

    return jsonify({
        "ok": False,
        "deprecated": True,
        "error": "이 API는 더 이상 지원되지 않습니다.",
        "migration": f"/api/history/test-topic?era={era}&episode=1",
        "message": "주제 기반 수집(/api/history/test-topic)을 사용하세요."
    }), 410  # 410 Gone


@history_bp.route('/api/history/test-topic', methods=['GET'])
def api_history_test_topic():
    """
    주제 기반 자료 수집 테스트

    파라미터:
    - era: 시대 키 (기본 GOJOSEON)
    - episode: 시대 내 에피소드 번호 (기본 1)
    """
    try:
        from scripts.history_pipeline import (
            ERAS, ERA_ORDER, HISTORY_TOPICS,
            collect_topic_materials,
            get_total_episode_count,
        )

        era = request.args.get('era', 'GOJOSEON').upper()
        episode = int(request.args.get('episode', '1'))

        if era not in ERAS:
            return jsonify({
                "ok": False,
                "error": f"알 수 없는 시대: {era}",
                "valid_eras": list(ERAS.keys())
            }), 400

        topics = HISTORY_TOPICS.get(era, [])
        if episode < 1 or episode > len(topics):
            return jsonify({
                "ok": False,
                "error": f"{era}에 {episode}화 없음 (1~{len(topics)}화 가능)",
                "available_episodes": [
                    {"episode": i+1, "title": t.get("title")}
                    for i, t in enumerate(topics)
                ]
            }), 400

        era_info = ERAS[era]
        topic_info = topics[episode - 1]

        collected = collect_topic_materials(era, episode)

        return jsonify({
            "ok": True,
            "era": era,
            "era_name": era_info.get("name"),
            "period": era_info.get("period"),
            "episode": episode,
            "total_episodes": len(topics),
            "topic": {
                "title": topic_info.get("title"),
                "topic": topic_info.get("topic"),
                "keywords": topic_info.get("keywords"),
                "description": topic_info.get("description"),
                "reference_links": topic_info.get("reference_links"),
            },
            "collected": {
                "materials_count": len(collected.get("materials", [])),
                "content_length": len(collected.get("full_content", "")),
                "sources": collected.get("sources", []),
                "content_preview": collected.get("full_content", "")[:2000],
            },
            "all_topics": [
                {"episode": i+1, "title": t.get("title"), "topic": t.get("topic")}
                for i, t in enumerate(topics)
            ],
            "total_series_episodes": get_total_episode_count(),
        })

    except ImportError as e:
        return jsonify({
            "ok": False,
            "error": f"모듈 로드 실패: {e}"
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/auto-generate', methods=['GET', 'POST'])
def api_history_auto_generate():
    """
    한국사 대본 자동 생성 (GPT-5.1 파트별 생성)

    ★ '준비' 상태 에피소드를 찾아 GPT-5.1로 대본 자동 생성
    ★ 파트별 생성 (인트로 → 배경 → 본론 → 마무리)

    파라미터:
    - max_scripts: 한번에 생성할 최대 대본 수 (기본 1)
    - force: "1"이면 이미 대본이 있어도 재생성
    """
    print("[HISTORY] ===== auto-generate 호출됨 =====")

    try:
        from scripts.history_pipeline import run_auto_script_pipeline

        if not _get_sheets_service:
            return jsonify({"ok": False, "error": "Sheets 서비스가 설정되지 않았습니다"}), 500

        service = _get_sheets_service()
        if not service:
            return jsonify({
                "ok": False,
                "error": "Google Sheets 서비스 계정이 설정되지 않았습니다"
            }), 400

        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({
                "ok": False,
                "error": "OPENAI_API_KEY 환경변수가 필요합니다"
            }), 400

        sheet_id = (
            os.environ.get('HISTORY_SHEET_ID') or
            os.environ.get('NEWS_SHEET_ID') or
            os.environ.get('AUTOMATION_SHEET_ID')
        )
        if not sheet_id:
            return jsonify({
                "ok": False,
                "error": "HISTORY_SHEET_ID, NEWS_SHEET_ID, 또는 AUTOMATION_SHEET_ID 환경변수가 필요합니다"
            }), 400

        max_scripts = int(request.args.get('max_scripts', '1'))
        force = request.args.get('force', '0') == '1'

        print(f"[HISTORY] max_scripts: {max_scripts}, force: {force}")

        result = run_auto_script_pipeline(
            sheet_id=sheet_id,
            service=service,
            max_scripts=max_scripts
        )

        if result.get("success"):
            return jsonify({
                "ok": True,
                "generated": result.get("generated", 0),
                "episodes": result.get("episodes", []),
                "total_cost": result.get("total_cost", 0),
                "message": f"{result.get('generated', 0)}개 대본 생성 완료"
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.get("error", "알 수 없는 오류"),
                "details": result.get("details", [])
            }), 500

    except ImportError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": f"모듈 로드 실패: {e}"
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/status', methods=['GET'])
def api_history_status():
    """
    한국사 시리즈 전체 현황 조회

    파라미터:
    - episode: 특정 에피소드 파일 정보 조회 (선택)

    응답:
    - 전체 에피소드 수 (60화)
    - 시대별 에피소드 목록
    - 현재 진행 상황 (시트 연결 시)
    """
    try:
        # 특정 에피소드 조회
        episode_num = request.args.get('episode')
        if episode_num:
            return _get_episode_file_info(int(episode_num))

        from scripts.history_pipeline import (
            ERAS, ERA_ORDER, HISTORY_TOPICS,
            get_total_episode_count,
        )

        status = {
            "ok": True,
            "total_episodes": get_total_episode_count(),
            "eras": [],
        }

        episode_num = 0
        for era in ERA_ORDER:
            topics = HISTORY_TOPICS.get(era, [])
            era_info = ERAS.get(era, {})

            era_data = {
                "key": era,
                "name": era_info.get("name", era),
                "period": era_info.get("period", ""),
                "episode_count": len(topics),
                "start_episode": episode_num + 1,
                "end_episode": episode_num + len(topics),
                "topics": [
                    {
                        "global_episode": episode_num + i + 1,
                        "era_episode": i + 1,
                        "title": t.get("title"),
                        "topic": t.get("topic"),
                    }
                    for i, t in enumerate(topics)
                ]
            }
            status["eras"].append(era_data)
            episode_num += len(topics)

        return jsonify(status)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


def _get_episode_file_info(episode_num: int):
    """에피소드 파일 정보 조회"""
    import importlib.util
    import glob as glob_module

    episode_id = f"ep{episode_num:03d}"
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    episode_files = glob_module.glob(os.path.join(
        base_path, "scripts", "history_pipeline", "episodes", f"{episode_id}_*.py"
    ))

    main_file = None
    image_prompts_file = None
    for f in episode_files:
        if "image_prompts" in f:
            image_prompts_file = f
        elif "data" not in f:
            main_file = f

    if not main_file:
        return jsonify({
            "ok": False,
            "error": f"{episode_id} 에피소드 파일 없음"
        }), 404

    try:
        spec = importlib.util.spec_from_file_location(f"{episode_id}_main", main_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        episode_info = getattr(module, 'EPISODE_INFO', {})
        script = getattr(module, 'SCRIPT', '')
        metadata = getattr(module, 'METADATA', {})

        # 이미지 프롬프트 수
        image_count = 0
        if image_prompts_file:
            img_spec = importlib.util.spec_from_file_location(f"{episode_id}_img", image_prompts_file)
            img_module = importlib.util.module_from_spec(img_spec)
            img_spec.loader.exec_module(img_module)
            image_prompts = getattr(img_module, 'IMAGE_PROMPTS', [])
            image_count = len(image_prompts)

        return jsonify({
            "ok": True,
            "episode": {
                "episode_id": episode_id,
                "title": episode_info.get('title') or metadata.get('title') or f'한국사 {episode_num}화',
                "script_length": len(script),
                "image_count": image_count,
                "has_script": bool(script),
                "has_metadata": bool(metadata),
            }
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"파일 로드 실패: {e}"
        }), 500


@history_bp.route('/api/history/execute-episode', methods=['GET', 'POST'])
def api_history_execute_episode():
    """
    에피소드 파일에서 데이터를 로드하여 영상 생성 파이프라인 실행

    파라미터:
    - episode: 에피소드 번호 (예: 21)
    - generate_video: 영상 렌더링 여부 (기본 true)
    - upload: YouTube 업로드 여부 (기본 false)
    - privacy_status: 공개 설정 (기본 private)

    예시:
    - GET /api/history/execute-episode?episode=21
    - GET /api/history/execute-episode?episode=21&upload=1&privacy_status=public
    """
    print("[HISTORY] ===== execute-episode 호출됨 =====")

    try:
        import importlib.util
        import glob as glob_module
        from scripts.history_pipeline import execute_episode

        episode_num = request.args.get('episode')
        if not episode_num and request.is_json:
            episode_num = request.json.get('episode')
        if not episode_num:
            return jsonify({
                "ok": False,
                "error": "episode 파라미터가 필요합니다 (예: ?episode=21)"
            }), 400

        episode_num = int(episode_num)
        episode_id = f"ep{episode_num:03d}"

        # 에피소드 파일 경로
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        episode_files = glob_module.glob(os.path.join(
            base_path, "scripts", "history_pipeline", "episodes", f"{episode_id}_*.py"
        ))

        # 메인 에피소드 파일 찾기 (image_prompts 제외)
        main_file = None
        image_prompts_file = None
        for f in episode_files:
            if "image_prompts" in f:
                image_prompts_file = f
            elif "data" not in f:  # _data 파일 제외
                main_file = f

        if not main_file:
            return jsonify({
                "ok": False,
                "error": f"{episode_id} 에피소드 파일을 찾을 수 없습니다",
                "searched_path": os.path.join(base_path, "scripts", "history_pipeline", "episodes"),
                "found_files": episode_files
            }), 404

        # 메인 모듈 로드
        spec = importlib.util.spec_from_file_location(f"{episode_id}_main", main_file)
        episode_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(episode_module)

        # 필수 데이터 추출
        episode_info = getattr(episode_module, 'EPISODE_INFO', {})
        script = getattr(episode_module, 'SCRIPT', '')
        metadata = getattr(episode_module, 'METADATA', {})
        brief = getattr(episode_module, 'BRIEF', None)
        thumbnail = getattr(episode_module, 'THUMBNAIL', None)

        if not script:
            return jsonify({
                "ok": False,
                "error": f"{episode_id} 대본(SCRIPT)이 없습니다"
            }), 400

        # 이미지 프롬프트 로드
        image_prompts = []
        if image_prompts_file:
            img_spec = importlib.util.spec_from_file_location(f"{episode_id}_image_prompts", image_prompts_file)
            img_module = importlib.util.module_from_spec(img_spec)
            img_spec.loader.exec_module(img_module)
            image_prompts = getattr(img_module, 'IMAGE_PROMPTS', [])

        # 파라미터 처리
        generate_video = request.args.get('generate_video', '1') != '0'
        upload = request.args.get('upload', '0') == '1'
        privacy_status = request.args.get('privacy_status', 'private')

        title = episode_info.get('title', f'한국사 {episode_num}화')

        print(f"[HISTORY] 에피소드: {episode_id}")
        print(f"[HISTORY] 제목: {title}")
        print(f"[HISTORY] 대본 길이: {len(script):,}자")
        print(f"[HISTORY] 이미지 프롬프트: {len(image_prompts)}개")
        print(f"[HISTORY] 영상 생성: {generate_video}, 업로드: {upload}")

        # 실행
        result = execute_episode(
            episode_id=episode_id,
            title=title,
            script=script,
            image_prompts=image_prompts,
            metadata=metadata,
            brief=brief,
            generate_video=generate_video,
            upload=upload,
            privacy_status=privacy_status,
            thumbnail_config=thumbnail,
        )

        if result.get("ok"):
            return jsonify({
                "ok": True,
                "episode_id": episode_id,
                "title": title,
                "script_length": len(script),
                "image_count": len(image_prompts),
                "audio_path": result.get("audio_path"),
                "video_path": result.get("video_path"),
                "youtube_url": result.get("youtube_url"),
                "duration": result.get("duration"),
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.get("error", "알 수 없는 오류"),
                "episode_id": episode_id,
            }), 500

    except ImportError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": f"모듈 로드 실패: {e}"
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/execute-background', methods=['GET', 'POST'])
def api_history_execute_background():
    """
    백그라운드에서 에피소드 실행 (대시보드용)
    즉시 job_id 반환, 실제 작업은 백그라운드에서 진행

    파라미터:
    - episode: 에피소드 번호 (예: 22)
    - upload: YouTube 업로드 여부 (기본 true)
    - privacy_status: 공개 설정 (기본 private)

    응답:
    {
        "ok": true,
        "job_id": "abc-123",
        "message": "작업이 시작되었습니다"
    }
    """
    try:
        import importlib.util
        import glob as glob_module
        from scripts.history_pipeline import execute_episode

        # 파라미터 추출
        episode_num = request.args.get('episode')
        if not episode_num and request.is_json:
            episode_num = request.json.get('episode')
        if not episode_num:
            return jsonify({"ok": False, "error": "episode 파라미터가 필요합니다"}), 400

        episode_num = int(episode_num)
        episode_id = f"ep{episode_num:03d}"

        # 이미 실행 중인지 확인
        for job_id, job in _history_jobs.items():
            if job.get("episode_id") == episode_id and job.get("status") == "running":
                return jsonify({
                    "ok": False,
                    "error": f"{episode_id} 이미 실행 중입니다",
                    "job_id": job_id
                }), 409

        # 에피소드 파일 로드
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        episode_files = glob_module.glob(os.path.join(
            base_path, "scripts", "history_pipeline", "episodes", f"{episode_id}_*.py"
        ))

        main_file = None
        image_prompts_file = None
        for f in episode_files:
            if "image_prompts" in f:
                image_prompts_file = f
            elif "data" not in f:
                main_file = f

        if not main_file:
            return jsonify({"ok": False, "error": f"{episode_id} 에피소드 파일 없음"}), 404

        # 모듈 로드
        spec = importlib.util.spec_from_file_location(f"{episode_id}_main", main_file)
        episode_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(episode_module)

        episode_info = getattr(episode_module, 'EPISODE_INFO', {})
        script = getattr(episode_module, 'SCRIPT', '')
        metadata = getattr(episode_module, 'METADATA', {})
        brief = getattr(episode_module, 'BRIEF', None)
        thumbnail = getattr(episode_module, 'THUMBNAIL', None)

        if not script:
            return jsonify({"ok": False, "error": f"{episode_id} 대본 없음"}), 400

        # 이미지 프롬프트 로드
        image_prompts = []
        if image_prompts_file:
            img_spec = importlib.util.spec_from_file_location(f"{episode_id}_image_prompts", image_prompts_file)
            img_module = importlib.util.module_from_spec(img_spec)
            img_spec.loader.exec_module(img_module)
            image_prompts = getattr(img_module, 'IMAGE_PROMPTS', [])

        # 파라미터
        upload = request.args.get('upload', '1') == '1'  # 기본 True
        privacy_status = request.args.get('privacy_status', 'private')
        title = episode_info.get('title', f'한국사 {episode_num}화')

        # Job 생성
        job_id = str(uuid.uuid4())[:8]
        _history_jobs[job_id] = {
            "status": "running",
            "episode_id": episode_id,
            "title": title,
            "started_at": datetime.now().isoformat(),
            "result": None,
            "error": None,
        }

        # 백그라운드 실행 함수
        def run_in_background():
            try:
                print(f"[HISTORY-BG] {episode_id} 백그라운드 실행 시작")
                result = execute_episode(
                    episode_id=episode_id,
                    title=title,
                    script=script,
                    image_prompts=image_prompts,
                    metadata=metadata,
                    brief=brief,
                    generate_video=True,
                    upload=upload,
                    privacy_status=privacy_status,
                    thumbnail_config=thumbnail,
                )

                _history_jobs[job_id]["status"] = "completed" if result.get("ok") else "failed"
                _history_jobs[job_id]["result"] = result
                _history_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                print(f"[HISTORY-BG] {episode_id} 완료: {result.get('ok')}")

            except Exception as e:
                import traceback
                traceback.print_exc()
                _history_jobs[job_id]["status"] = "failed"
                _history_jobs[job_id]["error"] = str(e)
                _history_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                print(f"[HISTORY-BG] {episode_id} 실패: {e}")

        # 스레드 시작
        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()

        print(f"[HISTORY-BG] {episode_id} 작업 시작됨 (job_id: {job_id})")

        return jsonify({
            "ok": True,
            "job_id": job_id,
            "episode_id": episode_id,
            "title": title,
            "message": f"{episode_id} 백그라운드 실행 시작됨",
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/job-status', methods=['GET'])
def api_history_job_status():
    """
    백그라운드 작업 상태 조회

    파라미터:
    - job_id: 작업 ID (선택, 없으면 전체 목록)

    응답:
    {
        "ok": true,
        "job": {...} 또는 "jobs": [...]
    }
    """
    job_id = request.args.get('job_id')

    if job_id:
        job = _history_jobs.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "작업을 찾을 수 없습니다"}), 404
        return jsonify({"ok": True, "job": job})

    # 전체 목록 (최근 10개)
    jobs = sorted(
        [{"job_id": k, **v} for k, v in _history_jobs.items()],
        key=lambda x: x.get("started_at", ""),
        reverse=True
    )[:10]

    return jsonify({"ok": True, "jobs": jobs})


@history_bp.route('/api/history/script-image-matching', methods=['GET'])
def api_history_script_image_matching():
    """
    대본-이미지 매칭 검증 API

    대본을 문단 단위로 나누고, 각 문단에 해당하는 이미지 프롬프트를 보여줍니다.
    대시보드에서 대본과 이미지가 제대로 매칭되는지 확인할 수 있습니다.

    파라미터:
    - episode: 에피소드 번호 (예: 22)

    응답:
    {
        "ok": true,
        "episode_id": "ep022",
        "title": "거란과의 전쟁",
        "script_length": 13500,
        "estimated_duration_sec": 1800,
        "sections": [
            {
                "index": 0,
                "start_sec": 0,
                "end_sec": 60,
                "text": "993년 가을이었어요...",
                "image": {
                    "timestamp_sec": 0,
                    "prompt": "Epic scene..."
                }
            },
            ...
        ]
    }
    """
    try:
        import importlib.util
        import glob as glob_module

        episode_num = request.args.get('episode')
        if not episode_num:
            return jsonify({"ok": False, "error": "episode 파라미터가 필요합니다"}), 400

        episode_num = int(episode_num)
        episode_id = f"ep{episode_num:03d}"

        # 에피소드 파일 로드
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        episode_files = glob_module.glob(os.path.join(
            base_path, "scripts", "history_pipeline", "episodes", f"{episode_id}_*.py"
        ))

        main_file = None
        image_prompts_file = None
        for f in episode_files:
            if "image_prompts" in f:
                image_prompts_file = f
            elif "data" not in f:
                main_file = f

        if not main_file:
            return jsonify({"ok": False, "error": f"{episode_id} 에피소드 파일 없음"}), 404

        # 메인 모듈 로드
        spec = importlib.util.spec_from_file_location(f"{episode_id}_main", main_file)
        episode_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(episode_module)

        episode_info = getattr(episode_module, 'EPISODE_INFO', {})
        script = getattr(episode_module, 'SCRIPT', '')

        if not script:
            return jsonify({"ok": False, "error": "대본 없음"}), 400

        # 이미지 프롬프트 로드
        image_prompts = []
        if image_prompts_file:
            img_spec = importlib.util.spec_from_file_location(f"{episode_id}_image_prompts", image_prompts_file)
            img_module = importlib.util.module_from_spec(img_spec)
            img_spec.loader.exec_module(img_module)
            image_prompts = getattr(img_module, 'IMAGE_PROMPTS', [])

        # 대본을 문단 단위로 분할
        paragraphs = [p.strip() for p in script.strip().split('\n\n') if p.strip()]

        # TTS 기준 예상 시간 계산 (21화 실측: 6.4자/초)
        chars_per_sec = 6.4  # 초당 약 6.4자 (21화 기준 실측)
        total_chars = len(script.replace('\n', '').replace(' ', ''))
        estimated_duration = total_chars / chars_per_sec

        # 각 문단의 시작 시간 계산
        sections = []
        current_time = 0

        for i, para in enumerate(paragraphs):
            para_chars = len(para.replace('\n', '').replace(' ', ''))
            para_duration = para_chars / chars_per_sec

            # 이 시간대에 해당하는 이미지 찾기
            matching_image = None
            for img in image_prompts:
                img_time = img.get('timestamp_sec', 0) if isinstance(img, dict) else 0
                if current_time <= img_time < current_time + para_duration:
                    matching_image = img
                    break

            sections.append({
                "index": i,
                "start_sec": round(current_time, 1),
                "end_sec": round(current_time + para_duration, 1),
                "text": para[:200] + "..." if len(para) > 200 else para,
                "text_full": para,
                "char_count": para_chars,
                "image": matching_image
            })

            current_time += para_duration

        # 이미지 프롬프트 중 매칭되지 않은 것들 확인
        matched_images = set()
        for sec in sections:
            if sec.get('image'):
                img_time = sec['image'].get('timestamp_sec', 0) if isinstance(sec['image'], dict) else 0
                matched_images.add(img_time)

        unmatched_images = []
        for img in image_prompts:
            img_time = img.get('timestamp_sec', 0) if isinstance(img, dict) else 0
            if img_time not in matched_images:
                unmatched_images.append(img)

        # 문제점 분석
        issues = []
        if estimated_duration > 0:
            last_image_time = max(
                (img.get('timestamp_sec', 0) if isinstance(img, dict) else 0)
                for img in image_prompts
            ) if image_prompts else 0

            if last_image_time < estimated_duration * 0.8:
                issues.append(f"마지막 이미지({last_image_time}초)가 대본 끝({round(estimated_duration)}초)보다 너무 앞에 있음")

        if unmatched_images:
            issues.append(f"{len(unmatched_images)}개 이미지가 대본과 매칭되지 않음")

        sections_without_image = sum(1 for s in sections if not s.get('image'))
        if sections_without_image > len(sections) * 0.5:
            issues.append(f"{sections_without_image}개 문단에 이미지 없음 (전체 {len(sections)}개)")

        # timestamp_sec를 키로 하는 프롬프트 맵 생성
        prompts_by_timestamp = {}
        for img in image_prompts:
            ts = img.get('timestamp_sec', 0) if isinstance(img, dict) else 0
            prompts_by_timestamp[ts] = img.get('prompt', '') if isinstance(img, dict) else ''

        return jsonify({
            "ok": True,
            "episode_id": episode_id,
            "title": episode_info.get('title', f'한국사 {episode_num}화'),
            "script_length": len(script),
            "estimated_duration_sec": round(estimated_duration, 1),
            "total_paragraphs": len(paragraphs),
            "total_images": len(image_prompts),
            "sections": sections,
            "unmatched_images": unmatched_images,
            "issues": issues,
            "prompts_by_timestamp": prompts_by_timestamp,  # timestamp -> prompt 맵
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/generate-image', methods=['POST'])
def api_history_generate_image():
    """
    단일 이미지 생성 API

    Input:
    {
        "episode_id": "ep022",
        "timestamp_sec": 0,
        "prompt": "establishing_shot, massive Khitan cavalry..."
    }

    Output:
    {
        "ok": true,
        "image_url": "/outputs/history/images/ep022_0000.png",
        "timestamp_sec": 0
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data"}), 400

        episode_id = data.get("episode_id")
        timestamp_sec = data.get("timestamp_sec", 0)
        prompt = data.get("prompt", "")
        use_gpu = data.get("use_gpu", True)  # 기본값: GPU 사용

        if not episode_id or not prompt:
            return jsonify({"ok": False, "error": "episode_id and prompt required"}), 400

        # 스타일 프리픽스 추가
        style_prefix = """Korean webtoon style meets Studio Ghibli and modern flat illustration,
clean line art with soft warm lighting, vibrant yet gentle colors,
cel shading with subtle gradients, dynamic composition but peaceful atmosphere,
hand-painted feel with clean aesthetic, accessible and friendly, bright warm palette."""

        full_prompt = f"{style_prefix}\n\n{prompt}"

        # 출력 디렉토리
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_path, "outputs", "history", "images")
        os.makedirs(output_dir, exist_ok=True)

        # 이미지 생성 (GPU/ComfyUI 우선)
        if use_gpu:
            import os as os_env
            os_env.environ['COMFYUI_ENABLED'] = 'true'
            os_env.environ['COMFYUI_MODEL'] = 'flux'
            from image.comfyui import generate_image_comfyui
            result = generate_image_comfyui(
                prompt=full_prompt,
                size="1024x576",
                steps=2
            )
        else:
            from image.gemini import generate_image
            result = generate_image(
                prompt=full_prompt,
                size="1280x720",
                output_dir=output_dir,
                add_aspect_instruction=True
            )

        if result.get("ok"):
            # 파일명 변경: episode_id_timestamp.ext
            original_path = result.get("image_url", "")

            # 절대 경로로 변환
            if os.path.isabs(original_path):
                # 이미 절대 경로면 그대로 사용
                original_full_path = original_path
            else:
                # 상대 경로인 경우 base_path 기준으로 변환
                original_full_path = os.path.join(base_path, original_path)

            # 새 파일명 (원본 확장자 유지)
            original_ext = os.path.splitext(original_full_path)[1] or ".jpg"
            new_filename = f"{episode_id}_{timestamp_sec:04d}{original_ext}"
            new_path = os.path.join(output_dir, new_filename)

            # 파일 이동
            if os.path.exists(original_full_path) and original_full_path != new_path:
                import shutil
                shutil.move(original_full_path, new_path)

            image_url = f"/outputs/history/images/{new_filename}"

            return jsonify({
                "ok": True,
                "image_url": image_url,
                "timestamp_sec": timestamp_sec,
                "cost": result.get("cost", 0)
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.get("error", "Image generation failed")
            }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/generate-video', methods=['POST'])
def api_history_generate_video():
    """
    이미지를 영상으로 변환 (FFmpeg 팬/줌 효과)

    Input:
    {
        "image_path": "outputs/history/images/ep022_001.jpg",
        "effect": "zoom_in",  // zoom_in, zoom_out, pan_left, pan_right, random
        "duration": 5.0  // 초
    }

    Output:
    {
        "ok": true,
        "video_path": "outputs/history/videos/ep022_001.mp4",
        "effect": "zoom_in",
        "duration": 5.0
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data"}), 400

        image_path = data.get("image_path")
        effect = data.get("effect", "random")
        duration = float(data.get("duration", 5.0))

        if not image_path:
            return jsonify({"ok": False, "error": "image_path required"}), 400

        # 절대 경로 변환
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isabs(image_path):
            image_path = os.path.join(base_path, image_path)

        if not os.path.exists(image_path):
            return jsonify({"ok": False, "error": f"이미지 파일 없음: {image_path}"}), 404

        # 출력 경로 생성
        video_dir = os.path.join(base_path, "outputs", "history", "videos")
        os.makedirs(video_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(video_dir, f"{base_name}.mp4")

        # 영상 생성
        from image.video_effects import image_to_video
        result = image_to_video(
            image_path=image_path,
            output_path=output_path,
            effect=effect,
            duration=duration,
        )

        if result["ok"]:
            # 상대 경로로 변환해서 반환
            rel_path = os.path.relpath(output_path, base_path)
            return jsonify({
                "ok": True,
                "video_path": rel_path,
                "effect": result.get("effect", effect),
                "duration": duration,
            })
        else:
            return jsonify(result), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/generate-videos-batch', methods=['POST'])
def api_history_generate_videos_batch():
    """
    여러 이미지를 일괄 영상 변환

    Input:
    {
        "image_paths": ["outputs/history/images/ep022_001.jpg", ...],
        "effect": "random",  // random이면 각각 다른 효과
        "duration": 5.0
    }

    Output:
    {
        "ok": true,
        "results": [...],
        "success_count": 10,
        "fail_count": 0
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data"}), 400

        image_paths = data.get("image_paths", [])
        effect = data.get("effect", "random")
        duration = float(data.get("duration", 5.0))

        if not image_paths:
            return jsonify({"ok": False, "error": "image_paths required"}), 400

        # 절대 경로 변환
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_paths = []
        for p in image_paths:
            if os.path.isabs(p):
                abs_paths.append(p)
            else:
                abs_paths.append(os.path.join(base_path, p))

        # 출력 디렉토리
        video_dir = os.path.join(base_path, "outputs", "history", "videos")

        # 일괄 변환
        from image.video_effects import batch_image_to_video
        result = batch_image_to_video(
            image_paths=abs_paths,
            output_dir=video_dir,
            effect=effect,
            duration=duration,
        )

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/save-image-prompts', methods=['POST'])
def api_history_save_image_prompts():
    """
    이미지 프롬프트 저장 API

    대시보드에서 편집한 이미지 프롬프트를 파일로 저장합니다.

    Input:
    {
        "episode_id": "ep022",
        "image_prompts": [
            {"timestamp_sec": 0, "prompt": "..."},
            {"timestamp_sec": 10, "prompt": "..."},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data"}), 400

        episode_id = data.get("episode_id")
        image_prompts = data.get("image_prompts", [])

        if not episode_id:
            return jsonify({"ok": False, "error": "episode_id required"}), 400

        # 저장 경로
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompts_file = os.path.join(
            base_path, "scripts", "history_pipeline", "episodes",
            f"{episode_id}_image_prompts.py"
        )

        # 스타일 프리픽스
        style_prefix = """Korean webtoon style meets Studio Ghibli and modern flat illustration,
clean line art with soft warm lighting,
vibrant yet gentle colors,
cel shading with subtle gradients,
dynamic composition but peaceful atmosphere,
hand-painted feel with clean aesthetic,
accessible and friendly,
bright warm palette,
16:9 aspect ratio."""

        # Python 파일 생성
        content = f'''"""
{episode_id} 이미지 프롬프트
Auto-generated by Script-Image Editor
"""

STYLE_PREFIX = """{style_prefix}"""

IMAGE_PROMPTS = [
'''
        for p in image_prompts:
            ts = p.get("timestamp_sec", 0)
            prompt = p.get("prompt", "").replace('"""', '\\"\\"\\"').replace("'''", "\\'\\'\\'")
            content += f'''    {{
        "timestamp_sec": {ts},
        "prompt": """{prompt}"""
    }},
'''

        content += "]\n"

        # 파일 저장
        os.makedirs(os.path.dirname(prompts_file), exist_ok=True)
        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({
            "ok": True,
            "episode_id": episode_id,
            "saved_count": len(image_prompts),
            "file_path": prompts_file
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/history/tts', methods=['POST'])
def api_history_tts():
    """
    History TTS 생성 (ElevenLabs)

    Input:
    {
        "episode_id": "test",
        "script": "대본 텍스트...",
        "voice": "aurnUodFzOtofecLd3T1",  # ElevenLabs voice_id (선택)
        "speed": 0.95  # 속도 (선택, 기본 1.0)
    }

    Output:
    {
        "ok": true,
        "audio_path": "outputs/audio/test_full.mp3",
        "audio_url": "/outputs/audio/test_full.mp3",
        "srt_path": "outputs/subtitles/test.srt",
        "duration": 60.5
    }
    """
    print("[HISTORY-TTS] ===== TTS API 호출됨 =====")

    try:
        from scripts.history_pipeline.tts import generate_tts

        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data received"}), 400

        episode_id = data.get("episode_id", "tts_test")
        script = data.get("script", "")
        voice = data.get("voice")  # ElevenLabs voice_id
        speed = data.get("speed", 1.0)

        if not script:
            return jsonify({"ok": False, "error": "script가 필요합니다"}), 400

        # --- 구분선 제거
        script = script.replace('\n---\n', '\n\n').replace('---\n', '').replace('\n---', '')

        print(f"[HISTORY-TTS] Episode: {episode_id}")
        print(f"[HISTORY-TTS] Script length: {len(script)}자")
        print(f"[HISTORY-TTS] Voice: {voice or 'default'}")
        print(f"[HISTORY-TTS] Speed: {speed}")

        # 출력 디렉토리
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_path, "outputs", "audio")

        result = generate_tts(
            episode_id=episode_id,
            script=script,
            output_dir=output_dir,
            voice=voice,
            speed=speed
        )

        if result.get("ok"):
            audio_path = result.get("audio_path", "")
            srt_path = result.get("srt_path", "")

            # 상대 경로로 변환
            if audio_path and base_path in audio_path:
                audio_rel = audio_path.replace(base_path + "/", "")
            else:
                audio_rel = audio_path
            if srt_path and base_path in srt_path:
                srt_rel = srt_path.replace(base_path + "/", "")
            else:
                srt_rel = srt_path

            # URL 생성
            audio_url = "/" + audio_rel if audio_rel else ""
            srt_url = "/" + srt_rel if srt_rel else ""

            return jsonify({
                "ok": True,
                "episode_id": episode_id,
                "audio_path": audio_rel,
                "audio_url": audio_url,
                "srt_path": srt_rel,
                "srt_url": srt_url,
                "duration": result.get("duration", 0)
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.get("error", "TTS 생성 실패")
            }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ============================================================
# YouTube Factory - 대본 기반 영상 생성
# ============================================================

from pathlib import Path
import json as json_lib

# 대본 디렉토리
SCRIPTS_DIR = Path(__file__).parent.parent / "video_scripts"


@history_bp.route('/youtube-factory')
def youtube_factory_page():
    """YouTube Factory 페이지"""
    return render_template('youtube_factory.html')


@history_bp.route('/api/youtube-factory/scripts')
def youtube_factory_list_scripts():
    """대본 목록 조회"""
    try:
        scripts = []
        if SCRIPTS_DIR.exists():
            for file in sorted(SCRIPTS_DIR.glob("*.json")):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json_lib.load(f)
                        scripts.append({
                            "id": file.stem,
                            "title": data.get("title", file.stem),
                            "era": data.get("era", ""),
                            "scene_count": len(data.get("scenes", []))
                        })
                except Exception as e:
                    print(f"[YOUTUBE-FACTORY] 대본 로드 실패: {file} - {e}")

        return jsonify({"ok": True, "scripts": scripts})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/youtube-factory/scripts/<script_id>')
def youtube_factory_get_script(script_id: str):
    """대본 상세 조회"""
    try:
        script_path = SCRIPTS_DIR / f"{script_id}.json"
        if not script_path.exists():
            return jsonify({"ok": False, "error": "대본을 찾을 수 없습니다"}), 404

        with open(script_path, 'r', encoding='utf-8') as f:
            data = json_lib.load(f)

        return jsonify(data)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@history_bp.route('/api/youtube-factory/generate', methods=['POST'])
def youtube_factory_generate():
    """대본으로 영상 생성"""
    try:
        data = request.get_json() or {}
        script_id = data.get('script_id')

        if not script_id:
            return jsonify({"ok": False, "error": "script_id가 필요합니다"}), 400

        # 대본 로드
        script_path = SCRIPTS_DIR / f"{script_id}.json"
        if not script_path.exists():
            return jsonify({"ok": False, "error": "대본을 찾을 수 없습니다"}), 404

        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json_lib.load(f)

        print(f"[YOUTUBE-FACTORY] 영상 생성 시작: {script_data.get('title')}")

        # History Pipeline 사용
        from scripts.history_pipeline.pipeline import HistoryPipeline

        pipeline = HistoryPipeline()
        result = pipeline.run_from_script(script_data)

        if result.get("ok"):
            video_path = result.get("video_path", "")
            # URL로 변환
            base_path = str(Path(__file__).parent.parent)
            if video_path.startswith(base_path):
                video_rel = video_path.replace(base_path + "/", "")
            else:
                video_rel = video_path

            return jsonify({
                "ok": True,
                "video_url": "/" + video_rel,
                "video_path": video_rel,
                "title": script_data.get("title")
            })
        else:
            return jsonify({
                "ok": False,
                "error": result.get("error", "영상 생성 실패")
            }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

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
"""

import os
from flask import Blueprint, request, jsonify

# Blueprint 생성
history_bp = Blueprint('history', __name__)

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

    응답:
    - 전체 에피소드 수 (60화)
    - 시대별 에피소드 목록
    - 현재 진행 상황 (시트 연결 시)
    """
    try:
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

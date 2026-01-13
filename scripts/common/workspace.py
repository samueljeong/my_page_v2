"""
Workspace Helper for Claude Code
대시보드에 작업 현황을 실시간으로 표시하기 위한 헬퍼 모듈
"""

import os
import json
from datetime import datetime

WORKSPACE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "outputs/workspace/current_script.json"
)


def _ensure_dir():
    """workspace 디렉토리 생성"""
    os.makedirs(os.path.dirname(WORKSPACE_FILE), exist_ok=True)


def _load():
    """현재 workspace 상태 로드"""
    _ensure_dir()
    if os.path.exists(WORKSPACE_FILE):
        with open(WORKSPACE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save(data):
    """workspace 상태 저장"""
    _ensure_dir()
    with open(WORKSPACE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def start_script(pipeline: str, episode: int, plan: list = None):
    """
    대본 작성 시작

    Args:
        pipeline: "history" | "isekai"
        episode: 에피소드 번호
        plan: 기획 목록 (optional)
    """
    default_plan = [
        {"title": "인트로", "description": "시청자 주목을 끄는 cold open", "target": "1,000-1,500자", "status": "pending"},
        {"title": "배경 설명", "description": "역사적 맥락, 인물 소개", "target": "2,000-2,500자", "status": "pending"},
        {"title": "본론 전반부", "description": "사건 전개, 갈등 고조", "target": "3,500-4,000자", "status": "pending"},
        {"title": "본론 후반부", "description": "클라이맥스, 극적 전환", "target": "4,000-4,500자", "status": "pending"},
        {"title": "마무리", "description": "역사적 의미, 다음 예고", "target": "2,000-2,500자", "status": "pending"},
    ]

    data = {
        "status": "planning",
        "pipeline": pipeline,
        "episode": episode,
        "started_at": datetime.now().isoformat(),
        "current_part": "기획",
        "plan": plan or default_plan,
        "parts": {},
        "total_chars": 0,
        "message": f"Starting {pipeline} EP{episode}..."
    }
    _save(data)
    return data


def update_plan(plan: list):
    """기획 업데이트"""
    data = _load()
    data["plan"] = plan
    data["status"] = "planning"
    _save(data)


def start_part(part_id: str, part_name: str):
    """
    파트 작성 시작

    Args:
        part_id: "intro" | "background" | "body1" | "body2" | "closing"
        part_name: "인트로" | "배경 설명" 등
    """
    data = _load()
    data["status"] = "writing"
    data["current_part"] = part_name

    # plan에서 해당 파트 active로 변경
    part_map = {"intro": 0, "background": 1, "body1": 2, "body2": 3, "closing": 4}
    idx = part_map.get(part_id, -1)
    if idx >= 0 and data.get("plan"):
        for i, p in enumerate(data["plan"]):
            if i < idx:
                p["status"] = "completed"
            elif i == idx:
                p["status"] = "active"
            else:
                p["status"] = "pending"

    data["message"] = f"Writing {part_name}..."
    _save(data)


def update_part(part_id: str, content: str):
    """
    파트 내용 업데이트 (실시간)

    Args:
        part_id: "intro" | "background" | "body1" | "body2" | "closing"
        content: 현재까지 작성된 내용
    """
    data = _load()
    data["parts"][part_id] = content

    # 총 글자수 계산
    total = sum(len(c) for c in data["parts"].values())
    data["total_chars"] = total

    _save(data)


def complete_part(part_id: str, content: str):
    """파트 작성 완료"""
    data = _load()
    data["parts"][part_id] = content

    # plan에서 해당 파트 completed로 변경
    part_map = {"intro": 0, "background": 1, "body1": 2, "body2": 3, "closing": 4}
    idx = part_map.get(part_id, -1)
    if idx >= 0 and data.get("plan"):
        data["plan"][idx]["status"] = "completed"

    # 총 글자수 계산
    total = sum(len(c) for c in data["parts"].values())
    data["total_chars"] = total

    data["message"] = f"{part_id} completed ({len(content):,}자)"
    _save(data)


def complete_script():
    """대본 작성 완료"""
    data = _load()
    data["status"] = "completed"
    data["current_part"] = "완료"

    # 모든 plan completed로
    if data.get("plan"):
        for p in data["plan"]:
            p["status"] = "completed"

    total = sum(len(c) for c in data.get("parts", {}).values())
    data["total_chars"] = total
    data["message"] = f"Script completed! Total: {total:,}자"
    _save(data)


def set_error(message: str):
    """에러 상태 설정"""
    data = _load()
    data["status"] = "error"
    data["message"] = message
    _save(data)


def reset():
    """workspace 초기화"""
    data = {
        "status": "idle",
        "pipeline": None,
        "episode": None,
        "started_at": None,
        "current_part": None,
        "plan": [],
        "parts": {},
        "total_chars": 0,
        "message": "Waiting for Claude Code to start..."
    }
    _save(data)


# 편의 함수: 전체 대본 가져오기
def get_full_script() -> str:
    """작성된 전체 대본 반환"""
    data = _load()
    parts_order = ["intro", "background", "body1", "body2", "closing"]
    parts = data.get("parts", {})
    return "\n\n".join(parts.get(p, "") for p in parts_order if parts.get(p))

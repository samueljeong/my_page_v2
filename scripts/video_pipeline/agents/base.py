"""
영상 생성 파이프라인 - Base Agent

모든 에이전트의 기본 클래스와 영상 생성 전용 컨텍스트 정의
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import uuid

# 공통 클래스 import
from scripts.common import AgentStatus, AgentResult, BaseAgent, BudgetManager

# 하위 호환성을 위한 re-export
__all__ = ["AgentStatus", "AgentResult", "BaseAgent", "BudgetManager", "VideoTaskContext"]


@dataclass
class VideoTaskContext:
    """
    영상 생성 작업 컨텍스트 - 에이전트 간 공유 데이터

    Google Sheets 행 데이터를 기반으로 전체 파이프라인에서 사용됩니다.
    """
    # 기본 식별자
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    row_number: int = 0
    sheet_name: str = ""

    # 입력 데이터 (Google Sheets에서)
    script: str = ""  # 원본 대본
    title_input: str = ""  # 사용자 입력 제목
    thumbnail_text_input: str = ""  # 사용자 입력 썸네일 문구
    channel_id: str = ""
    privacy_status: str = "private"
    publish_at: Optional[str] = None
    playlist_id: Optional[str] = None
    voice: str = "chirp3:Charon"  # 기본: Chirp 3 HD 남성 음성
    project_suffix: str = ""  # YouTube 프로젝트 ('', '_2')
    input_category: str = ""  # 시트에서 입력된 카테고리 (news 등)
    citation_links: str = ""  # ★ 인용링크 (유튜브 설명에 포함)

    # 분석 결과
    analysis_result: Optional[Dict[str, Any]] = None
    scenes: Optional[List[Dict[str, Any]]] = None
    youtube_metadata: Optional[Dict[str, Any]] = None
    thumbnail_config: Optional[Dict[str, Any]] = None
    video_effects: Optional[Dict[str, Any]] = None
    detected_category: str = ""

    # 생성된 에셋
    tts_result: Optional[Dict[str, Any]] = None
    subtitles: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[str]] = None
    thumbnail_path: Optional[str] = None
    video_path: Optional[str] = None

    # 품질 검증 결과
    quality_scores: Dict[str, float] = field(default_factory=dict)
    quality_feedback: Dict[str, str] = field(default_factory=dict)

    # 최종 결과
    video_url: Optional[str] = None
    shorts_url: Optional[str] = None

    # 시도 횟수
    analysis_attempts: int = 0
    tts_attempts: int = 0
    image_attempts: int = 0
    video_attempts: int = 0
    upload_attempts: int = 0

    # 설정
    max_attempts: int = 3

    # 비용 추적
    total_cost: float = 0.0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)

    # 로그
    logs: List[Dict[str, Any]] = field(default_factory=list)

    # 전략 (슈퍼바이저가 결정)
    strategy: Optional[Dict[str, Any]] = None

    def add_log(self, agent: str, action: str, result: str, details: str = ""):
        """로그 추가"""
        self.logs.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent,
            "action": action,
            "result": result,
            "details": details,
        })

    def add_cost(self, agent: str, amount: float):
        """비용 추가"""
        self.total_cost += amount
        self.cost_breakdown[agent] = self.cost_breakdown.get(agent, 0) + amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "row_number": self.row_number,
            "sheet_name": self.sheet_name,
            "script_length": len(self.script) if self.script else 0,
            "scenes_count": len(self.scenes) if self.scenes else 0,
            "images_count": len(self.images) if self.images else 0,
            "video_url": self.video_url,
            "shorts_url": self.shorts_url,
            "total_cost": self.total_cost,
            "cost_breakdown": self.cost_breakdown,
            "quality_scores": self.quality_scores,
            "logs": self.logs,
        }

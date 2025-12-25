"""
ImageAgent - 이미지 생성 에이전트

역할:
- 씬별 이미지 생성 (썸네일 제외)
- 검수 피드백 반영하여 재생성
"""

import os
import time
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentResult, AgentStatus, TaskContext

# 기존 run.py의 이미지 생성 함수 사용
from ..run import generate_images_parallel, generate_single_image


class ImageAgent(BaseAgent):
    """이미지 생성 에이전트"""

    def __init__(self):
        super().__init__("ImageAgent")
        self.max_workers = 4  # 병렬 워커 수
        self.output_base_dir = "/tmp/shorts_agents"

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """
        이미지 생성 실행

        Args:
            context: 작업 컨텍스트 (script 필수)
            **kwargs:
                feedback: 검수 에이전트의 피드백 (개선 시)
                failed_scenes: 재생성할 씬 번호 리스트

        Returns:
            AgentResult with image paths
        """
        self.set_status(AgentStatus.RUNNING)
        start_time = time.time()

        feedback = kwargs.get("feedback")
        failed_scenes = kwargs.get("failed_scenes", [])

        # 대본이 없으면 실패
        if not context.script:
            self.set_status(AgentStatus.FAILED)
            return AgentResult(
                success=False,
                error="대본이 없습니다. ScriptAgent를 먼저 실행하세요.",
            )

        try:
            if feedback and failed_scenes:
                # 특정 씬만 재생성
                result = await self._regenerate_scenes(context, failed_scenes, feedback)
            else:
                # 전체 이미지 생성
                result = await self._generate_all_images(context)

            duration = time.time() - start_time

            if result.get("ok") or len(result.get("images", [])) >= 4:  # 80% 이상 성공
                self.set_status(AgentStatus.SUCCESS)
                context.images = [img["path"] for img in result.get("images", [])]
                context.image_attempts += 1
                context.add_log(
                    self.name,
                    "regenerate" if failed_scenes else "generate",
                    "success",
                    f"{len(result.get('images', []))}개 이미지, ${result.get('cost', 0):.3f}"
                )

                return AgentResult(
                    success=True,
                    data=result,
                    cost=result.get("cost", 0),
                    duration=duration,
                )
            else:
                self.set_status(AgentStatus.FAILED)
                failed_info = result.get("failed", [])
                error_msg = f"이미지 생성 실패: {len(failed_info)}개 씬 실패"
                context.add_log(self.name, "generate", "failed", error_msg)

                return AgentResult(
                    success=False,
                    error=error_msg,
                    data=result,
                    duration=duration,
                )

        except Exception as e:
            self.set_status(AgentStatus.FAILED)
            context.add_log(self.name, "execute", "exception", str(e))
            return AgentResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time,
            )

    async def _generate_all_images(self, context: TaskContext) -> Dict[str, Any]:
        """전체 씬 이미지 생성"""
        self.log(f"이미지 생성 시작: {context.task_id}")

        scenes = context.script.get("scenes", [])
        if not scenes:
            return {"ok": False, "error": "씬 정보가 없습니다", "images": [], "failed": []}

        output_dir = os.path.join(self.output_base_dir, context.task_id, "images")
        os.makedirs(output_dir, exist_ok=True)

        result = generate_images_parallel(
            scenes=scenes,
            output_dir=output_dir,
            max_workers=self.max_workers
        )

        return result

    async def _regenerate_scenes(
        self,
        context: TaskContext,
        failed_scenes: List[int],
        feedback: str
    ) -> Dict[str, Any]:
        """특정 씬 이미지 재생성"""
        self.log(f"이미지 재생성: 씬 {failed_scenes}")
        self.log(f"피드백: {feedback[:100]}...")

        scenes = context.script.get("scenes", [])
        output_dir = os.path.join(self.output_base_dir, context.task_id, "images")

        # 재생성할 씬만 필터링
        scenes_to_regenerate = [
            scene for scene in scenes
            if scene.get("scene_number") in failed_scenes
        ]

        if not scenes_to_regenerate:
            return {"ok": True, "images": [], "failed": [], "cost": 0}

        # 피드백을 반영한 프롬프트 개선 (선택적)
        for scene in scenes_to_regenerate:
            original_prompt = scene.get("image_prompt_enhanced", scene.get("image_prompt", ""))
            # 피드백 내용을 프롬프트에 추가
            scene["image_prompt_enhanced"] = f"""
{original_prompt}

IMPROVEMENT NOTES based on review feedback:
{feedback}

Please address the feedback while maintaining the overall style.
"""

        result = generate_images_parallel(
            scenes=scenes_to_regenerate,
            output_dir=output_dir,
            max_workers=self.max_workers
        )

        # 기존 이미지 목록과 병합
        if context.images:
            existing_images = []
            for i, path in enumerate(context.images):
                scene_num = i + 1
                if scene_num not in failed_scenes:
                    existing_images.append({"scene": scene_num, "path": path})

            result["images"] = sorted(
                existing_images + result.get("images", []),
                key=lambda x: x["scene"]
            )

        return result

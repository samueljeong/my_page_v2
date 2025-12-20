"""
sermon_modules/prompt.py
프롬프트 빌더 함수들

스타일별 분기 지원:
- three_points (3대지): 전통적인 3포인트 설교
- topical (주제설교): 주제 중심 설교
- expository (강해설교): 본문 해설 중심 설교
"""

import json
from .utils import is_json_guide, parse_json_guide
from .styles import get_style, get_available_styles, READABILITY_GUIDE


def get_system_prompt_for_step(step_name):
    """단계별 기본 system prompt 반환"""
    if '제목' in step_name:
        return """당신은 설교 '제목 후보'만 제안하는 역할입니다.

CRITICAL RULES:
1. 반드시 한국어로만 응답하세요
2. 정확히 3개의 제목만 제시하세요
3. 각 제목은 한 줄로 작성하세요
4. 번호, 기호, 마크다운 사용 금지
5. 제목만 작성하고 설명 추가 금지

출력 형식 예시:
하나님의 약속을 믿는 믿음
약속의 땅을 향한 여정
아브라함의 신앙 결단"""
    else:
        return f"""당신은 설교 '초안 자료'만 준비하는 역할입니다.

현재 단계: {step_name}

기본 역할:
- 반드시 한국어로만 응답하세요
- 완성된 설교 문단이 아닌, 자료와 구조만 제공
- 사용자가 제공하는 세부 지침을 최우선으로 따름
- 지침이 없는 경우에만 일반적인 설교 자료 형식 사용

⚠️ 중요: 사용자의 세부 지침이 제공되면 그것을 절대적으로 우선하여 따라야 합니다."""


# ═══════════════════════════════════════════════════════════════
# 스타일별 프롬프트 함수들
# ═══════════════════════════════════════════════════════════════

def get_step2_prompt_for_style(style_id: str, step1_result: dict = None, context_data: dict = None) -> str:
    """
    스타일별 Step2 구조 설계 프롬프트 반환

    Args:
        style_id: 스타일 ID (three_points, topical, expository)
        step1_result: Step1 분석 결과
        context_data: 시대 컨텍스트 데이터

    Returns:
        스타일에 맞는 Step2 구조 설계 프롬프트
    """
    style = get_style(style_id)
    return style.build_step2_prompt(step1_result=step1_result, context_data=context_data)


def get_step3_prompt_for_style(style_id: str, step2_result: dict = None, duration: str = "20분") -> str:
    """
    스타일별 Step3/Step4 설교문 작성 프롬프트 반환

    Args:
        style_id: 스타일 ID (three_points, topical, expository)
        step2_result: Step2 구조 설계 결과
        duration: 설교 분량

    Returns:
        스타일에 맞는 Step3 작성 프롬프트 (가독성 가이드 포함)
    """
    style = get_style(style_id)
    return style.build_step3_prompt(step2_result=step2_result, duration=duration)


def get_style_structure_template(style_id: str) -> dict:
    """
    스타일별 구조 템플릿 반환 (Step2 출력용)

    Args:
        style_id: 스타일 ID

    Returns:
        해당 스타일의 JSON 구조 템플릿
    """
    style = get_style(style_id)
    return style.get_structure_template()


def get_style_checklist(style_id: str) -> list:
    """
    스타일별 체크리스트 반환 (Step3용)

    Args:
        style_id: 스타일 ID

    Returns:
        해당 스타일의 체크리스트 항목 리스트
    """
    style = get_style(style_id)
    return style.get_step3_checklist()


def get_style_illustration_guide(style_id: str) -> str:
    """
    스타일별 예화 배치 가이드 반환

    Args:
        style_id: 스타일 ID

    Returns:
        해당 스타일의 예화 배치 가이드
    """
    style = get_style(style_id)
    return style.get_illustration_guide()


def build_prompt_from_json(json_guide, step_type="step1"):
    """JSON 지침을 기반으로 시스템 프롬프트 생성"""
    role = json_guide.get("role", "설교 자료 작성자")
    principle = json_guide.get("principle", "")
    output_format = json_guide.get("output_format", {})

    prompt = f"""당신은 '{role}'입니다.

【 핵심 원칙 】
{principle}

【 출력 형식 】
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 순수 JSON만 출력하세요.

```json
{{
"""

    fields = []
    for key, value in output_format.items():
        label = value.get("label", key) if isinstance(value, dict) else key
        description = value.get("description", "") if isinstance(value, dict) else ""
        fields.append(f'  "{key}": "/* {label}: {description} */"')

    prompt += ",\n".join(fields)
    prompt += "\n}\n```\n"

    prompt += "\n【 각 필드 상세 지침 】\n"
    for key, value in output_format.items():
        if isinstance(value, dict):
            label = value.get("label", key)
            description = value.get("description", "")
            purpose = value.get("purpose", "")
            items = value.get("items", [])

            prompt += f"\n▶ {key} ({label})\n"
            if description:
                prompt += f"  - 설명: {description}\n"
            if purpose:
                prompt += f"  - 목적: {purpose}\n"
            if items:
                prompt += f"  - 포함 항목: {', '.join(items)}\n"

            for sub_key in ["per_verse", "per_term", "sub_items", "format"]:
                if sub_key in value:
                    sub_value = value[sub_key]
                    if isinstance(sub_value, dict):
                        prompt += f"  - {sub_key}:\n"
                        for sk, sv in sub_value.items():
                            if isinstance(sv, dict):
                                prompt += f"    • {sk}: {sv.get('description', sv)}\n"
                            else:
                                prompt += f"    • {sk}: {sv}\n"
                    elif isinstance(sub_value, list):
                        prompt += f"  - {sub_key}: {', '.join(str(x) for x in sub_value)}\n"

    prompt += "\n⚠️ 중요: 반드시 위 JSON 형식으로만 응답하세요."
    return prompt


def build_step3_prompt_from_json(json_guide, meta_data, step1_result, step2_result, style_id: str = None):
    """
    Step3용 프롬프트 생성 - Step1/2 데이터를 충실히 전달

    Args:
        json_guide: JSON 지침
        meta_data: 메타 정보 (duration, worship_type, target, sermon_style 등)
        step1_result: Step1 분석 결과
        step2_result: Step2 구조 설계 결과
        style_id: 설교 스타일 ID (없으면 meta_data에서 추출)

    Returns:
        Step3용 완성된 프롬프트
    """
    duration = meta_data.get("duration", "")
    worship_type = meta_data.get("worship_type", "")
    special_notes = meta_data.get("special_notes", "")
    target = meta_data.get("target", "")

    # 스타일 ID 결정 (파라미터 > meta_data > 기본값)
    if not style_id:
        style_id = meta_data.get("sermon_style", "three_points")

    prompt = ""

    # ========================================
    # 1순위: Step1 핵심 분석 (설교의 기초)
    # ========================================
    prompt += "=" * 60 + "\n"
    prompt += "【 ★★★ 1순위: Step1 본문 분석 (설교의 기초) ★★★ 】\n"
    prompt += "=" * 60 + "\n\n"

    if step1_result and isinstance(step1_result, dict):
        # 핵심 메시지 (가장 중요)
        core_message = step1_result.get("핵심_메시지")
        if core_message:
            prompt += "▶ 핵심 메시지 (이 설교의 중심 진리)\n"
            if isinstance(core_message, str):
                prompt += f"   {core_message}\n\n"
            else:
                prompt += json.dumps(core_message, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 본문 개요
        overview = step1_result.get("본문_개요")
        if overview:
            prompt += "▶ 본문 개요\n"
            if isinstance(overview, str):
                prompt += f"   {overview}\n\n"
            else:
                prompt += json.dumps(overview, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 구조 분석
        structure = step1_result.get("구조_분석")
        if structure:
            prompt += "▶ 본문 구조 분석\n"
            if isinstance(structure, str):
                prompt += f"   {structure}\n\n"
            else:
                prompt += json.dumps(structure, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 핵심 단어 분석 (실제 Step1 출력 키)
        key_terms = step1_result.get("핵심_단어_분석") or step1_result.get("key_terms")
        if key_terms:
            prompt += "▶ 핵심 단어/원어 분석\n"
            if isinstance(key_terms, str):
                prompt += f"   {key_terms}\n\n"
            else:
                prompt += json.dumps(key_terms, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 주요 절 해설
        verse_notes = step1_result.get("주요_절_해설")
        if verse_notes:
            prompt += "▶ 주요 절 해설 (설교에서 반드시 다뤄야 할 구절)\n"
            if isinstance(verse_notes, str):
                prompt += f"   {verse_notes}\n\n"
            else:
                prompt += json.dumps(verse_notes, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 대지 후보
        point_candidates = step1_result.get("대지_후보")
        if point_candidates:
            prompt += "▶ 대지 후보 (Step2에서 선택된 포인트들의 원천)\n"
            if isinstance(point_candidates, str):
                prompt += f"   {point_candidates}\n\n"
            else:
                prompt += json.dumps(point_candidates, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 신학적 주제
        theological = step1_result.get("신학적_주제")
        if theological:
            prompt += "▶ 신학적 주제\n"
            if isinstance(theological, str):
                prompt += f"   {theological}\n\n"
            else:
                prompt += json.dumps(theological, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 보충 성경구절 (cross_references 호환)
        cross_refs = step1_result.get("보충_성경구절") or step1_result.get("cross_references")
        if cross_refs:
            prompt += "▶ 보충 성경구절\n"
            if isinstance(cross_refs, str):
                prompt += f"   {cross_refs}\n\n"
            else:
                prompt += json.dumps(cross_refs, ensure_ascii=False, indent=2)
                prompt += "\n\n"
    else:
        prompt += "⚠️ Step1 분석 결과가 없습니다. 본문을 직접 분석하여 작성하세요.\n\n"

    # ========================================
    # 2순위: Step2 설교 구조 (뼈대)
    # ========================================
    prompt += "=" * 60 + "\n"
    prompt += "【 ★★★ 2순위: Step2 설교 구조 (반드시 따를 것) ★★★ 】\n"
    prompt += "=" * 60 + "\n\n"

    if step2_result and isinstance(step2_result, dict):
        # 설교 제목
        sermon_title = step2_result.get("설교_제목")
        if sermon_title:
            prompt += "▶ 설교 제목\n"
            if isinstance(sermon_title, str):
                prompt += f"   {sermon_title}\n\n"
            else:
                prompt += json.dumps(sermon_title, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 대지 연결 흐름
        flow = step2_result.get("대지_연결_흐름")
        if flow:
            prompt += "▶ 대지 연결 흐름 (1→2→3대지 논리적 연결)\n"
            if isinstance(flow, str):
                prompt += f"   {flow}\n\n"
            else:
                prompt += json.dumps(flow, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 서론 방향
        intro = step2_result.get("서론_방향")
        if intro:
            prompt += "▶ 서론 방향\n"
            if isinstance(intro, str):
                prompt += f"   {intro}\n\n"
            else:
                prompt += json.dumps(intro, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 대지 1, 2, 3
        for i in range(1, 4):
            point = step2_result.get(f"대지_{i}")
            if point:
                prompt += f"▶ 대지 {i}\n"
                if isinstance(point, str):
                    prompt += f"   {point}\n\n"
                elif isinstance(point, dict):
                    for key, value in point.items():
                        prompt += f"   • {key}: {value}\n"
                    prompt += "\n"
                else:
                    prompt += json.dumps(point, ensure_ascii=False, indent=2)
                    prompt += "\n\n"

        # 결론 방향
        conclusion = step2_result.get("결론_방향")
        if conclusion:
            prompt += "▶ 결론 방향\n"
            if isinstance(conclusion, str):
                prompt += f"   {conclusion}\n\n"
            else:
                prompt += json.dumps(conclusion, ensure_ascii=False, indent=2)
                prompt += "\n\n"

        # 기존 호환: writing_spec, sermon_outline, detailed_points
        writing_spec = step2_result.get("writing_spec", {})
        if writing_spec:
            prompt += "▶ 작성 규격\n"
            for key, value in writing_spec.items():
                prompt += f"  - {key}: {value}\n"
            prompt += "\n"

        sermon_outline = step2_result.get("sermon_outline")
        if sermon_outline:
            prompt += "▶ 설교 구조 (outline)\n"
            prompt += json.dumps(sermon_outline, ensure_ascii=False, indent=2)
            prompt += "\n\n"

        detailed_points = step2_result.get("detailed_points")
        if detailed_points:
            prompt += "▶ 상세 구조\n"
            prompt += json.dumps(detailed_points, ensure_ascii=False, indent=2)
            prompt += "\n\n"
    else:
        prompt += "⚠️ Step2 구조 결과가 없습니다. 3대지 구조를 직접 설계하여 작성하세요.\n\n"

    # ========================================
    # 3순위: 설정 정보 (분량, 대상, 예배유형)
    # ========================================
    prompt += "=" * 60 + "\n"
    prompt += "【 3순위: 설정 정보 】\n"
    prompt += "=" * 60 + "\n"

    # 기본 정보
    key_labels = {
        "scripture": "성경 본문", "title": "설교 제목", "target": "대상",
        "worship_type": "예배·집회 유형", "duration": "분량",
        "sermon_style": "설교 스타일", "category": "카테고리"
    }
    prompt += "\n▶ 기본 정보\n"
    for key, value in meta_data.items():
        if value and key != "special_notes":
            label = key_labels.get(key, key)
            prompt += f"  - {label}: {value}\n"
    prompt += "\n"

    if special_notes:
        prompt += f"▶ 특별 참고 사항\n   {special_notes}\n\n"

    # ========================================
    # 스타일별 작성 지침 (있는 경우)
    # ========================================
    if json_guide and isinstance(json_guide, dict):
        prompt += "=" * 60 + "\n"
        prompt += "【 스타일별 작성 지침 】\n"
        prompt += "=" * 60 + "\n\n"

        priority_order = json_guide.get("priority_order", {})
        if priority_order:
            prompt += "▶ 우선순위\n"
            for key, value in priority_order.items():
                prompt += f"  {key}: {value}\n"
            prompt += "\n"

        use_from_step1 = json_guide.get("use_from_step1", {})
        if use_from_step1:
            prompt += "▶ Step1 자료 활용법\n"
            for field, config in use_from_step1.items():
                if isinstance(config, dict):
                    instruction = config.get("instruction", "")
                    prompt += f"  • {field}: {instruction}\n"
                else:
                    prompt += f"  • {field}: {config}\n"
            prompt += "\n"

        use_from_step2 = json_guide.get("use_from_step2", {})
        if use_from_step2:
            prompt += "▶ Step2 구조 활용법\n"
            for field, config in use_from_step2.items():
                if isinstance(config, dict):
                    instruction = config.get("instruction", "")
                    prompt += f"  • {field}: {instruction}\n"
                else:
                    prompt += f"  • {field}: {config}\n"
            prompt += "\n"

        writing_rules = json_guide.get("writing_rules", {})
        if writing_rules:
            prompt += "▶ 작성 규칙\n"
            for rule_name, rule_config in writing_rules.items():
                if isinstance(rule_config, dict):
                    label = rule_config.get("label", rule_name)
                    rules = rule_config.get("rules", [])
                    prompt += f"  [{label}]\n"
                    for rule in rules:
                        prompt += f"    - {rule}\n"
            prompt += "\n"

    # ========================================
    # 스타일별 작성 가이드 (신규)
    # ========================================
    prompt += "=" * 60 + "\n"
    prompt += f"【 ★★★ 설교 스타일별 작성 가이드 ({style_id}) ★★★ 】\n"
    prompt += "=" * 60 + "\n\n"

    # 스타일별 작성 가이드 추가
    style_writing_guide = get_step3_prompt_for_style(style_id, step2_result, duration or "20분")
    prompt += style_writing_guide
    prompt += "\n\n"

    # 스타일별 예화 가이드 추가
    style_illustration_guide = get_style_illustration_guide(style_id)
    prompt += style_illustration_guide
    prompt += "\n\n"

    # ========================================
    # 최종 체크리스트 (스타일별 + 공통)
    # ========================================
    prompt += "=" * 60 + "\n"
    prompt += "【 ★★★ 최종 체크리스트 ★★★ 】\n"
    prompt += "=" * 60 + "\n\n"

    # 스타일별 체크리스트
    prompt += "▶ 스타일별 필수 체크:\n"
    style_checklist = get_style_checklist(style_id)
    for item in style_checklist:
        prompt += f"  □ {item}\n"
    prompt += "\n"

    # 공통 체크리스트
    prompt += "▶ 공통 필수 체크:\n"
    prompt += "  □ Step1의 '핵심_메시지'가 설교 전체에 일관되게 흐르는가?\n"
    prompt += "  □ Step1의 '주요_절_해설'과 '핵심_단어_분석'을 적절히 활용했는가?\n"
    if duration:
        prompt += f"  □ 분량이 {duration}에 맞는가?\n"
    if target:
        prompt += f"  □ 대상({target})에 맞는 어조와 예시를 사용했는가?\n"
    if worship_type:
        prompt += f"  □ 예배 유형({worship_type})에 맞는 톤인가?\n"
    prompt += "  □ 마크다운 없이 순수 텍스트로 작성했는가?\n"
    prompt += "  □ 복음과 소망, 하나님의 은혜가 분명하게 드러나는가?\n"
    prompt += "  □ 성경 구절이 가독성 가이드에 맞게 줄바꿈 처리되었는가?\n"

    prompt += "\n⚠️ 중요: Step1과 Step2의 분석 결과를 충실히 반영하여, "
    prompt += "일관성 있고 깊이 있는 설교문을 작성하세요.\n"
    prompt += "⚠️ 특히 가독성 가이드를 반드시 따르세요 (성경 구절 줄바꿈, 짧은 문장).\n"

    return prompt

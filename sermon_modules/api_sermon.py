"""
api_sermon.py
설교 처리 관련 API Blueprint

포함될 라우트:
- POST /api/sermon/process      - Step 처리 (Step1, Step2)
- POST /api/sermon/meditation   - 묵상메시지 생성
- POST /api/sermon/gpt-pro      - GPT PRO (Step3)
- POST /api/sermon/qa           - Q&A 질의응답
- POST /api/sermon/recommend-scripture - 본문 추천
- POST /api/sermon/chat         - 설교 챗봇

사용법:
    from sermon_modules.api_sermon import api_sermon_bp
    app.register_blueprint(api_sermon_bp)
"""

from flask import Blueprint, request, jsonify

api_sermon_bp = Blueprint('api_sermon', __name__, url_prefix='/api/sermon')

# TODO: 아래 라우트들을 sermon_server.py에서 마이그레이션
# 현재는 라우트 정의만 준비되어 있습니다.

# @api_sermon_bp.route('/process', methods=['POST'])
# def process_step():
#     """Step1, Step2 처리"""
#     pass

# @api_sermon_bp.route('/meditation', methods=['POST'])
# def create_meditation():
#     """묵상메시지 생성"""
#     pass

# @api_sermon_bp.route('/gpt-pro', methods=['POST'])
# def gpt_pro():
#     """GPT PRO (Step3) 설교문 완성"""
#     pass

# @api_sermon_bp.route('/qa', methods=['POST'])
# def sermon_qa():
#     """Q&A 질의응답"""
#     pass

# @api_sermon_bp.route('/recommend-scripture', methods=['POST'])
# def recommend_scripture():
#     """본문 추천"""
#     pass

# @api_sermon_bp.route('/chat', methods=['POST'])
# def sermon_chat():
#     """설교 챗봇"""
#     pass

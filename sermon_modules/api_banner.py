"""
api_banner.py
배너/현수막 관련 API Blueprint

포함될 라우트:
- GET  /api/banner/templates           - 템플릿 목록
- POST /api/banner/generate            - 배너 생성
- GET  /api/banner/fonts               - 폰트 목록
- POST /api/banner/generate-with-text  - 텍스트 포함 배너 생성
- POST /api/banner/generate-prompt     - 프롬프트 기반 생성
- GET  /api/banner/references          - 참조 이미지 목록
- POST /api/banner/references          - 참조 이미지 추가
- DELETE /api/banner/references/<id>   - 참조 이미지 삭제
- POST /api/banner/references/<id>/rate - 이미지 평가
- POST /api/banner/crawl               - 이미지 크롤링
- POST /api/banner/references/bulk     - 대량 이미지 추가

사용법:
    from sermon_modules.api_banner import api_banner_bp
    app.register_blueprint(api_banner_bp)
"""

from flask import Blueprint, request, jsonify

api_banner_bp = Blueprint('api_banner', __name__, url_prefix='/api/banner')

# TODO: 아래 라우트들을 sermon_server.py에서 마이그레이션
# 현재는 라우트 정의만 준비되어 있습니다.

# @api_banner_bp.route('/templates', methods=['GET'])
# def get_templates():
#     """배너 템플릿 목록"""
#     pass

# @api_banner_bp.route('/generate', methods=['POST'])
# def generate_banner():
#     """배너 생성"""
#     pass

# @api_banner_bp.route('/fonts', methods=['GET'])
# def get_fonts():
#     """폰트 목록"""
#     pass

# @api_banner_bp.route('/generate-with-text', methods=['POST'])
# def generate_with_text():
#     """텍스트 포함 배너 생성"""
#     pass

# @api_banner_bp.route('/generate-prompt', methods=['POST'])
# def generate_prompt():
#     """프롬프트 기반 생성"""
#     pass

# @api_banner_bp.route('/references', methods=['GET'])
# def get_references():
#     """참조 이미지 목록"""
#     pass

# @api_banner_bp.route('/references', methods=['POST'])
# def add_reference():
#     """참조 이미지 추가"""
#     pass

# @api_banner_bp.route('/references/<int:ref_id>', methods=['DELETE'])
# def delete_reference(ref_id):
#     """참조 이미지 삭제"""
#     pass

# @api_banner_bp.route('/references/<int:ref_id>/rate', methods=['POST'])
# def rate_reference(ref_id):
#     """이미지 평가"""
#     pass

# @api_banner_bp.route('/crawl', methods=['POST'])
# def crawl_images():
#     """이미지 크롤링"""
#     pass

# @api_banner_bp.route('/references/bulk', methods=['POST'])
# def bulk_add_references():
#     """대량 이미지 추가"""
#     pass

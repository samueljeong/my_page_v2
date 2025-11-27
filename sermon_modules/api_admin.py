"""
api_admin.py
관리자 관련 API Blueprint

포함될 라우트:
- GET  /admin                          - 관리자 대시보드
- POST /admin/toggle-admin/<id>        - 관리자 권한 토글
- POST /admin/delete-user/<id>         - 사용자 삭제
- POST /admin/set-credits/<id>         - 크레딧 설정
- POST /admin/add-credits/<id>         - 크레딧 추가
- GET/POST /admin/settings             - 설정 관리
- GET  /admin/benchmark-data           - 벤치마크 데이터
- GET  /api/admin/usage-stats          - 사용량 통계

사용법:
    from sermon_modules.api_admin import api_admin_bp
    app.register_blueprint(api_admin_bp)
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session

api_admin_bp = Blueprint('api_admin', __name__)

# TODO: 아래 라우트들을 sermon_server.py에서 마이그레이션
# 현재는 라우트 정의만 준비되어 있습니다.

# @api_admin_bp.route('/admin')
# @admin_required
# def admin_dashboard():
#     """관리자 대시보드"""
#     pass

# @api_admin_bp.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
# @admin_required
# def toggle_admin(user_id):
#     """관리자 권한 토글"""
#     pass

# @api_admin_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
# @admin_required
# def delete_user(user_id):
#     """사용자 삭제"""
#     pass

# @api_admin_bp.route('/admin/set-credits/<int:user_id>', methods=['POST'])
# @admin_required
# def set_user_credits(user_id):
#     """크레딧 설정"""
#     pass

# @api_admin_bp.route('/admin/add-credits/<int:user_id>', methods=['POST'])
# @admin_required
# def add_user_credits(user_id):
#     """크레딧 추가"""
#     pass

# @api_admin_bp.route('/admin/settings', methods=['GET', 'POST'])
# @admin_required
# def admin_settings():
#     """설정 관리"""
#     pass

# @api_admin_bp.route('/admin/benchmark-data')
# @admin_required
# def benchmark_data():
#     """벤치마크 데이터"""
#     pass

# @api_admin_bp.route('/api/admin/usage-stats')
# @admin_required
# def usage_stats():
#     """사용량 통계"""
#     pass

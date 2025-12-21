"""
교회 교적 관리 시스템 (Church Registry)
"""
import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

# Flask 앱 초기화
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///church.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 초기화
db = SQLAlchemy(app)

# 로그인 매니저 초기화
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# =============================================================================
# 모델 임포트 (나중에 models/ 폴더로 분리)
# =============================================================================

class Member(db.Model):
    """교인 모델"""
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 이름
    phone = db.Column(db.String(20))  # 전화번호
    email = db.Column(db.String(120))  # 이메일
    address = db.Column(db.String(200))  # 주소
    birth_date = db.Column(db.Date)  # 생년월일
    gender = db.Column(db.String(10))  # 성별

    # 교회 관련 정보
    baptism_date = db.Column(db.Date)  # 세례일
    registration_date = db.Column(db.Date)  # 등록일
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))  # 셀/구역/목장

    # 가족 관계
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'))
    family_role = db.Column(db.String(20))  # 가장, 배우자, 자녀 등

    # 상태
    status = db.Column(db.String(20), default='active')  # active, inactive, newcomer
    notes = db.Column(db.Text)  # 메모

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<Member {self.name}>'


class Family(db.Model):
    """가족 모델"""
    __tablename__ = 'families'

    id = db.Column(db.Integer, primary_key=True)
    family_name = db.Column(db.String(100))  # 가족명 (예: 홍길동 가정)
    members = db.relationship('Member', backref='family', lazy=True)

    created_at = db.Column(db.DateTime, default=db.func.now())


class Group(db.Model):
    """셀/구역/목장 그룹 모델"""
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 그룹명
    group_type = db.Column(db.String(50))  # cell, district, mokjang 등
    leader_id = db.Column(db.Integer)  # 리더 교인 ID

    members = db.relationship('Member', backref='group', lazy=True)

    created_at = db.Column(db.DateTime, default=db.func.now())


class Attendance(db.Model):
    """출석 기록 모델"""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # 출석 날짜
    service_type = db.Column(db.String(50))  # 주일예배, 수요예배, 금요기도회 등
    attended = db.Column(db.Boolean, default=True)

    member = db.relationship('Member', backref='attendance_records')

    created_at = db.Column(db.DateTime, default=db.func.now())


class Visit(db.Model):
    """심방 기록 모델"""
    __tablename__ = 'visits'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    visitor_name = db.Column(db.String(100))  # 심방자
    purpose = db.Column(db.String(100))  # 심방 목적
    notes = db.Column(db.Text)  # 심방 내용

    member = db.relationship('Member', backref='visit_records')

    created_at = db.Column(db.DateTime, default=db.func.now())


class Offering(db.Model):
    """헌금 기록 모델"""
    __tablename__ = 'offerings'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # 금액 (원)
    offering_type = db.Column(db.String(50))  # 십일조, 감사헌금, 건축헌금 등
    notes = db.Column(db.Text)

    member = db.relationship('Member', backref='offering_records')

    created_at = db.Column(db.DateTime, default=db.func.now())


# =============================================================================
# 라우트
# =============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/members')
def member_list():
    """교인 목록"""
    # 검색 파라미터
    query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    group_filter = request.args.get('group', '')

    # 기본 쿼리
    members_query = Member.query

    # 이름 검색
    if query:
        members_query = members_query.filter(Member.name.contains(query))

    # 상태 필터
    if status_filter:
        members_query = members_query.filter(Member.status == status_filter)

    # 그룹 필터
    if group_filter:
        members_query = members_query.filter(Member.group_id == int(group_filter))

    members = members_query.order_by(Member.name).all()
    groups = Group.query.all()

    return render_template('members/list.html',
                         members=members,
                         groups=groups,
                         query=query,
                         status_filter=status_filter,
                         group_filter=group_filter)


@app.route('/members/new', methods=['GET', 'POST'])
def member_new():
    """교인 등록"""
    if request.method == 'POST':
        # 폼 데이터 수집
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        gender = request.form.get('gender', '')
        status = request.form.get('status', 'active')
        group_id = request.form.get('group_id')
        notes = request.form.get('notes', '').strip()

        # 날짜 처리
        birth_date = None
        if request.form.get('birth_date'):
            birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()

        baptism_date = None
        if request.form.get('baptism_date'):
            baptism_date = datetime.strptime(request.form.get('baptism_date'), '%Y-%m-%d').date()

        registration_date = None
        if request.form.get('registration_date'):
            registration_date = datetime.strptime(request.form.get('registration_date'), '%Y-%m-%d').date()
        else:
            registration_date = date.today()

        # 유효성 검사
        if not name:
            flash('이름은 필수 입력 항목입니다.', 'danger')
            return render_template('members/form.html', groups=Group.query.all())

        # 교인 생성
        member = Member(
            name=name,
            phone=phone,
            email=email,
            address=address,
            birth_date=birth_date,
            gender=gender,
            baptism_date=baptism_date,
            registration_date=registration_date,
            group_id=int(group_id) if group_id else None,
            status=status,
            notes=notes
        )

        db.session.add(member)
        db.session.commit()

        flash(f'{name} 교인이 등록되었습니다.', 'success')
        return redirect(url_for('member_detail', member_id=member.id))

    groups = Group.query.all()
    return render_template('members/form.html', groups=groups, member=None)


@app.route('/members/<int:member_id>')
def member_detail(member_id):
    """교인 상세 보기"""
    member = Member.query.get_or_404(member_id)
    return render_template('members/detail.html', member=member)


@app.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
def member_edit(member_id):
    """교인 수정"""
    member = Member.query.get_or_404(member_id)

    if request.method == 'POST':
        # 폼 데이터 수집
        member.name = request.form.get('name', '').strip()
        member.phone = request.form.get('phone', '').strip()
        member.email = request.form.get('email', '').strip()
        member.address = request.form.get('address', '').strip()
        member.gender = request.form.get('gender', '')
        member.status = request.form.get('status', 'active')
        member.notes = request.form.get('notes', '').strip()

        group_id = request.form.get('group_id')
        member.group_id = int(group_id) if group_id else None

        # 날짜 처리
        if request.form.get('birth_date'):
            member.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()
        else:
            member.birth_date = None

        if request.form.get('baptism_date'):
            member.baptism_date = datetime.strptime(request.form.get('baptism_date'), '%Y-%m-%d').date()
        else:
            member.baptism_date = None

        if request.form.get('registration_date'):
            member.registration_date = datetime.strptime(request.form.get('registration_date'), '%Y-%m-%d').date()

        # 유효성 검사
        if not member.name:
            flash('이름은 필수 입력 항목입니다.', 'danger')
            return render_template('members/form.html', groups=Group.query.all(), member=member)

        db.session.commit()

        flash(f'{member.name} 교인 정보가 수정되었습니다.', 'success')
        return redirect(url_for('member_detail', member_id=member.id))

    groups = Group.query.all()
    return render_template('members/form.html', groups=groups, member=member)


@app.route('/members/<int:member_id>/delete', methods=['POST'])
def member_delete(member_id):
    """교인 삭제"""
    member = Member.query.get_or_404(member_id)
    name = member.name

    db.session.delete(member)
    db.session.commit()

    flash(f'{name} 교인이 삭제되었습니다.', 'success')
    return redirect(url_for('member_list'))


@app.route('/health')
def health():
    """헬스 체크 (Render용)"""
    return {'status': 'ok'}


# =============================================================================
# 그룹 관리 라우트
# =============================================================================

@app.route('/groups')
def group_list():
    """그룹 목록"""
    groups = Group.query.order_by(Group.name).all()
    return render_template('groups/list.html', groups=groups)


@app.route('/groups/new', methods=['GET', 'POST'])
def group_new():
    """그룹 등록"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        group_type = request.form.get('group_type', '')
        leader_id = request.form.get('leader_id')

        if not name:
            flash('그룹명은 필수 입력 항목입니다.', 'danger')
            return render_template('groups/form.html', members=Member.query.all())

        group = Group(
            name=name,
            group_type=group_type,
            leader_id=int(leader_id) if leader_id else None
        )

        db.session.add(group)
        db.session.commit()

        flash(f'{name} 그룹이 생성되었습니다.', 'success')
        return redirect(url_for('group_list'))

    members = Member.query.order_by(Member.name).all()
    return render_template('groups/form.html', members=members, group=None)


@app.route('/groups/<int:group_id>')
def group_detail(group_id):
    """그룹 상세 보기"""
    group = Group.query.get_or_404(group_id)
    return render_template('groups/detail.html', group=group)


@app.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
def group_edit(group_id):
    """그룹 수정"""
    group = Group.query.get_or_404(group_id)

    if request.method == 'POST':
        group.name = request.form.get('name', '').strip()
        group.group_type = request.form.get('group_type', '')
        leader_id = request.form.get('leader_id')
        group.leader_id = int(leader_id) if leader_id else None

        if not group.name:
            flash('그룹명은 필수 입력 항목입니다.', 'danger')
            return render_template('groups/form.html', members=Member.query.all(), group=group)

        db.session.commit()

        flash(f'{group.name} 그룹이 수정되었습니다.', 'success')
        return redirect(url_for('group_detail', group_id=group.id))

    members = Member.query.order_by(Member.name).all()
    return render_template('groups/form.html', members=members, group=group)


@app.route('/groups/<int:group_id>/delete', methods=['POST'])
def group_delete(group_id):
    """그룹 삭제"""
    group = Group.query.get_or_404(group_id)
    name = group.name

    # 소속 교인들의 그룹 해제
    for member in group.members:
        member.group_id = None

    db.session.delete(group)
    db.session.commit()

    flash(f'{name} 그룹이 삭제되었습니다.', 'success')
    return redirect(url_for('group_list'))


# =============================================================================
# 출석 관리 라우트
# =============================================================================

@app.route('/attendance')
def attendance_list():
    """출석 현황"""
    # 날짜 파라미터 (기본: 오늘)
    date_str = request.args.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = date.today()

    # 예배 종류 필터
    service_type = request.args.get('service', '주일예배')

    # 해당 날짜의 출석 기록
    attendance_records = Attendance.query.filter_by(
        date=selected_date,
        service_type=service_type
    ).all()

    # 출석한 교인 ID 목록
    attended_ids = {r.member_id for r in attendance_records if r.attended}

    # 전체 활동 교인
    members = Member.query.filter(Member.status.in_(['active', 'newcomer'])).order_by(Member.name).all()

    return render_template('attendance/list.html',
                         members=members,
                         attended_ids=attended_ids,
                         selected_date=selected_date,
                         service_type=service_type)


@app.route('/attendance/check', methods=['POST'])
def attendance_check():
    """출석 체크 처리"""
    selected_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    service_type = request.form.get('service_type', '주일예배')
    member_ids = request.form.getlist('member_ids')

    # 기존 출석 기록 삭제 (해당 날짜 + 예배 종류)
    Attendance.query.filter_by(date=selected_date, service_type=service_type).delete()

    # 새 출석 기록 생성
    for member_id in member_ids:
        attendance = Attendance(
            member_id=int(member_id),
            date=selected_date,
            service_type=service_type,
            attended=True
        )
        db.session.add(attendance)

    db.session.commit()

    flash(f'{selected_date.strftime("%Y-%m-%d")} {service_type} 출석이 저장되었습니다. ({len(member_ids)}명)', 'success')
    return redirect(url_for('attendance_list', date=selected_date.strftime('%Y-%m-%d'), service=service_type))


@app.route('/attendance/stats')
def attendance_stats():
    """출석 통계"""
    # 최근 4주 출석 통계
    from sqlalchemy import func

    stats = db.session.query(
        Attendance.date,
        Attendance.service_type,
        func.count(Attendance.id).label('count')
    ).filter(
        Attendance.attended == True
    ).group_by(
        Attendance.date,
        Attendance.service_type
    ).order_by(
        Attendance.date.desc()
    ).limit(20).all()

    return render_template('attendance/stats.html', stats=stats)


# =============================================================================
# 데이터베이스 초기화
# =============================================================================

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, port=5000)

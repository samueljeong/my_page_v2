"""
GPT Chat API Blueprint
/api/gpt/* 엔드포인트 담당

의존성:
- db_connection_func: get_db_connection 함수 (set_db_connection으로 주입)
- openai_client: OpenAI 클라이언트 (set_openai_client으로 주입)
- use_postgres: PostgreSQL 사용 여부 (set_use_postgres로 주입)
"""

import os
from flask import Blueprint, request, jsonify, render_template
from error_handlers import error_response, ERROR_MESSAGES
from logging_config import get_logger
from gpt_config import DEFAULT_USERS, USER_PROFILES, get_system_prompt_for_user
from services.gpt_service import analyze_question_complexity

logger = get_logger(__name__)

# Blueprint 생성 (template_folder 지정 필요: 상위 디렉토리의 templates 폴더 사용)
gpt_bp = Blueprint('gpt', __name__, template_folder='../templates')

# ===== 의존성 주입 =====
_db_connection_func = None
_openai_client = None
_use_postgres = False


def set_db_connection(func):
    """DB 연결 함수 주입"""
    global _db_connection_func
    _db_connection_func = func


def set_openai_client(client):
    """OpenAI 클라이언트 주입"""
    global _openai_client
    _openai_client = client


def set_use_postgres(value: bool):
    """PostgreSQL 사용 여부 설정"""
    global _use_postgres
    _use_postgres = value


def get_db_connection():
    """DB 연결 함수 호출"""
    if _db_connection_func is None:
        raise RuntimeError("DB connection function not set. Call set_db_connection first.")
    return _db_connection_func()


# ===== 상수 =====
GPT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'gpt_chat')
GPT_CONVERSATIONS_FILE = os.path.join(GPT_DATA_DIR, 'conversations.json')
GPT_USERS_FILE = os.path.join(GPT_DATA_DIR, 'users.json')


# ===== 헬퍼 함수 =====

def ensure_gpt_data_dir():
    """GPT 데이터 디렉토리 생성"""
    os.makedirs(GPT_DATA_DIR, exist_ok=True)


def load_gpt_users():
    """사용자 목록 로드 (PostgreSQL)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM gpt_users ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if rows:
            return [row['user_id'] if isinstance(row, dict) else row[0] for row in rows]
        else:
            save_gpt_users(DEFAULT_USERS)
            return DEFAULT_USERS.copy()
    except Exception as e:
        print(f"[GPT] 사용자 로드 실패: {e}")
        return DEFAULT_USERS.copy()


def save_gpt_users(users):
    """사용자 목록 저장 (PostgreSQL)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for user_id in users:
            if _use_postgres:
                cursor.execute(
                    "INSERT INTO gpt_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                    (user_id,)
                )
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO gpt_users (user_id) VALUES (?)",
                    (user_id,)
                )

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[GPT] 사용자 저장 완료: {users}")
        return True
    except Exception as e:
        print(f"[GPT] 사용자 저장 실패: {e}")
        return False


def load_gpt_conversations_for_user(user_id: str):
    """특정 사용자의 대화 목록 로드 (N+1 쿼리 최적화: JOIN 사용)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 단일 JOIN 쿼리로 모든 데이터 가져오기 (N+1 쿼리 방지)
        cursor.execute(
            """SELECT c.conversation_id, c.created_at as conv_created, c.updated_at as conv_updated,
                      m.role, m.content, m.model, m.has_image, m.created_at as msg_created
               FROM gpt_conversations c
               LEFT JOIN gpt_messages m ON c.user_id = m.user_id AND c.conversation_id = m.conversation_id
               WHERE c.user_id = %s
               ORDER BY c.updated_at DESC, m.created_at ASC""" if _use_postgres else
            """SELECT c.conversation_id, c.created_at as conv_created, c.updated_at as conv_updated,
                      m.role, m.content, m.model, m.has_image, m.created_at as msg_created
               FROM gpt_conversations c
               LEFT JOIN gpt_messages m ON c.user_id = m.user_id AND c.conversation_id = m.conversation_id
               WHERE c.user_id = ?
               ORDER BY c.updated_at DESC, m.created_at ASC""",
            (user_id,)
        )
        rows = cursor.fetchall()

        # 결과를 대화별로 그룹화
        result = {}
        for row in rows:
            conv_id = row['conversation_id'] if isinstance(row, dict) else row[0]

            if conv_id not in result:
                conv_created = row['conv_created'] if isinstance(row, dict) else row[1]
                conv_updated = row['conv_updated'] if isinstance(row, dict) else row[2]
                result[conv_id] = {
                    'created_at': conv_created.isoformat() if hasattr(conv_created, 'isoformat') else str(conv_created) if conv_created else None,
                    'updated_at': conv_updated.isoformat() if hasattr(conv_updated, 'isoformat') else str(conv_updated) if conv_updated else None,
                    'messages': []
                }

            # 메시지가 있는 경우에만 추가 (LEFT JOIN으로 메시지 없는 대화도 포함)
            role = row['role'] if isinstance(row, dict) else row[3]
            if role is not None:
                msg_created = row['msg_created'] if isinstance(row, dict) else row[7]
                result[conv_id]['messages'].append({
                    'role': role,
                    'content': row['content'] if isinstance(row, dict) else row[4],
                    'model': row['model'] if isinstance(row, dict) else row[5],
                    'has_image': bool(row['has_image'] if isinstance(row, dict) else row[6]),
                    'timestamp': msg_created.isoformat() if hasattr(msg_created, 'isoformat') else str(msg_created) if msg_created else None
                })

        cursor.close()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"[GPT] 대화 로드 실패: {e}", exc_info=True)
        return {}


def save_gpt_message(user_id: str, conversation_id: str, role: str, content: str, model: str = None, has_image: bool = False):
    """단일 메시지 저장 (PostgreSQL)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if _use_postgres:
            cursor.execute(
                """INSERT INTO gpt_conversations (user_id, conversation_id)
                   VALUES (%s, %s)
                   ON CONFLICT (user_id, conversation_id)
                   DO UPDATE SET updated_at = CURRENT_TIMESTAMP""",
                (user_id, conversation_id)
            )
            cursor.execute(
                """INSERT INTO gpt_messages (user_id, conversation_id, role, content, model, has_image)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, conversation_id, role, content, model, has_image)
            )
        else:
            cursor.execute(
                """INSERT OR REPLACE INTO gpt_conversations (user_id, conversation_id, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (user_id, conversation_id)
            )
            cursor.execute(
                """INSERT INTO gpt_messages (user_id, conversation_id, role, content, model, has_image)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, conversation_id, role, content, model, 1 if has_image else 0)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"[GPT] 메시지 저장 실패: {e}", exc_info=True)
        return False


def delete_gpt_conversation(user_id: str, conversation_id: str):
    """대화 삭제 (PostgreSQL)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if _use_postgres:
            cursor.execute(
                "DELETE FROM gpt_messages WHERE user_id = %s AND conversation_id = %s",
                (user_id, conversation_id)
            )
            cursor.execute(
                "DELETE FROM gpt_conversations WHERE user_id = %s AND conversation_id = %s",
                (user_id, conversation_id)
            )
        else:
            cursor.execute(
                "DELETE FROM gpt_messages WHERE user_id = ? AND conversation_id = ?",
                (user_id, conversation_id)
            )
            cursor.execute(
                "DELETE FROM gpt_conversations WHERE user_id = ? AND conversation_id = ?",
                (user_id, conversation_id)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[GPT] 대화 삭제 실패: {e}")
        return False


def delete_gpt_user(user_id: str):
    """사용자 삭제 (PostgreSQL)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if _use_postgres:
            cursor.execute("DELETE FROM gpt_messages WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM gpt_conversations WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM gpt_users WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM gpt_messages WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM gpt_conversations WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM gpt_users WHERE user_id = ?", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[GPT] 사용자 삭제 실패: {e}")
        return False


# ===== 라우트 =====

@gpt_bp.route('/gpt-chat')
def gpt_chat_page():
    """GPT Chat 페이지 렌더링"""
    return render_template('gpt-chat.html')


@gpt_bp.route('/api/gpt/chat', methods=['POST'])
def api_gpt_chat():
    """GPT Chat API - 질문 복잡도에 따른 자동 모델 라우팅"""
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        model_preference = data.get('model', 'auto')
        history = data.get('history', [])
        user_id = data.get('user_id', 'default')
        conversation_id = data.get('conversation_id')
        has_image = data.get('has_image', False)
        image_base64 = data.get('image')

        if not message and not image_base64:
            return jsonify({"ok": False, "error": "메시지를 입력하세요"})

        if model_preference == 'auto':
            selected_model = analyze_question_complexity(message, has_image or bool(image_base64))
        else:
            selected_model = model_preference

        print(f"[GPT] 모델 선택: {selected_model} (preference: {model_preference}, user: {user_id}, has_image: {bool(image_base64)})")

        system_prompt = get_system_prompt_for_user(user_id)

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            messages.append({
                "role": h.get('role', 'user'),
                "content": h.get('content', '')
            })

        client = _openai_client
        if client is None:
            return jsonify({"ok": False, "error": "OpenAI client not configured"})

        if image_base64 and selected_model == 'gpt-4o':
            user_content = [{"type": "text", "text": message or "이 이미지에 대해 설명해주세요."}]

            if image_base64.startswith('data:'):
                user_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            else:
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}})

            messages.append({"role": "user", "content": user_content})

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            assistant_response = response.choices[0].message.content
            model_used = "gpt-4o"

        elif selected_model == 'gpt-5.2':
            messages.append({"role": "user", "content": message})

            input_messages = []
            for msg in messages:
                input_messages.append({
                    "role": msg["role"],
                    "content": [{"type": "input_text", "text": msg["content"]}]
                })

            response = client.responses.create(
                model="gpt-5.2",
                input=input_messages,
                temperature=0.7
            )

            if getattr(response, "output_text", None):
                assistant_response = response.output_text.strip()
            else:
                text_chunks = []
                for item in getattr(response, "output", []) or []:
                    for content in getattr(item, "content", []) or []:
                        if getattr(content, "type", "") == "text":
                            text_chunks.append(getattr(content, "text", ""))
                assistant_response = "\n".join(text_chunks).strip()

            model_used = "gpt-5.2"

        else:
            messages.append({"role": "user", "content": message})
            max_tokens = 2000 if selected_model == 'gpt-4o-mini' else 4000

            response = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens
            )
            assistant_response = response.choices[0].message.content
            model_used = selected_model

        if conversation_id:
            try:
                save_gpt_message(user_id, conversation_id, 'user', message, None, bool(image_base64))
                save_gpt_message(user_id, conversation_id, 'assistant', assistant_response, model_used, False)
            except Exception as e:
                print(f"[GPT] 대화 저장 오류: {e}")

        return jsonify({
            "ok": True,
            "response": assistant_response,
            "model_used": model_used,
            "complexity": "complex" if model_used == "gpt-5.2" else "simple"
        })

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"], log_prefix="GPT채팅")


@gpt_bp.route('/api/gpt/conversations', methods=['GET'])
def api_gpt_get_conversations():
    """사용자별 대화 목록 조회"""
    try:
        user_id = request.args.get('user_id', 'default')
        user_convs = load_gpt_conversations_for_user(user_id)

        result = []
        for conv_id, conv_data in user_convs.items():
            title = "새 대화"
            for msg in conv_data.get('messages', []):
                if msg.get('role') == 'user':
                    title = msg.get('content', '')[:50] + ('...' if len(msg.get('content', '')) > 50 else '')
                    break

            result.append({
                'id': conv_id,
                'title': title,
                'created_at': conv_data.get('created_at'),
                'updated_at': conv_data.get('updated_at'),
                'message_count': len(conv_data.get('messages', []))
            })

        result.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return jsonify({"ok": True, "conversations": result})

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"])


@gpt_bp.route('/api/gpt/conversations/<conversation_id>', methods=['GET'])
def api_gpt_get_conversation(conversation_id):
    """특정 대화 조회"""
    try:
        user_id = request.args.get('user_id', 'default')
        user_convs = load_gpt_conversations_for_user(user_id)
        conv_data = user_convs.get(conversation_id)

        if not conv_data:
            return jsonify({"ok": False, "error": "대화를 찾을 수 없습니다"})

        return jsonify({
            "ok": True,
            "conversation": {
                'id': conversation_id,
                'messages': conv_data.get('messages', []),
                'created_at': conv_data.get('created_at'),
                'updated_at': conv_data.get('updated_at')
            }
        })

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"])


@gpt_bp.route('/api/gpt/conversations/<conversation_id>', methods=['DELETE'])
def api_gpt_delete_conversation(conversation_id):
    """대화 삭제"""
    try:
        user_id = request.args.get('user_id', 'default')

        if delete_gpt_conversation(user_id, conversation_id):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "대화를 찾을 수 없습니다"})

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"])


@gpt_bp.route('/api/gpt/users', methods=['GET'])
def api_gpt_get_users():
    """등록된 사용자 목록 조회"""
    try:
        users = load_gpt_users()

        result = []
        for user_id in users:
            user_convs = load_gpt_conversations_for_user(user_id)
            total_messages = sum(len(c.get('messages', [])) for c in user_convs.values())
            result.append({
                'id': user_id,
                'conversation_count': len(user_convs),
                'total_messages': total_messages
            })

        return jsonify({"ok": True, "users": result})

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"])


@gpt_bp.route('/api/gpt/users', methods=['POST'])
def api_gpt_add_user():
    """사용자 추가"""
    try:
        data = request.get_json() or {}
        user_name = data.get('name', '').strip()

        if not user_name:
            return jsonify({"ok": False, "error": "사용자 이름을 입력하세요"})

        users = load_gpt_users()

        if user_name in users:
            return jsonify({"ok": False, "error": "이미 존재하는 사용자입니다"})

        users.append(user_name)
        save_gpt_users(users)

        return jsonify({"ok": True, "users": users})

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"])


@gpt_bp.route('/api/gpt/users/<user_id>', methods=['DELETE'])
def api_gpt_delete_user(user_id):
    """사용자 삭제"""
    try:
        users = load_gpt_users()

        if user_id not in users:
            return jsonify({"ok": False, "error": "사용자를 찾을 수 없습니다"})

        delete_gpt_user(user_id)
        users = load_gpt_users()
        return jsonify({"ok": True, "users": users})

    except Exception as e:
        return error_response(e, ERROR_MESSAGES["chat"])

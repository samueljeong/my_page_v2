# sermon_server.py
import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

def get_client():
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY가 비어 있습니다. Render 대시보드 > Environment에 추가하세요.")
    # 디버그용 로그 (배포 후엔 주석 처리 권장)
    print(f"🔑 OPENAI_API_KEY length={len(key)}, prefix={(key[:6] if len(key)>=6 else key)}")
    return OpenAI(api_key=key)

client = get_client()

@app.route("/")
def home():
    return render_template("sermon.html")

@app.route("/sermon")
def sermon():
    return render_template("sermon.html")

# 헬스체크/키체크(마스킹)
@app.route("/health")
def health():
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    masked = f"{key[:3]}***{key[-3:]}" if len(key) >= 7 else "(none)"
    return jsonify({
        "ok": True,
        "key_present": bool(key),
        "key_len": len(key),
        "key_masked": masked,
        "prefix": key[:6]
    })

# ✅ 기존 @app.route("/api/sermon/analyze", ...) 함수 전부 교체
@app.route("/api/sermon/analyze", methods=["POST"])
def api_sermon_analyze():
    data = request.json or {}
    guide = data.get("guide", "")
    bible_text = data.get("text", "")
    ref = data.get("ref", "")
    category = data.get("category", "")

    # 디버그 로그 (Render 로그/로컬 터미널에서 확인 가능)
    print("[ANALYZE] payload =>", {
        "len_guide": len(guide),
        "len_text": len(bible_text),
        "ref": ref,
        "category": category,
    })

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You help a Korean pastor. Always apply user's guide first."
                },
                {
                    "role": "user",
                    "content": f"[지침]\n{guide}\n\n[카테고리]\n{category}\n\n[본문]\n{ref}\n{bible_text}"
                }
            ],
            temperature=0.7,
        )

        # 혹시 None 방지
        result_text = (completion.choices[0].message.content or "").strip()
        print("[ANALYZE] result length =>", len(result_text))

        return jsonify({"ok": True, "result": result_text})

    except Exception as e:
        # 에러를 항상 JSON으로, 그리고 내용 최대한 보여주기
        err_text = ""
        try:
            # OpenAI SDK 에러 응답 원문
            if hasattr(e, "response") and getattr(e.response, "text", None):
                err_text = e.response.text
        except Exception:
            pass
        if not err_text:
            err_text = str(e)

        print("[ANALYZE][ERROR]", err_text)
        # 200으로 내려도 되고, 500으로 내려도 됩니다. (프런트에서 둘 다 처리)
        return jsonify({"ok": False, "error": err_text}), 200
    
    
@app.route("/api/sermon/prompt", methods=["POST"])
def api_sermon_prompt():
    data = request.json or {}
    guide = data.get("guide", "")
    ref = data.get("ref", "")
    category = data.get("category", "")
    bible_text = data.get("text", "")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create sermon-generation prompts."},
                {"role": "user", "content": (
                    f"[지침]\n{guide}\n\n"
                    f"[카테고리]\n{category}\n\n"
                    f"[본문]\n{ref}\n{bible_text}\n\n"
                    "위 정보를 이용해서 GPT에 붙여넣을 설교문 제작 프롬포트를 만들어줘."
                )}
            ],
        )
        return jsonify({"result": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============ 여기부터 추가 ============

@app.route("/message")
def message():
    return render_template("message.html")

# 오전 메시지 생성
@app.route("/api/message/morning", methods=["POST"])
def api_morning_message():
    data = request.json or {}
    guide = data.get("guide", "")
    bible_text = data.get("text", "")
    ref = data.get("ref", "")
    date = data.get("date", "")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You help create morning devotional messages in Korean."},
                {"role": "user", "content": f"[오전 지침]\n{guide}\n\n[날짜]\n{date}\n\n[본문]\n{ref}\n{bible_text}"}
            ],
            temperature=0.7,
        )
        result_text = (completion.choices[0].message.content or "").strip()
        return jsonify({"ok": True, "result": result_text})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

# 저녁 메시지 생성
@app.route("/api/message/evening", methods=["POST"])
def api_evening_message():
    data = request.json or {}
    guide = data.get("guide", "")
    bible_text = data.get("text", "")
    ref = data.get("ref", "")
    date = data.get("date", "")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You help create evening devotional messages in Korean."},
                {"role": "user", "content": f"[저녁 지침]\n{guide}\n\n[날짜]\n{date}\n\n[본문]\n{ref}\n{bible_text}"}
            ],
            temperature=0.7,
        )
        result_text = (completion.choices[0].message.content or "").strip()
        return jsonify({"ok": True, "result": result_text})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

# 번역
@app.route("/api/message/translate", methods=["POST"])
def api_translate():
    data = request.json or {}
    guide = data.get("guide", "")
    text = data.get("text", "")
    lang = data.get("lang", "en")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You translate Korean text to {'English' if lang == 'en' else 'Japanese'}."},
                {"role": "user", "content": f"[번역 지침]\n{guide}\n\n[번역할 텍스트]\n{text}"}
            ],
            temperature=0.3,
        )
        result_text = (completion.choices[0].message.content or "").strip()
        return jsonify({"ok": True, "result": result_text})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

# 이미지 프롬프트 생성
@app.route("/api/message/image-prompt", methods=["POST"])
def api_image_prompt():
    data = request.json or {}
    guide = data.get("guide", "")
    message = data.get("message", "")
    time = data.get("time", "morning")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create image and music generation prompts based on devotional messages."},
                {"role": "user", "content": f"[이미지 프롬프트 지침]\n{guide}\n\n[메시지]\n{message}\n\n위 메시지에 맞는 이미지 3개와 배경음악 1개를 생성하는 프롬프트를 작성해주세요."}
            ],
            temperature=0.7,
        )
        result_text = (completion.choices[0].message.content or "").strip()
        return jsonify({"ok": True, "result": result_text})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

# ============ 여기까지 추가 ============

if __name__ == "__main__":
    import os
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5057)), debug=True)
# sermon_server.py
import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

def get_client():
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY가 비어 있습니다.")
    return OpenAI(api_key=key)

client = get_client()

@app.route("/")
def home():
    return render_template("sermon.html")

@app.route("/sermon")
def sermon():
    return render_template("sermon.html")

@app.route("/health")
def health():
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    masked = f"{key[:3]}***{key[-3:]}" if len(key) >= 7 else "(none)"
    return jsonify({
        "ok": True,
        "key_present": bool(key),
        "key_masked": masked,
    })

@app.route("/api/sermon/analyze", methods=["POST"])
def api_sermon_analyze():
    data = request.json or {}
    guide = data.get("guide", "")
    bible_text = data.get("text", "")
    ref = data.get("reference", "")  # ← "reference"로 수정!
    category = data.get("category", "")

    print(f"[ANALYZE] ref={ref}, category={category}, text_len={len(bible_text)}, guide_len={len(guide)}")

    try:
        # 본문이 있으면 포함, 없으면 제외
        content = f"[지침]\n{guide}\n\n[카테고리]\n{category}\n\n[본문]\n{ref}"
        if bible_text:
            content += f"\n\n[본문 내용]\n{bible_text}"

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You help a Korean pastor analyze Bible passages. Always apply user's guide first."
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            temperature=0.7,
        )

        result_text = (completion.choices[0].message.content or "").strip()
        print(f"[ANALYZE] result length: {len(result_text)}")

        return jsonify({"ok": True, "result": result_text})

    except Exception as e:
        err_text = str(e)
        print(f"[ANALYZE][ERROR] {err_text}")
        return jsonify({"ok": False, "error": err_text}), 200

@app.route("/api/sermon/prompt", methods=["POST"])
def api_sermon_prompt():
    data = request.json or {}
    guide = data.get("guide", "")
    ref = data.get("reference", "")  # ← "reference"로 수정!
    category = data.get("category", "")
    bible_text = data.get("text", "")
    analysis = data.get("analysis", "")

    print(f"[PROMPT] ref={ref}, category={category}")

    try:
        content = f"[지침]\n{guide}\n\n[카테고리]\n{category}\n\n[본문]\n{ref}"
        if bible_text:
            content += f"\n\n[본문 내용]\n{bible_text}"
        if analysis:
            content += f"\n\n[본문 분석]\n{analysis}"
        
        content += "\n\n위 정보를 이용해서 GPT에 붙여넣을 설교문 제작 프롬포트를 만들어줘."

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create sermon-generation prompts."},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
        )
        
        result = completion.choices[0].message.content
        return jsonify({"ok": True, "result": result})
        
    except Exception as e:
        print(f"[PROMPT][ERROR] {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 200

if __name__ == "__main__":
    import os
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5057)), debug=True)
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
    return jsonify({"ok": True})

# ===== 처리 단계 실행 API =====
@app.route("/api/sermon/process", methods=["POST"])
def api_process_step():
    """단일 처리 단계 실행"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No data received"}), 400
        
        category = data.get("category", "")
        step_id = data.get("stepId", "")
        step_name = data.get("stepName", "")
        reference = data.get("reference", "")
        text = data.get("text", "")
        guide = data.get("guide", "")
        master_guide = data.get("masterGuide", "")
        previous_results = data.get("previousResults", {})
        
        print(f"[PROCESS] {category} - {step_name}")
        
        # 시스템 메시지 구성
        system_content = "You are an assistant helping to create sermon materials in Korean."
        
        # 총괄 지침이 있으면 추가
        if master_guide:
            system_content += f"\n\n【 카테고리 총괄 지침 】\n{master_guide}\n\n"
            system_content += f"【 현재 단계 】\n- 단계명: {step_name}\n\n"
            system_content += "위 총괄 지침을 반드시 참고하여, 현재 단계의 역할과 비중에 맞게 작성하세요."
        
        # 사용자 메시지 구성
        user_content = f"[성경구절]\n{reference}\n\n"
        
        if text:
            user_content += f"[성경 본문]\n{text}\n\n"
        
        # 이전 단계 결과 추가
        if previous_results:
            user_content += "[이전 단계 결과]\n"
            for prev_id, prev_data in previous_results.items():
                user_content += f"\n### {prev_data['name']}\n{prev_data['result']}\n"
            user_content += "\n"
        
        # 현재 단계 지침 추가
        if guide:
            user_content += f"[{step_name} 단계 지침]\n{guide}\n\n"
        
        user_content += f"위 내용을 바탕으로 '{step_name}' 단계를 작성해주세요."
        
        # GPT 호출
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=0.7,
        )
        
        result = completion.choices[0].message.content.strip()
        return jsonify({"ok": True, "result": result})
        
    except Exception as e:
        print(f"[PROCESS][ERROR] {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 200


# ===== Render 배포를 위한 설정 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5058))
    app.run(host="0.0.0.0", port=port, debug=False)
from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)


GEMINI_API_KEY = "AIzaSyBJbLm1W-zovQ6y4MNJCKp5scilPJ7JaNk"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# =========================
# 🔹 LOAD UNIVERSITY DATA
# =========================
def load_university_data():
    text = ""
    for file in os.listdir("data"):
        if file.endswith(".txt"):
            with open(
                os.path.join("data", file),
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:
                text += f.read() + "\n"
    # 🔴 VERY IMPORTANT: limit size to avoid timeout
    return text[:12000]

UNIVERSITY_DATA = load_university_data()

# =========================
# 🔹 ASK GEMINI (SAFE)
# =========================
def ask_gemini(question):
    prompt = f"""
You are a university assistant.
Answer ONLY using the information below.
If the answer is not found, say:
"Sorry, this information is not available in the university records."

University Information:
{UNIVERSITY_DATA}

Question:
{question}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            GEMINI_URL,
            json=payload,
            timeout=4   # 🔴 MUST be <= 5 sec
        )

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception:
        return "Sorry, I could not retrieve that information right now."

# =========================
# 🔹 ALEXA RESPONSE FORMAT
# =========================
def alexa_response(text, end_session):
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text
            },
            "shouldEndSession": end_session
        }
    })

# =========================
# 🔹 ALEXA WEBHOOK
# =========================
@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json
    request_type = body["request"]["type"]

    # 🔹 Launch
    if request_type == "LaunchRequest":
        return alexa_response(
            "Welcome to University Assistant. Ask me about admissions, fees, departments, or faculty.",
            False
        )

    # 🔹 Intent
    if request_type == "IntentRequest":
        try:
            question = body["request"]["intent"]["slots"]["query"]["value"]
        except:
            question = ""

        answer = ask_gemini(question)
        return alexa_response(answer, True)

    # 🔹 Fallback safety
    return alexa_response(
        "Please ask me about university related information.",
        True
    )

# =========================
# 🔹 RUN SERVER (RENDER)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


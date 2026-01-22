from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# 🔹 Google Gemini API
GEMINI_API_KEY = os.environ.get("AIzaSyBJbLm1W-zovQ6y4MNJCKp5scilPJ7JaNk")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# 🔹 Load ALL TXT files (unchanged)
def load_university_data():
    text = ""
    for file in os.listdir("data"):
        if file.endswith(".txt"):
            with open(os.path.join("data", file),
                      "r", encoding="utf-8", errors="ignore") as f:
                text += f.read() + "\n"
    return text

UNIVERSITY_DATA = load_university_data()

# 🔹 Ask Gemini AI
def ask_gemini(question):
    prompt = f"""
You are a university assistant.
Answer ONLY using the information below.
If the answer is not found, say "Sorry, I do not have that information."

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

    response = requests.post(GEMINI_URL, json=payload)
    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Sorry, I could not process that request."

# 🔹 Alexa webhook
@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json
    req_type = body["request"]["type"]

    if req_type == "LaunchRequest":
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Welcome to University Assistant. Ask me anything about the university."
                },
                "shouldEndSession": False
            }
        })

    if req_type == "IntentRequest":
        try:
            question = body["request"]["intent"]["slots"]["query"]["value"]
        except:
            question = ""

        answer = ask_gemini(question)

        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": answer
                },
                "shouldEndSession": True
            }
        })

    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Sorry, I did not understand."
            },
            "shouldEndSession": True
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

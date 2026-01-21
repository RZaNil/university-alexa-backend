from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Load dataset
def load_data():
    with open("data.txt", "r", encoding="utf-8") as f:
        return f.readlines()

# Find answer from dataset
def find_answer(question):
    question = question.lower()

    for line in load_data():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.lower() in question:
                return value.strip()

    return "Sorry, I could not find that information in the university records."

@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json

    request_type = body["request"]["type"]

    # 👉 When user says: "open university assistant"
    if request_type == "LaunchRequest":
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Welcome to University Assistant. You can ask me about admission, tuition fee, departments or faculty."
                },
                "shouldEndSession": False
            }
        })

    # 👉 When user asks a question
    if request_type == "IntentRequest":
        try:
            user_text = body["request"]["intent"]["slots"]["query"]["value"]
        except:
            user_text = ""

        answer = find_answer(user_text)

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

    # Fallback
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Sorry, I did not understand that."
            },
            "shouldEndSession": True
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

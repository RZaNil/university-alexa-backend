from flask import Flask, request, jsonify

app = Flask(__name__)

# data.txt থেকে সব লাইন পড়া
def load_data():
    with open("data.txt", "r", encoding="utf-8") as f:
        return f.readlines()

# user question এর সাথে data মিলানো
def find_answer(question):
    question = question.lower()
    data = load_data()

    for line in data:
        if ":" in line:
            key, value = line.split(":", 1)
            if key.lower() in question:
                return value.strip()

    return "Sorry, I could not find that information in the university records."

# Alexa webhook
@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json

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
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


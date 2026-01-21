from flask import Flask, request, jsonify
import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# ---------- TEXT CLEANING (NO FILE CHANGE) ----------
def clean_and_split(text):
    sentences = []

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            continue
        if line.isupper():
            continue
        if re.match(r"^[0-9]+[\.\)]", line):
            continue

        parts = re.split(r"(?<=[.!?])\s+", line)
        for p in parts:
            if len(p.split()) > 4:
                sentences.append(p.strip())

    return sentences

# ---------- LOAD ALL TXT FILES ----------
def load_documents():
    all_sentences = []

    for filename in os.listdir("data"):
        if filename.endswith(".txt"):
            with open(os.path.join("data", filename),
                      "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                all_sentences.extend(clean_and_split(text))

    return all_sentences

documents = load_documents()

# ---------- TF-IDF MODEL (LOW MEMORY) ----------
vectorizer = TfidfVectorizer(stop_words="english")
doc_vectors = vectorizer.fit_transform(documents)

def ai_answer(question):
    q_vector = vectorizer.transform([question])
    similarities = cosine_similarity(q_vector, doc_vectors)
    best_index = int(np.argmax(similarities))
    return documents[best_index]

# ---------- ALEXA WEBHOOK ----------
@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json
    request_type = body["request"]["type"]

    if request_type == "LaunchRequest":
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

    if request_type == "IntentRequest":
        try:
            question = body["request"]["intent"]["slots"]["query"]["value"]
        except:
            question = ""

        answer = ai_answer(question)

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
                "text": "Sorry, I could not understand your request."
            },
            "shouldEndSession": True
        }
    })

# ---------- RUN SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



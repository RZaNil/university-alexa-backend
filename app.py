from flask import Flask, request, jsonify
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load AI model (FREE, local)
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------- TEXT CLEANING (NO FILE CHANGE) --------
def clean_and_split(text):
    sentences = []

    for line in text.split("\n"):
        line = line.strip()

        # skip empty lines
        if not line:
            continue

        # skip headings (ALL CAPS)
        if line.isupper():
            continue

        # skip numbered lines
        if re.match(r"^[0-9]+[\.\)]", line):
            continue

        # split paragraph into sentences
        parts = re.split(r"(?<=[.!?])\s+", line)
        for p in parts:
            if len(p.split()) > 4:
                sentences.append(p.strip())

    return sentences

# -------- LOAD ALL TXT FILES FROM data/ --------
def load_documents():
    all_sentences = []

    for filename in os.listdir("data"):
        if filename.endswith(".txt"):
            filepath = os.path.join("data", filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                all_sentences.extend(clean_and_split(text))

    return all_sentences

documents = load_documents()
doc_embeddings = model.encode(documents)

# -------- AI ANSWER FUNCTION --------
def ai_answer(question):
    q_embedding = model.encode([question])
    similarity = cosine_similarity(q_embedding, doc_embeddings)
    best_index = np.argmax(similarity)
    return documents[best_index]

# -------- ALEXA WEBHOOK --------
@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json
    request_type = body["request"]["type"]

    # When user says: "open university assistant"
    if request_type == "LaunchRequest":
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Welcome to University Assistant. You can ask me anything about the university."
                },
                "shouldEndSession": False
            }
        })

    # When user asks a question
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
                "text": "Sorry, I did not understand that."
            },
            "shouldEndSession": True
        }
    })

# -------- RUN SERVER (RENDER COMPATIBLE) --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

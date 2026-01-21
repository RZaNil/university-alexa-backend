from flask import Flask, request, jsonify
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

# 🔹 Lightweight AI model (Free-tier friendly)
model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

# 🔹 Clean & split text automatically (no file editing needed)
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

# 🔹 Load all TXT files from data/ folder
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

# 🔹 Precompute embeddings (lightweight model)
doc_embeddings = model.encode(documents)

# 🔹 Manual cosine similarity (no sklearn, low memory)
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def ai_answer(question):
    q_embedding = model.encode(question)
    scores = [cosine_sim(q_embedding, emb) for emb in doc_embeddings]
    best_index = int(np.argmax(scores))
    return documents[best_index]

# 🔹 Alexa webhook
@app.route("/", methods=["POST"])
def alexa_webhook():
    body = request.json
    request_type = body["request"]["type"]

    # Launch request
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

    # Intent request
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

    # Fallback
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Sorry, I could not understand your question."
            },
            "shouldEndSession": True
        }
    })

# 🔹 Render-compatible server start
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

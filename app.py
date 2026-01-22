"""
East West University Alexa Chatbot Backend
FINAL FIXED VERSION – SLOT SAFE + GROQ LLaMA-3
"""

import os
import glob
import json
from flask import Flask, request, jsonify
from groq import Groq

# =====================
# CONFIG
# =====================
DATA_FOLDER = "data"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =====================
# GROQ CLIENT
# =====================
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq client ready")
else:
    print("❌ GROQ_API_KEY missing")

# =====================
# DATA PROCESSOR
# =====================
class DataProcessor:
    def __init__(self, folder):
        self.folder = folder
        self.cache = None

    def load_all(self):
        if self.cache:
            return self.cache

        texts = []
        files = glob.glob(os.path.join(self.folder, "*.txt"))
        print(f"📁 Loading {len(files)} text files")

        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    texts.append(file.read())
            except:
                pass

        combined = "\n".join(texts)
        self.cache = combined[:12000]  # RAM + latency safe
        return self.cache

    def get_context(self, query, limit=1500):
        data = self.load_all()
        if not data:
            return ""

        words = [w for w in query.lower().split() if len(w) > 2]
        lines = data.split("\n")

        matches = [l for l in lines if any(w in l.lower() for w in words)]
        return "\n".join(matches)[:limit] if matches else data[:limit]

data_processor = DataProcessor(DATA_FOLDER)

# =====================
# AI ANSWER
# =====================
def generate_answer(question):
    if not groq_client:
        return "I can help with East West University information such as scholarships, courses, and faculty."

    context = data_processor.get_context(question)
    if not context:
        return "I don't have that information in the university records."

    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant for East West University. "
                        "Answer ONLY using the provided information. "
                        "If not found, say: "
                        "'I don't have that information in the university records.'"
                    )
                },
                {
                    "role": "user",
                    "content": f"INFORMATION:\n{context}\n\nQUESTION:\n{question}"
                }
            ],
            temperature=0.3,
            max_tokens=250   # 🔴 Alexa safe
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("❌ Groq error:", e)
        return "Sorry, I could not retrieve that information right now."

# =====================
# FLASK APP
# =====================
app = Flask(__name__)

# =====================
# ALEXA ENDPOINT
# =====================
@app.route("/alexa", methods=["POST"])
def alexa():
    body = request.get_json()
    req = body.get("request", {})
    req_type = req.get("type")

    response_text = ""
    should_end = False

    # ---- Launch ----
    if req_type == "LaunchRequest":
        response_text = (
            "Welcome to East West University Assistant. "
            "You can ask about scholarships, CSE faculty, fees, or programs."
        )

    # ---- Intent ----
    elif req_type == "IntentRequest":
        intent = req.get("intent", {})
        intent_name = intent.get("name")
        slots = intent.get("slots", {})

        user_query = ""

        # ✅ FIX 1: Preferred SearchQuery slot
        if "query" in slots and slots["query"].get("value"):
            user_query = slots["query"]["value"]

        # ✅ FIX 2: Any slot fallback
        if not user_query:
            for s in slots.values():
                if s and s.get("value"):
                    user_query = s["value"]
                    break

        # Stop / Cancel
        if intent_name in ["AMAZON.StopIntent", "AMAZON.CancelIntent"]:
            response_text = "Goodbye! Have a great day."
            should_end = True

        elif intent_name == "AMAZON.HelpIntent":
            response_text = (
                "You can ask me about East West University scholarships, "
                "CSE faculty, courses, or admission information."
            )

        elif user_query:
            response_text = generate_answer(user_query)

        else:
            response_text = (
                "Please ask a question about East West University. "
                "For example, who is the chairman of CSE department?"
            )

    # ---- Session End ----
    elif req_type == "SessionEndedRequest":
        response_text = "Goodbye!"
        should_end = True

    # ---- Alexa Response ----
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": response_text
            },
            "card": {
                "type": "Simple",
                "title": "EWU Assistant",
                "content": response_text
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Do you have another question about East West University?"
                }
            },
            "shouldEndSession": should_end
        }
    })

# =====================
# HEALTH
# =====================
@app.route("/")
def home():
    files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    return jsonify({
        "status": "running",
        "model": "LLaMA-3 (Groq)",
        "data_files": len(files),
        "alexa_endpoint": "/alexa"
    })

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print("🚀 EWU Alexa Chatbot running (FINAL FIX)")
    app.run(host="0.0.0.0", port=port)

"""
East West University Alexa Chatbot Backend
SIMPLE WORKING VERSION FOR RENDER
"""

import os
import glob
import json
import logging
from flask import Flask, jsonify, request

# =====================
# ENV CONFIGURATION
# =====================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBJbLm1W-zovQ6y4MNJCKp5scilPJ7JaNk")
SKILL_ID = os.getenv("SKILL_ID", "amzn1.ask.skill.dc127c71-e790-4d0b-98c1-04d4070913b6")
DATA_FOLDER = "data"

# =====================
# GOOGLE GEMINI SETUP
# =====================
GOOGLE_AI_AVAILABLE = False
MODEL = None

try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = genai.GenerativeModel("models/gemini-pro")
    GOOGLE_AI_AVAILABLE = True
    print("Google AI loaded successfully")
except Exception as e:
    print(f"Google AI not available: {e}")

# =====================
# DATA PROCESSOR
# =====================
class DataProcessor:
    def __init__(self, folder="data"):
        self.folder = folder
        self.cache = None

    def load_all_data(self):
        if self.cache:
            return self.cache

        texts = []
        for f in glob.glob(os.path.join(self.folder, "*.txt")):
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    texts.append(file.read())
                    print(f"Loaded: {f}")
            except Exception as e:
                print(f"Error loading {f}: {e}")

        combined = "\n".join(texts)
        self.cache = combined[:12000]
        print(f"Total data loaded: {len(self.cache)} characters")
        return self.cache

    def get_context(self, query, limit=1500):
        data = self.load_all_data()
        if not data:
            return ""

        q = query.lower()
        lines = data.split("\n")
        matched = [l for l in lines if any(w in l.lower() for w in q.split() if len(w) > 2)]

        if not matched:
            return data[:limit]

        return "\n".join(matched)[:limit]

data_processor = DataProcessor()

# =====================
# SAFE AI RESPONSE
# =====================
def generate_answer(question):
    if not GOOGLE_AI_AVAILABLE or MODEL is None:
        return "I can help with East West University information such as scholarships, courses, and faculty."

    context = data_processor.get_context(question)

    prompt = f"""
Answer ONLY using the information below.
If not found, say:
"I don't have that information in the university records."

Information:
{context}

Question:
{question}

Answer:
"""

    try:
        response = MODEL.generate_content(
            prompt,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 300,
            }
        )

        text = response.text.strip()
        return text if text else "I don't have that information in the university records."

    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, I could not find that information in the university records."

# =====================
# FLASK APP
# =====================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# =====================
# SIMPLE ALEXA ENDPOINT
# =====================
@app.route("/alexa", methods=["POST"])
def alexa_endpoint():
    try:
        # Get the Alexa request
        alexa_request = request.get_json()
        
        # Simple request type detection
        request_type = alexa_request.get("request", {}).get("type", "")
        
        if request_type == "LaunchRequest":
            response_text = "Welcome to East West University Assistant. You can ask about scholarships, CSE faculty, fees, or programs."
        elif request_type == "IntentRequest":
            intent_name = alexa_request.get("request", {}).get("intent", {}).get("name", "")
            
            if intent_name == "QueryIntent":
                slots = alexa_request.get("request", {}).get("intent", {}).get("slots", {})
                query = slots.get("query", {}).get("value", "") if "query" in slots else ""
                
                if query:
                    response_text = generate_answer(query)
                else:
                    response_text = "Please ask a question about East West University."
            else:
                response_text = "Please ask me about East West University, such as scholarships, courses, or faculty."
        else:
            response_text = "Welcome to East West University Assistant. How can I help you today?"
        
        # Build Alexa response
        response = {
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
                        "text": "Do you want to ask another question?"
                    }
                },
                "shouldEndSession": False
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error processing Alexa request: {e}")
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Sorry, something went wrong. Please try again."
                },
                "shouldEndSession": False
            }
        })

# =====================
# TEST ENDPOINT
# =====================
@app.route("/test", methods=["GET", "POST"])
def test_endpoint():
    if request.method == "POST":
        question = request.form.get("question", "")
        if not question:
            question = request.json.get("question", "") if request.is_json else ""
    else:
        question = request.args.get("question", "")
    
    if question:
        answer = generate_answer(question)
        return jsonify({
            "question": question,
            "answer": answer,
            "google_ai_available": GOOGLE_AI_AVAILABLE
        })
    
    return jsonify({
        "message": "Send a POST request with 'question' parameter or use GET with ?question=your_question",
        "endpoints": {
            "alexa": "/alexa (POST)",
            "test": "/test (GET/POST)",
            "home": "/"
        }
    })

# =====================
# HEALTH ENDPOINT
# =====================
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "service": "EWU Alexa Chatbot",
        "dataset_files": len(glob.glob(os.path.join(DATA_FOLDER, "*.txt"))),
        "google_ai": GOOGLE_AI_AVAILABLE,
        "endpoints": {
            "alexa": "/alexa",
            "test": "/test",
            "health": "/"
        }
    })

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"Starting server on port {port}")
    print(f"Google AI Available: {GOOGLE_AI_AVAILABLE}")
    print(f"Data folder: {DATA_FOLDER}")
    print(f"Files found: {len(glob.glob(os.path.join(DATA_FOLDER, '*.txt')))}")
    app.run(host="0.0.0.0", port=port, debug=False)

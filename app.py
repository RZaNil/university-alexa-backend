"""
East West University Alexa Chatbot Backend
FINAL STABLE VERSION (Alexa + Render + Google Gemini)
"""

import os
import glob
import logging
from flask import Flask, jsonify, request
from ask_sdk_webservice_support.flask import SkillAdapter
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler
)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from dotenv import load_dotenv

# =====================
# ENV
# =====================
load_dotenv()

# 🔴 HARD-CODED FOR CAPSTONE (Render-safe)
GOOGLE_API_KEY = "AIzaSyBJbLm1W-zovQ6y4MNJCKp5scilPJ7JaNk"
SKILL_ID = "amzn1.ask.skill.dc127c71-e790-4d0b-98c1-04d4070913b6"

DATA_FOLDER = "data"

# =====================
# GOOGLE GEMINI SETUP
# =====================
try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = genai.GenerativeModel("models/gemini-pro")
    GOOGLE_AI_AVAILABLE = True
except Exception as e:
    print("Google AI not available:", e)
    GOOGLE_AI_AVAILABLE = False

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
            except:
                pass

        combined = "\n".join(texts)
        self.cache = combined[:12000]  # 🔴 HARD LIMIT (RAM + TIME SAFE)
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
    if not GOOGLE_AI_AVAILABLE:
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
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=300,
            ),
            request_options={"timeout": 4}  # 🔴 ALEXA SAFE
        )

        text = response.text.strip()
        return text if text else "I don't have that information in the university records."

    except Exception:
        return "Sorry, I could not find that information in the university records."

# =====================
# FLASK APP
# =====================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# =====================
# ALEXA HANDLERS
# =====================
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speech = (
            "Welcome to East West University Assistant. "
            "You can ask about scholarships, CSE faculty, fees, or programs."
        )
        handler_input.response_builder.speak(speech).ask(speech).set_card(
            SimpleCard("EWU Assistant", speech)
        )
        return handler_input.response_builder.response

class QueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("QueryIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        query = slots["query"].value if "query" in slots else ""

        if not query:
            speech = "Please ask a question about East West University."
        else:
            speech = generate_answer(query)

        handler_input.response_builder.speak(speech).ask(
            "Do you want to ask another question?"
        ).set_card(SimpleCard("EWU Assistant", speech))

        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speech = "Please ask me about East West University, such as scholarships, courses, or faculty."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logging.error(exception, exc_info=True)
        speech = "Sorry, something went wrong. Please try again."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

# =====================
# SKILL BUILDER
# =====================
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(QueryIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

skill_adapter = SkillAdapter(
    skill=sb.create(),
    skill_id=SKILL_ID,
    app=app
)

skill_adapter.register(app, route="/alexa")

# =====================
# HEALTH ENDPOINT
# =====================
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "dataset_files": len(glob.glob(os.path.join(DATA_FOLDER, "*.txt"))),
        "google_ai": GOOGLE_AI_AVAILABLE,
        "alexa_endpoint": "/alexa"
    })

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



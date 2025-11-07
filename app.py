# app.py
from flask import Flask, render_template, request, jsonify
from outfit_model6 import get_outfit_for_chatbot
import re, random

app = Flask(__name__, static_folder="static", template_folder="templates")

# --- helper functions (same logic as your Gradio app) ---
def _extract_city(user_text: str) -> str:
    if not user_text:
        return None
    m = re.search(r"\b(?:in|at)\s+([A-Za-z ]+?)(?:\s+(?:on\b|\d{4}-\d{2}-\d{2}\b)|$)", user_text, flags=re.IGNORECASE)
    if m:
        return re.sub(r"\s+on$", "", m.group(1).strip(), flags=re.IGNORECASE)
    return None

def parse_user_input(user_input: str):
    if not user_input:
        return None, None, None, None, None
    low = user_input.lower()
    event = next((ev for ev in ["office", "trip", "marriage", "party"] if ev in low), None)
    gender = next((g for g in ["female", "male"] if g in low), None)
    skin = next((s for s in ["fair", "medium", "dark"] if s in low), None)
    date = None
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", user_input)
    if m:
        date = m.group(1)
    city = _extract_city(user_input)
    return event, gender, skin, date, city

def fashion_tips(user_input):
    low = user_input.lower()
    tips = []
    if "color" in low and "skin" in low:
        tips.append("✨ Fair skin: Pastel colors and soft shades look great.")
        tips.append("✨ Medium skin: Earthy tones like olive, beige, and warm reds suit well.")
        tips.append("✨ Dark skin: Bright colors like royal blue, yellow, fuchsia pop beautifully.")
    if "party" in low or "wedding" in low:
        tips.append("💡 Tip: Add statement accessories for parties or weddings.")
    return "\n".join(tips) if tips else ""

# --- routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True, silent=True) or {}
    user_message = (payload.get("message") or "").strip()

    if not user_message:
        return jsonify({"reply": "Please say or type something.", "html": ""})

    # Parse for event/gender/skin/date/city
    event, gender, skin, date, city = parse_user_input(user_message)

    # Use outfit_model6 to get html + reply
    html, reply = get_outfit_for_chatbot(event, date, gender, skin, city)

    # Greeting override (same as before)
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    if user_message.lower() in greetings:
        reply = random.choice([
            "Hello! I'm your fashion assistant. Tell me about your event and preferences, and I'll suggest outfits.",
            "Hi there! Looking for some outfit ideas? You can tell me your event, location, date, and skin tone."
        ])
        html = ""

    # Add fashion tips if relevant
    tips = fashion_tips(user_message)
    if tips:
        reply = reply + "\n" + tips

    return jsonify({"reply": reply, "html": html})

if __name__ == "__main__":
    # For local testing: debug True. If you want to test from phone, use host='0.0.0.0'
    app.run(debug=True)

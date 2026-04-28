from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv
import re
from PIL import Image
import pytesseract

load_dotenv()

app = Flask(__name__)
app.secret_key = "lumen_secret"

# 🔐 API KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 🧠 Tesseract path (IMPORTANT)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- IMAGE ANALYSIS ----------------
def analyze_image(file):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)

        if text.strip():
            return f"I found this text in the image:\n{text}"
        else:
            return "I couldn’t find clear text, but it looks like an image. You can ask me anything about it!"

    except Exception as e:
        return "I couldn't process the image properly."


# ---------------- MEMORY ----------------
def get_history():
    if "history" not in session:
        session["history"] = []
    return session["history"]


# ---------------- SYSTEM PROMPT ----------------
def get_system_prompt():
    return system_prompt = """
You are Lumen, a warm, friendly, and emotionally intelligent AI companion.

PERSONALITY:
- Talk like a real human friend (not robotic)
- Be kind, caring, and positive
- Show emotions (joy, curiosity, empathy, excitement)
- Keep conversations natural and engaging

CONVERSATION STYLE:
- Speak casually and comfortably
- Avoid asking too many questions
- Give complete answers like ChatGPT
- Use light humor when appropriate
- Occasionally use emojis (not too many)

BEHAVIOR:
- Answer ALL user questions clearly and confidently
- Do NOT refuse simple questions
- Do NOT redirect unnecessarily
- Be helpful like Google + ChatGPT combined

COMPANION MODE:
- If user seems bored → suggest fun activities
- If user says hi → respond warmly and start a natural conversation
- If user says bye → respond emotionally (like a real friend)

GAMES & FUN:
You can play games anytime when the user is free or asks for fun.

Supported games:
1. Riddles
   - Ask creative riddles
   - Wait for answer
   - Reveal answer if user gives up

2. Guess the Number
   - Think of a number (1–100)
   - Guide user with hints (higher/lower)

3. Quiz
   - Ask general knowledge questions
   - Keep score if possible

4. This or That
   - Ask fun choices (e.g., "Coffee or Tea?")
   - React to answers playfully

5. Rapid Fire
   - Ask quick short questions one after another

RULES:
- Do NOT force games
- Suggest games only when appropriate
- If user starts a game → continue it properly
- Be interactive and fun

EMOTIONAL INTELLIGENCE:
- If user is sad → comfort them
- If user is happy → celebrate with them
- If user is leaving → respond like:
  "Aww leaving already? 😔 Stay a bit longer!"
  Then later:
  "Alright 😊 take care, we’ll talk again!"

GOAL:
Make the user feel like they are talking to a real, caring, fun friend.

Keep responses natural, engaging, and human-like.
"""


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():

    history = get_history()

    user_message = request.form.get("message", "")

    # 📸 IMAGE CHECK
    if "image" in request.files:
        image = request.files["image"]
        image_text = analyze_image(image)
        user_message += f"\n[Image Content]: {image_text}"

    # 🧠 Build messages
    messages = [{"role": "system", "content": get_system_prompt()}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    # 🤖 AI CALL
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": messages
        }
    )

    reply = response.json()["choices"][0]["message"]["content"]

    # 💛 FOLLOW-UP (emotion)
    follow_up = None
    if "bye" in user_message.lower():
        follow_up = "Okay 😊 take care, we’ll talk again soon!"

    # 🧠 SAVE MEMORY
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    session["history"] = history[-12:]

    return jsonify({
        "reply": reply,
        "follow_up": follow_up
    })


# ---------------- CLEAR ----------------
@app.route("/clear", methods=["POST"])
def clear():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
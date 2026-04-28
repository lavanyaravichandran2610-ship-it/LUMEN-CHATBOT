from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "lumen_secret"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- MEMORY ----------------
def get_history():
    if "history" not in session:
        session["history"] = []
    return session["history"]


# ---------------- SYSTEM PROMPT ----------------
def get_system_prompt():
    return """
You are Lumen, a friendly and intelligent AI assistant created by Lavanya.

CORE RULE:
- Always answer the user’s question clearly and correctly.
- Never ignore the question.
- Never change the topic unnecessarily.

STYLE:
- Friendly and natural like ChatGPT
- Slight emotional tone (warm, polite)
- Clear and helpful answers

FUN MODE:
- Only suggest games if user asks (bored, play, game)
- Otherwise DO NOT suggest games

SPECIAL:
- "hi" → warm greeting
- "bye" → emotional goodbye

GOAL:
Answer first. Be friendly second.
"""


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():

    history = get_history()
    user_message = request.json.get("message", "")
    msg = user_message.lower()

    # ---------------- DIRECT SMART REPLIES ----------------
    if "who created you" in msg:
        return jsonify({"reply": "I was created by Lavanya 😊", "follow_up": None})

    if msg in ["hi", "hello", "hey"]:
        return jsonify({"reply": "Heyy 😊 Nice to see you! How can I help you today?", "follow_up": None})

    if "bye" in msg:
        return jsonify({
            "reply": "Aww leaving already? 😔 Stay a bit longer!",
            "follow_up": "Alright 😊 take care, we’ll talk again soon!"
        })

    # ---------------- BUILD MESSAGES ----------------
    messages = [{"role": "system", "content": get_system_prompt()}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    # 🎮 Enable game mode ONLY if user asks
    if any(word in msg for word in ["game", "play", "bored"]):
        messages.append({
            "role": "system",
            "content": "User wants fun. Suggest a simple game like riddles or guess the number."
        })

    # ---------------- AI CALL ----------------
    try:
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

    except:
        reply = "Oops 😅 Something went wrong. Try again!"

    # ---------------- FOLLOW-UP ----------------
    follow_up = None
    if "bye" in msg:
        follow_up = "Okay 😊 take care!"

    # ---------------- SAVE MEMORY ----------------
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    session["history"] = history[-10:]

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
from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv
import base64
import random

load_dotenv()

app = Flask(__name__)
app.secret_key = "lumen_secret"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- IMAGE ANALYSIS ----------------
def analyze_image(image, question):
    try:
        image_bytes = image.read()
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        prompt = f"""
You are an intelligent AI.

1. Read the image carefully (extract text if present).
2. Understand the user's question.
3. Give a clear, correct answer.

Question: {question}
"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.2-11b-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded}"
                                }
                            }
                        ]
                    }
                ]
            }
        )

        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return "I couldn't read the image clearly. Try sending a clearer image 😊"


# ---------------- MEMORY ----------------
def get_history():
    if "history" not in session:
        session["history"] = []
    return session["history"]


def save_history(user, bot):
    history = get_history()
    history.append({"role": "user", "content": user})
    history.append({"role": "assistant", "content": bot})
    session["history"] = history[-10:]


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message", "").strip()
    image = request.files.get("image")

    # 📷 IMAGE MODE
    if image:
        reply = analyze_image(image, user_message)
        return jsonify({"reply": reply})

    msg = user_message.lower()

    # ❤️ EMOTIONAL RESPONSES
    if msg in ["hi", "hello", "hey"]:
        reply = "Hey 😊 I'm really happy to see you! How can I help you today?"
        return jsonify({"reply": reply})

    if any(word in msg for word in ["sad", "upset", "tired"]):
        reply = "I'm here for you 💛 You can share anything with me."
        return jsonify({"reply": reply})

    if msg in ["bye", "goodbye"]:
        responses = [
            ("Why are you leaving 😢 Stay a bit more!", "Okay… take care ❤️ Let's talk again soon!"),
            ("Aww leaving already? 😔", "Alright 😊 Bye! Come back anytime.")
        ]
        r = random.choice(responses)
        return jsonify({"reply": r[0], "follow_up": r[1]})

    # 🤖 NORMAL AI CHAT
    try:
        history = get_history()

        messages = [
            {
                "role": "system",
                "content": """
You are Lumen, a friendly AI assistant.

- Be natural like ChatGPT
- Be helpful and clear
- Don't ask unnecessary questions
- Answer confidently
"""
            }
        ]

        messages += history
        messages.append({"role": "user", "content": user_message})

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

        # 🧠 Save memory
        save_history(user_message, reply)

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "Something went wrong 😅 Try again."})


# ---------------- CLEAR ----------------
@app.route("/clear", methods=["POST"])
def clear():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
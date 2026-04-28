from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import base64
import random

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- IMAGE ANALYSIS ----------------
def analyze_image(image, question):
    try:
        img_bytes = image.read()
        encoded = base64.b64encode(img_bytes).decode("utf-8")

        prompt = question if question else "Describe this image clearly."

        res = requests.post(
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

        return res.json()["choices"][0]["message"]["content"]

    except:
        return "Sorry, I couldn't understand the image."


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message", "").strip().lower()
    image = request.files.get("image")

    # 📷 IMAGE MODE
    if image:
        reply = analyze_image(image, user_message)
        return jsonify({"reply": reply})

    # ❤️ EMOTIONS
    if user_message in ["hi", "hello", "hey"]:
        return jsonify({"reply": "Hey! 😊 I'm really happy to see you here."})

    if any(word in user_message for word in ["sad", "tired", "upset"]):
        return jsonify({"reply": "I'm here for you 💛 Tell me what's bothering you."})

    if user_message in ["bye", "goodbye"]:
        replies = [
            ("Aww leaving already? 😢 I enjoyed talking with you.",
             "Okay… take care ❤️ Come back soon!"),
            ("Don't go 😢 Stay a bit more!",
             "Alright… bye 😊 See you soon!")
        ]
        r = random.choice(replies)
        return jsonify({"reply": r[0], "follow_up": r[1]})

    # 🤖 NORMAL AI
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a friendly, helpful AI. Answer clearly and naturally."
                    },
                    {"role": "user", "content": user_message}
                ]
            }
        )

        reply = res.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except:
        return jsonify({"reply": "Something went wrong 😅"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
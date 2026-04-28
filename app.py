from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io
import pytesseract
import random

load_dotenv()

app = Flask(__name__)
app.secret_key = "lumen_secret"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 👉 If Windows, set path like this:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- OCR ----------------
def extract_text(image):
    try:
        img = Image.open(image)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except:
        return ""


# ---------------- VISION ----------------
def vision_answer(image, question):
    try:
        img = Image.open(image)
        img.thumbnail((800, 800))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        encoded = base64.b64encode(buffer.getvalue()).decode()

        prompt = f"""
Analyze this image carefully.

- Understand the content
- Read any visible text
- Answer the question clearly

Question: {question}
"""

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
        return None


# ---------------- HYBRID IMAGE ANALYSIS ----------------
def analyze_image(image, question):
    try:
        # 🔁 Reset pointer for reuse
        image.seek(0)

        # 1️⃣ OCR first (best for text)
        text = extract_text(image)

        if text and len(text) > 20:
            prompt = f"""
This text was extracted from an image:

{text}

Now answer the question:
{question}

Be clear and correct.
"""

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "Answer clearly."},
                        {"role": "user", "content": prompt}
                    ]
                }
            )

            return res.json()["choices"][0]["message"]["content"]

        # 2️⃣ If OCR weak → use vision
        image.seek(0)
        vision_result = vision_answer(image, question)

        if vision_result:
            return vision_result

        # 3️⃣ Final fallback
        return "I can see the image, but I need a clearer or more focused one to give an accurate answer 😊"

    except:
        return "Something went wrong while analyzing the image."


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

    # ❤️ EMOTIONS
    if msg in ["hi", "hello", "hey"]:
        return jsonify({"reply": "Hey 😊 I'm really happy to see you!"})

    if any(word in msg for word in ["sad", "tired", "upset"]):
        return jsonify({"reply": "I'm here for you 💛 Tell me what's wrong."})

    if msg in ["bye", "goodbye"]:
        replies = [
            ("Why are you leaving 😢 Stay a bit more!", "Okay… take care ❤️ Come back soon!"),
            ("Aww leaving already? 😔", "Alright 😊 Bye! See you again!")
        ]
        r = random.choice(replies)
        return jsonify({"reply": r[0], "follow_up": r[1]})

    # 🤖 NORMAL CHAT
    try:
        history = get_history()

        messages = [
            {
                "role": "system",
                "content": "You are a friendly, helpful AI like ChatGPT. Answer clearly and confidently."
            }
        ]

        messages += history
        messages.append({"role": "user", "content": user_message})

        res = requests.post(
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

        reply = res.json()["choices"][0]["message"]["content"]

        save_history(user_message, reply)

        return jsonify({"reply": reply})

    except:
        return jsonify({"reply": "Something went wrong 😅"})


# ---------------- CLEAR ----------------
@app.route("/clear", methods=["POST"])
def clear():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
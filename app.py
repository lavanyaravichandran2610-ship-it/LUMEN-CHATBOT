from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv
import re
import random

load_dotenv()

app = Flask(__name__)
app.secret_key = "lumen_secret"


# 🔐 API KEYS
WEATHER_API = os.getenv("WEATHER_API")
NEWS_API = os.getenv("NEWS_API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- TOOLS ----------------

def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
        data = requests.get(url).json()

        if data.get("cod") != 200:
            return f"Sorry, I couldn't find weather for {city}"

        return f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"
    except:
        return "Weather service unavailable"


def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API}"
        data = requests.get(url).json()

        headlines = [a["title"] for a in data["articles"][:3]]
        return "Top news:\n" + "\n".join(headlines)
    except:
        return "News service unavailable"


def search_google(query):
    try:
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        data = requests.post(url, json={"q": query}, headers=headers).json()

        return data.get("organic", [{}])[0].get("snippet", "No real-time info found")
    except:
        return "Search service unavailable"


# ---------------- CHAT ----------------

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"].strip().lower()

    # ❤️ EMOTIONAL SHORTCUTS

    if user_message in ["hi", "hello", "hey"]:
        return jsonify({
            "reply": "Hey! 😊 I'm really happy to see you here. How are you doing?"
        })

    if any(word in user_message for word in ["sad", "upset", "tired", "depressed"]):
        return jsonify({
            "reply": "I'm really sorry you're feeling this way 💛 I'm here for you. You can talk to me anytime."
        })

    if any(word in user_message for word in ["happy", "excited", "good news"]):
        return jsonify({
            "reply": "That’s amazing! 😄 I’m really happy for you. Tell me more!"
        })

    if user_message in ["bye", "goodbye", "see you"]:
        replies = [
            ("Aww, leaving already? 😢 I really enjoyed talking with you.",
             "Okay… take care ❤️ Come back soon, I’ll be here 😊"),
            ("Don't go yet 😢 I like talking with you!",
             "Alright… bye for now 😊 See you soon!"),
        ]

        r = random.choice(replies)

        return jsonify({
            "reply": r[0],
            "follow_up": r[1]
        })

    # 🧠 NORMAL AI RESPONSE

    system_prompt = """
You are Lumen, a warm, caring, and friendly AI assistant.

- Talk like a real human
- Be kind and supportive
- Keep answers simple and clear
- Add light emotion when appropriate
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
    )

    reply = response.json()["choices"][0]["message"]["content"]

    return jsonify({"reply": reply})


# ---------------- CLEAR ----------------

@app.route("/clear", methods=["POST"])
def clear():
    session.clear()
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
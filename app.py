from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

# 🔐 API KEYS
WEATHER_API = os.getenv("WEATHER_API")
NEWS_API = os.getenv("NEWS_API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# 🔍 Extract city from user input
def get_city(text):
    words = text.split()
    for word in words:
        if word.lower() not in ["weather", "in", "of"]:
            return word.capitalize()
    return "Chennai"


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"].lower()

    # 🌦️ WEATHER (dynamic city)
    if "weather" in user_message:
        city = get_city(user_message)

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
        res = requests.get(url)
        data = res.json()

        try:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]

            return jsonify({
                "reply": f"🌦️ Weather in {city}: {temp}°C, {desc}"
            })
        except:
            return jsonify({"reply": f"😅 Couldn't fetch weather for {city}"})


    # 📰 NEWS
    if "news" in user_message:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API}"
        res = requests.get(url)
        data = res.json()

        try:
            headlines = [a["title"] for a in data["articles"][:3]]

            return jsonify({
                "reply": "📰 Latest News:\n" + "\n".join(headlines)
            })
        except:
            return jsonify({"reply": "😅 Couldn't fetch news"})


    # 🤓 FACT
    if "fact" in user_message:
        res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
        data = res.json()

        return jsonify({
            "reply": f"🤓 {data['text']}"
        })


    # 🤖 AI (fallback for everything else)
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are Lumen, a smart AI like ChatGPT. Be helpful and friendly."},
                    {"role": "user", "content": user_message}
                ]
            }
        )

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        return jsonify({"reply": reply})

    except:
        return jsonify({"reply": "⚠️ AI error. Check API key."})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
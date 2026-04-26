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
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- CITY EXTRACT ----------------
def get_city(text):
    text = text.lower()

    patterns = [
        r"weather.*in ([a-zA-Z ]+)",
        r"temperature.*in ([a-zA-Z ]+)",
        r"in ([a-zA-Z ]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().title()

    words = text.split()
    if len(words) > 1:
        return words[-1].title()

    return "Chennai"


# ---------------- REAL-TIME SEARCH ----------------
def search_google(query):
    url = "https://google.serper.dev/search"

    payload = {"q": query}

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        data = res.json()

        return data["organic"][0]["snippet"]
    except:
        return "😅 Couldn't fetch real-time info"


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"].lower()

    # 🌦️ WEATHER
    if "weather" in user_message or "temperature" in user_message:
        city = get_city(user_message)

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
        res = requests.get(url)
        data = res.json()

        if data.get("cod") != 200:
            return jsonify({"reply": f"❌ Couldn't find weather for {city}"})

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]

        return jsonify({
            "reply": f"🌦️ Weather in {city}: {temp}°C, {desc}"
        })


    # 📰 NEWS
    if "news" in user_message:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API}"
        res = requests.get(url)
        data = res.json()

        if data.get("status") != "ok":
            return jsonify({"reply": "❌ News API error"})

        headlines = [a["title"] for a in data["articles"][:3]]

        return jsonify({
            "reply": "📰 Latest News:\n" + "\n".join(headlines)
        })


    # 🤓 FACT
    if "fact" in user_message:
        res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
        data = res.json()

        return jsonify({
            "reply": f"🤓 {data['text']}"
        })


    # 🔎 REAL-TIME SEARCH (IPL, today, score, etc.)
    if any(word in user_message for word in ["ipl", "score", "today", "latest", "match"]):
        result = search_google(user_message)
        return jsonify({"reply": f"🔎 {result}"})


    # 🤖 AI FALLBACK
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
                    {"role": "system", "content": "You are Lumen, a smart AI like ChatGPT. Be helpful, friendly, and concise."},
                    {"role": "user", "content": user_message}
                ]
            }
        )

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        return jsonify({"reply": reply})

    except Exception as e:
        print("AI ERROR:", e)
        return jsonify({"reply": "⚠️ AI error. Check API key."})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
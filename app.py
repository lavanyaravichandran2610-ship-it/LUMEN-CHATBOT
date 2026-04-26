from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 🔐 API KEYS
WEATHER_API = os.getenv("WEATHER_API")
NEWS_API = os.getenv("NEWS_API")

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"].lower()

    # 🌦️ WEATHER
    if "weather" in user_message:
        city = "Chennai"

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
        res = requests.get(url)
        data = res.json()

        print("WEATHER DEBUG:", data)

        try:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]

            return jsonify({
                "reply": f"🌦️ {city}: {temp}°C, {desc}"
            })
        except:
            return jsonify({"reply": "😅 Couldn't fetch weather"})


    # 📰 NEWS
    if "news" in user_message:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API}"
        res = requests.get(url)
        data = res.json()

        print("NEWS DEBUG:", data)

        try:
            headlines = [a["title"] for a in data["articles"][:3]]

            return jsonify({
                "reply": "📰 Latest News:\n" + "\n".join(headlines)
            })
        except:
            return jsonify({"reply": "😅 Couldn't fetch news"})


    # 🤓 FACTS
    if "fact" in user_message:
        res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
        data = res.json()

        return jsonify({
            "reply": f"🤓 {data['text']}"
        })


    # ❗ DEFAULT
    return jsonify({
        "reply": "Ask me about weather 🌦️, news 📰, or facts 🤓"
    })


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
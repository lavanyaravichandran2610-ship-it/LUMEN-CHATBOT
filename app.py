from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 🔐 ENV VARIABLES
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
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

    # 🕒 DATE & TIME
    if "time" in user_message:
        return jsonify({"reply": f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"})

    if "date" in user_message:
        return jsonify({"reply": f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}"})

    # 🌦️ WEATHER
    if "weather" in user_message:
        city = "Chennai"  # you can improve later

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
        res = requests.get(url)
        data = res.json()

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

        try:
            headlines = [article["title"] for article in data["articles"][:3]]
            news_text = "\n".join([f"📰 {h}" for h in headlines])

            return jsonify({"reply": news_text})
        except:
            return jsonify({"reply": "😅 Couldn't fetch news"})

    # 🤓 FACTS
    if "fact" in user_message:
        res = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
        data = res.json()

        return jsonify({
            "reply": f"🤓 Did you know?\n{data['text']}"
        })

    # 🤖 AI (GROQ)
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Lumen, a friendly chatbot. Talk casually like a human. Keep replies short. Use Tamil + English mix. Use words like 'hmm', 'ok', 'seri'."
                    },
                    {"role": "user", "content": user_message}
                ]
            }
        )

        reply = response.json()["choices"][0]["message"]["content"]

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"😅 AI error: {str(e)}"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv
import re

# Load environment variables
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

        return f"The weather in {city} is {data['main']['temp']}°C with {data['weather'][0]['description']}."
    except:
        return "Weather service is currently unavailable."


def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API}"
        data = requests.get(url).json()

        articles = data.get("articles", [])[:3]
        if not articles:
            return "No news available right now."

        headlines = [a["title"] for a in articles]
        return "Here are the top news headlines:\n" + "\n".join(headlines)
    except:
        return "News service is currently unavailable."


def search_google(query):
    try:
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        data = requests.post(url, json={"q": query}, headers=headers).json()

        return data.get("organic", [{}])[0].get("snippet", "I couldn't find real-time information.")
    except:
        return "Search service is currently unavailable."


# ---------------- MEMORY ----------------

def trim_history(history):
    return history[-10:]


# ---------------- CHAT ----------------

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "")

        if not user_message:
            return jsonify({"reply": "Please enter a message 😊"})

        # 🧠 INIT MEMORY
        if "history" not in session:
            session["history"] = []

        history = session["history"]

        # 🔥 SYSTEM PROMPT
        system_prompt = """
You are Lumen, a friendly AI assistant created by Lavanya.

STYLE:
- Positive and polite
- Natural like ChatGPT
- Clear and short answers

TOOLS:
WEATHER(city)
NEWS()
SEARCH(query)

RULES:
- Use tools only when needed
- If tool needed → return exact format
- Otherwise reply normally
"""

        messages = [{"role": "system", "content": system_prompt}]
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

        ai_reply = response.json()["choices"][0]["message"]["content"]

        # ---------------- TOOL EXECUTION ----------------

        if "WEATHER(" in ai_reply:
            city = re.findall(r"\((.*?)\)", ai_reply)[0]
            result = get_weather(city)

        elif "NEWS()" in ai_reply:
            result = get_news()

        elif "SEARCH(" in ai_reply:
            query = re.findall(r"\((.*?)\)", ai_reply)[0]
            result = search_google(query)

        else:
            result = ai_reply

        # 🤖 FINAL HUMAN-LIKE RESPONSE
        final = requests.post(
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
                        "content": "Make this response friendly, natural, and positive like ChatGPT."
                    },
                    {"role": "user", "content": result}
                ]
            }
        )

        reply = final.json()["choices"][0]["message"]["content"]

        # 🧠 SAVE MEMORY
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        session["history"] = trim_history(history)

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "Something went wrong 😅 Please try again."})


# ---------------- CLEAR ----------------

@app.route("/clear", methods=["POST"])
def clear():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
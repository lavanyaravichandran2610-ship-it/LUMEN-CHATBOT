from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv
import re

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

        headlines = [a["title"] for a in data["articles"][:3]]
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

def summarize_history(history):
    if len(history) < 8:
        return history

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
                    {"role": "system", "content": "Summarize this conversation briefly."},
                    {"role": "user", "content": str(history)}
                ]
            }
        )

        summary = res.json()["choices"][0]["message"]["content"]
        return [{"role": "system", "content": "Memory: " + summary}]

    except:
        return history[-6:]


# ---------------- CHAT ----------------

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]

    # 🧠 INIT MEMORY
    if "history" not in session:
        session["history"] = []

    history = session["history"]

    # 🧠 CONTEXT AWARENESS
    if history:
        last = history[-1]["content"]
        user_message = f"Previous context: {last}\nUser: {user_message}"

    # 🔥 SYSTEM PROMPT
    system_prompt = """
You are Lumen, a friendly and intelligent AI assistant created by Lavanya.

PERSONALITY:
- Positive, polite, and supportive
- Clear and easy to understand
- Natural like ChatGPT

BEHAVIOR:
- Understand the user clearly
- Give helpful responses
- Keep answers simple unless more detail is needed

TOOLS:
1. WEATHER(city)
2. NEWS()
3. SEARCH(query)

RULES:
- Use tools only when needed
- If using tool → respond exactly:
  TOOL_NAME(arguments)
- Otherwise respond normally

STYLE:
- Conversational and friendly
- Avoid robotic replies
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages += summarize_history(history)
    messages.append({"role": "user", "content": user_message})

    # 🤖 FIRST AI CALL
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
        tool_result = get_weather(city)

    elif "NEWS()" in ai_reply:
        tool_result = get_news()

    elif "SEARCH(" in ai_reply:
        query = re.findall(r"\((.*?)\)", ai_reply)[0]
        tool_result = search_google(query)

    else:
        tool_result = ai_reply

    # fallback improvement
    if "unavailable" in tool_result or "couldn't" in tool_result.lower():
        tool_result += " Please try again in a moment."

    # 🤖 FINAL RESPONSE (humanize)
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
                    "content": """
Rewrite this into a friendly, positive, and natural response.
Make it sound like ChatGPT. Keep it clear and helpful.
"""
                },
                {"role": "user", "content": tool_result}
            ]
        }
    )

    reply = final.json()["choices"][0]["message"]["content"]

    # small positivity touch
    if len(reply.split()) < 6:
        reply += " 😊"

    # 🧠 SAVE MEMORY
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    session["history"] = history[-12:]

    return jsonify({"reply": reply})


# ---------------- CLEAR ----------------

@app.route("/clear", methods=["POST"])
def clear():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
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
            return f"Weather not found for {city}"
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
    user_message = request.json["message"].strip()

    # 🧠 QUICK HUMAN GREETING (hard rule)
    if user_message.lower() in ["hi", "hello", "hey", "hii", "helo"]:
        return jsonify({"reply": "Hey! 😊 How can I help you today?"})

    # 🧠 INIT MEMORY
    if "history" not in session:
        session["history"] = []

    history = session["history"]

    # 🧠 CONTEXT
    if history:
        last = history[-1]["content"]
        user_message = f"Previous context: {last}\nUser: {user_message}"

    # 🔥 SYSTEM PROMPT (SMART + HUMAN)
    system_prompt = """
You are Lumen, a friendly and intelligent AI assistant.

BEHAVIOR:
- If user greets → reply casually like a human
- If user asks something → give a clear direct answer
- Do NOT treat simple messages like search queries
- Do NOT give long answers unless needed

RULES:
- Do NOT ask unnecessary questions
- If unclear → assume best meaning and answer
- Be natural, friendly, and simple

TOOLS:
1. WEATHER(city)
2. NEWS()
3. SEARCH(query)

TOOL RULES:
- Use tools only when needed
- If using tool → respond EXACTLY:
  TOOL_NAME(arguments)

STYLE:
- Talk like a real person
- Short, clean, helpful replies
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

    # 🤖 FINAL RESPONSE (HUMAN STYLE)
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
Rewrite this in a natural human tone.

Rules:
- If greeting → short and friendly
- If answer → clear and simple
- No robotic or textbook tone
"""
                },
                {"role": "user", "content": tool_result}
            ]
        }
    )

    reply = final.json()["choices"][0]["message"]["content"]

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
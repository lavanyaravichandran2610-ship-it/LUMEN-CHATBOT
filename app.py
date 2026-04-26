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
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric"
    data = requests.get(url).json()

    if data.get("cod") != 200:
        return f"Couldn't find weather for {city}"

    return f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"


def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API}"
    data = requests.get(url).json()

    headlines = [a["title"] for a in data["articles"][:3]]
    return "Top news:\n" + "\n".join(headlines)


def search_google(query):
    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    data = requests.post(url, json={"q": query}, headers=headers).json()

    try:
        return data["organic"][0]["snippet"]
    except:
        return "No real-time info found"


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]

    # 🧠 MEMORY INIT
    if "history" not in session:
        session["history"] = []

    history = session["history"]

    # 🔥 SYSTEM PROMPT (THIS IS THE MAGIC)
    system_prompt = """
You are Lumen, an intelligent AI assistant like ChatGPT.friendly ai agent,created by Lavanya.

You can:
- Answer general questions naturally
- Use tools when needed

Available tools:
1. WEATHER(city)
2. NEWS()
3. SEARCH(query)

Rules:
- If user asks weather → respond exactly: WEATHER(city)
- If news → NEWS()
- If real-time info → SEARCH(query)
- Otherwise answer normally

Be natural, helpful, and conversational.
be frienly to the user
reply shortly

"""

    # build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    # 🤖 FIRST AI CALL (decide action)
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

    data = response.json()
    ai_reply = data["choices"][0]["message"]["content"]

    # ---------------- TOOL EXECUTION ----------------

    # WEATHER
    if ai_reply.startswith("WEATHER"):
        city = re.findall(r"\((.*?)\)", ai_reply)[0]
        tool_result = get_weather(city)

    # NEWS
    elif ai_reply.startswith("NEWS"):
        tool_result = get_news()

    # SEARCH
    elif ai_reply.startswith("SEARCH"):
        query = re.findall(r"\((.*?)\)", ai_reply)[0]
        tool_result = search_google(query)

    else:
        tool_result = ai_reply  # normal answer

    # 🧠 SECOND AI CALL (make it natural)
    final_response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Convert tool output into a natural, friendly reply."},
                {"role": "user", "content": tool_result}
            ]
        }
    )

    final_data = final_response.json()
    reply = final_data["choices"][0]["message"]["content"]

    # 🧠 SAVE MEMORY
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    session["history"] = history[-10:]

    return jsonify({"reply": reply})


# ---------------- CLEAR ----------------
@app.route("/clear", methods=["POST"])
def clear():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
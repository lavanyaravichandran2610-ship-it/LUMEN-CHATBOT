from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

# 🔐 Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# 🧠 Simple memory (last messages)
chat_history = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message")

        if not user_message:
            return jsonify({"reply": "Empty message 😅"})

        # Store user message
        chat_history.append({"role": "user", "content": user_message})

        # Keep last 6 messages
        recent = chat_history[-6:]

        # 🔐 Get API key safely
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            return jsonify({"reply": "API key missing 😅"})

        # 🤖 Call Cloud AI
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": """
You are Lumen, a friendly ChatGPT-like assistant.

- Talk naturally like a human
- Keep replies short
- Use casual tone (hmm, ok, got it)
- Mix Tamil + English sometimes
"""
                    }
                ] + recent
            }
        )

        data = response.json()

        # ❌ Handle API error
        if "error" in data:
            return jsonify({"reply": f"AI error 😅: {data['error']['message']}"})

        if "choices" not in data:
            return jsonify({"reply": "AI not responding 😅"})

        bot_reply = data["choices"][0]["message"]["content"]

        # Store bot reply
        chat_history.append({"role": "assistant", "content": bot_reply})

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"reply": "Server error 😅"})


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, jsonify, render_template, session
import requests
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = Flask(__name__)

# Secret key for Flask session
app.secret_key = os.getenv("FLASK_SECRET_KEY", "lumen_secret")

# Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq API URL
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- MEMORY ----------------
def get_history():
    if "history" not in session:
        session["history"] = []

    return session["history"]


# ---------------- SYSTEM PROMPT ----------------
def get_system_prompt():
    return """
You are Lumen, a friendly and intelligent AI assistant created by Lavanya.

CORE RULE:
- Always answer the user's question clearly and correctly.
- Never ignore the question.
- Never change the topic unnecessarily.
- If you do not know something, honestly say so.

STYLE:
- Friendly and natural like ChatGPT.
- Warm, polite and helpful.
- Keep simple questions concise.
- Give detailed explanations when needed.
- Use examples when useful.

FUN MODE:
- Only suggest games if the user asks about games, playing, boredom, or fun.
- Otherwise, do NOT suggest games.

SPECIAL:
- If the user says hi, hello or hey, give a warm greeting.
- If the user says bye, give a friendly goodbye.

GOAL:
Answer first. Be friendly second.
"""


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():

    # Check API key
    if not GROQ_API_KEY:
        return jsonify({
            "reply": "Groq API key is missing. Please check your .env file.",
            "follow_up": None
        }), 500

    # Check request data
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "reply": "No message received.",
                "follow_up": None
            }), 400

        user_message = data.get("message", "").strip()

    except Exception as e:
        print("REQUEST ERROR:", e)

        return jsonify({
            "reply": "Invalid request.",
            "follow_up": None
        }), 400

    # Empty message
    if not user_message:
        return jsonify({
            "reply": "Please type something 😊",
            "follow_up": None
        })


    msg = user_message.lower()


    # ---------------- DIRECT SMART REPLIES ----------------

    if "who created you" in msg:
        return jsonify({
            "reply": "I was created by Lavanya 😊",
            "follow_up": None
        })


    if msg in ["hi", "hello", "hey"]:
        return jsonify({
            "reply": "Heyy 😊 Nice to see you! How can I help you today?",
            "follow_up": None
        })


    if msg == "bye":
        return jsonify({
            "reply": "Aww leaving already? 😔 Take care! We'll talk again soon ❤️",
            "follow_up": None
        })


    # ---------------- GET MEMORY ----------------

    history = get_history()


    # ---------------- BUILD MESSAGES ----------------

    messages = [
        {
            "role": "system",
            "content": get_system_prompt()
        }
    ]

    # Add previous conversation
    messages.extend(history)

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })


    # ---------------- GAME MODE ----------------

    if any(word in msg for word in ["game", "play", "bored"]):

        messages.append({
            "role": "system",
            "content": """
The user wants something fun.
Suggest a simple interactive activity such as:
- Riddle
- Guess the number
- Would you rather
- Trivia
Ask the user which one they prefer or start with a simple one.
"""
        })


    # ---------------- CALL GROQ API ----------------

    try:

        print("\n-----------------------------")
        print("Sending request to Groq...")
        print("User:", user_message)
        print("-----------------------------")

        response = requests.post(
            GROQ_URL,

            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },

            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            },

            timeout=60
        )


        # ---------------- DEBUG INFORMATION ----------------

        print("STATUS CODE:", response.status_code)
        print("GROQ RESPONSE:", response.text)


        # Check HTTP errors
        response.raise_for_status()


        # Convert response to JSON
        result = response.json()


        # Check response structure
        if "choices" not in result:

            print("INVALID GROQ RESPONSE:", result)

            return jsonify({
                "reply": "Groq returned an unexpected response. Check the terminal.",
                "follow_up": None
            }), 500


        # Get AI reply
        reply = result["choices"][0]["message"]["content"]


    # ---------------- ERROR HANDLING ----------------

    except requests.exceptions.Timeout:

        print("ERROR: Groq request timed out.")

        return jsonify({
            "reply": "The AI is taking too long to respond 😅 Please try again.",
            "follow_up": None
        }), 504


    except requests.exceptions.HTTPError as e:

        print("HTTP ERROR:", e)
        print("GROQ ERROR RESPONSE:", response.text)

        try:
            error_data = response.json()

            error_message = error_data.get(
                "error",
                {}
            ).get(
                "message",
                "Unknown Groq API error"
            )

        except Exception:
            error_message = response.text


        return jsonify({
            "reply": f"Groq API error: {error_message}",
            "follow_up": None
        }), response.status_code


    except requests.exceptions.RequestException as e:

        print("REQUEST ERROR:", e)

        return jsonify({
            "reply": "Could not connect to Groq 😅 Please check your internet connection.",
            "follow_up": None
        }), 500


    except Exception as e:

        print("UNKNOWN ERROR:", e)

        return jsonify({
            "reply": f"Something went wrong: {str(e)}",
            "follow_up": None
        }), 500


    # ---------------- SAVE MEMORY ----------------

    history.append({
        "role": "user",
        "content": user_message
    })

    history.append({
        "role": "assistant",
        "content": reply
    })


    # Keep only last 10 messages
    session["history"] = history[-10:]

    # Make sure session is saved
    session.modified = True


    # ---------------- RESPONSE ----------------

    return jsonify({
        "reply": reply,
        "follow_up": None
    })


# ---------------- CLEAR MEMORY ----------------
@app.route("/clear", methods=["POST"])
def clear():

    session.pop("history", None)

    return jsonify({
        "status": "cleared",
        "message": "Chat memory cleared successfully."
    })


# ---------------- HEALTH CHECK ----------------
@app.route("/health")
def health():

    return jsonify({
        "status": "Lumen is running",
        "groq_api_key_loaded": bool(GROQ_API_KEY)
    })


# ---------------- RUN ----------------
if __name__ == "__main__":

    print("\n==============================")
    print("        LUMEN CHATBOT")
    print("==============================")

    if GROQ_API_KEY:
        print("Groq API Key: LOADED")
    else:
        print("Groq API Key: NOT FOUND")

    print("Server: http://127.0.0.1:5000")
    print("==============================\n")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )

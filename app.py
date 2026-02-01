import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
GROQ_KEY = os.getenv("GROQ_KEY")

# Clients Initialize
app = Client("fun_ai_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
ai_client = Groq(api_key=GROQ_KEY)

# --- RENDER WEB SERVER (KEEP ALIVE) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Fun AI UserBot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- AI RESPONSE LOGIC ---
def get_ai_reply(user_text):
    try:
        completion = ai_client.chat.completions.create(
            # Model အသစ်ကို ပြောင်းလဲအသုံးပြုထားပါသည်
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "သင်က ဟာသဉာဏ်ရှိတဲ့ မြန်မာလူငယ်တစ်ယောက်ပါ။ စာပြန်ရင် လူငယ် vibe အတိုင်း ပေါ့ပေါ့ပါးပါးနဲ့ မြန်မာလိုပဲ ပြန်ဖြေပေးပါ။"
                },
                {"role": "user", "content": user_text}
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq Error: {str(e)}"

# --- BOT HANDLERS ---
@app.on_message(filters.private & filters.text & ~filters.me)
async def chat_handler(client, message):
    # စာဝင်လာရင် AI က ပြန်ဖြေပေးမည်
    reply = get_ai_reply(message.text)
    await message.reply(reply)

# --- STARTING ---
if __name__ == "__main__":
    # Render ၏ Port Binding အတွက် Flask ကို အရင်စတင်ပါမည်
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("AI UserBot is starting...")
    app.run()

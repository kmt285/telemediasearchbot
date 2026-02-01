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
app = Client("ai_chat_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
ai_client = Groq(api_key=GROQ_KEY)

# --- RENDER PORT BINDING & KEEP ALIVE ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    # ဒီနေရာက Render ကို "ငါ အလုပ်လုပ်နေတယ်" လို့ အကြောင်းကြားတဲ့နေရာပါ
    return "AI Chat UserBot is Active and Online!"

def run_flask():
    # Render က ပေးတဲ့ Port ကို အလိုအလျောက် ဖတ်ပြီး ချိတ်ပါမယ်
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- AI LOGIC ---
def get_ai_response(user_input):
    try:
        completion = ai_client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "သင်က ဖော်ရွေတဲ့ မြန်မာလူငယ်တစ်ယောက်ပါ။ အမေးအဖြေတွေကို မြန်မာလိုပဲ ပြန်ဖြေပေးပါ။"
                },
                {"role": "user", "content": user_input}
            ],
            model="llama3-70b-8192",
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

# စာဝင်လာရင် AI က ပြန်ဖြေမည့်အပိုင်း
@app.on_message(filters.private & filters.text & ~filters.me)
async def chat_handler(client, message):
    # AI ဆီက အဖြေတောင်းပြီး ပြန်ပို့ပေးပါမယ်
    response = get_ai_response(message.text)
    await message.reply(response)

# --- EXECUTION ---
if __name__ == "__main__":
    # ၁။ Flask ကို သီးသန့် Thread တစ်ခုအနေနဲ့ အရင် Run ပါ (Port Binding အတွက်)
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # ၂။ UserBot ကို စတင်ပါ
    print("UserBot is starting...")
    app.run()

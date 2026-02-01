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

app = Client("smart_ai_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
ai_client = Groq(api_key=GROQ_KEY)

# --- RENDER WEB SERVER ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Smart AI Bot is Active!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- AI LOGIC (Smart Prompting) ---
def get_smart_response(user_text):
    try:
        completion = ai_client.chat.completions.create(
            # အားအကောင်းဆုံး Model အသစ်ကို သုံးပါမည်
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": """သင်က Gemini AI လိုမျိုး အရမ်းတော်တဲ့ မြန်မာ AI Assistant တစ်ယောက်ပါ။ 
                    မြန်မာစကားပြောရာမှာ သဘာဝကျရမယ်၊ ယဉ်ကျေးရမယ်။ 
                    တစ်ဖက်လူရဲ့ မေးခွန်းကို သေချာနားလည်အောင် အရင်ဖတ်ပြီးမှ စမတ်ကျကျ ပြန်ဖြေပေးပါ။ 
                    စာလုံးပေါင်းမှားတာ၊ အဓိပ္ပာယ်မရှိတာမျိုး လုံးဝမဖြစ်စေရဘူး။"""
                },
                {"role": "user", "content": user_text}
            ],
            temperature=0.6, # တည်တည်ငြိမ်ငြိမ်နဲ့ မှန်မှန်ကန်ကန် ဖြေနိုင်ရန်
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@app.on_message(filters.private & filters.text & ~filters.me)
async def chat_handler(client, message):
    # AI က အဖြေထုတ်နေတုန်း "typing..." လို့ ပြထားမည်
    await client.send_chat_action(message.chat.id, "typing")
    response = get_smart_response(message.text)
    await message.reply(response)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    app.run()

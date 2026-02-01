import os
import re
from flask import Flask
from threading import Thread
import google.generativeai as genai
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
GEMINI_KEY = os.getenv("GEMINI_KEY")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

# Gemini Setup
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# UserBot Setup
bot = Client("poster_agent", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# --- RENDER PORT FIX (FLASK) ---
app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    return "Magic Poster Agent is Active!"

def run_flask():
    # Render ကပေးတဲ့ Port (ဒါမှမဟုတ် 10000) ကို သေချာ ချိတ်ပေးရပါမယ်
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@bot.on_message(filters.photo & filters.private)
async def analyze_poster(client, message):
    status = await message.reply("📸 ပုံကို ဖတ်နေပါသည်...")
    photo_path = await message.download()
    
    try:
        cookie_img = genai.upload_file(path=photo_path)
        prompt = "ဒီ Poster ထဲက ရုပ်ရှင်နာမည်ကို ရှာပြီး မြန်မာလို အညွှန်းလှလှလေး ရေးပေးပါ။"
        response = model.generate_content([prompt, cookie_img])
        
        await bot.send_photo(chat_id=DEST_CHANNEL, photo=photo_path, caption=response.text)
        await status.edit("✅ Channel ထဲသို့ တင်ပြီးပါပြီ။")
    except Exception as e:
        await status.edit(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Flask ကို Thread တစ်ခုနဲ့ အရင်စတင်ပါ
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is starting...")
    bot.run()


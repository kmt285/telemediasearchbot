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
# Model နာမည်ကို အရှည်အတိုင်း ရေးပေးခြင်းဖြင့် 404 Error ကို ကာကွယ်ပါသည်
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

# UserBot Setup
bot = Client("poster_agent", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# --- RENDER PORT BINDING ---
app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    return "Magic Poster Agent is Online!"

def run_flask():
    # Render ၏ Port (သို့မဟုတ် 10000) ကို သေချာချိတ်ဆက်ရန်
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@bot.on_message(filters.photo & filters.private)
async def analyze_poster(client, message):
    status = await message.reply("📸 AI က ပုံကို လေ့လာနေပါသည်...")
    photo_path = await message.download()
    
    try:
        # Gemini သို့ ပုံပို့ခြင်း
        sample_file = genai.upload_file(path=photo_path)
        
        prompt = """
        ဒီ Poster ပုံထဲက ရုပ်ရှင်နာမည်ကို ဖော်ပြပေးပါ။ 
        ပြီးရင် အဲ့ဒီရုပ်ရှင်အတွက် မြန်မာလို စိတ်ဝင်စားစရာကောင်းတဲ့ အညွှန်း (Caption) ရေးပေးပါ။
        Emoji များ နှင့် သင့်တော်သော Hashtag များ ထည့်ပေးပါ။
        """
        
        # Generation config ထည့်သွင်းခြင်းဖြင့် Error နည်းစေပါသည်
        response = model.generate_content(
            [prompt, sample_file],
            generation_config=genai.GenerationConfig(temperature=0.7)
        )
        
        await bot.send_photo(
            chat_id=DEST_CHANNEL, 
            photo=photo_path, 
            caption=response.text
        )
        await status.edit("✅ Channel ထဲသို့ တင်ပြီးပါပြီ။")
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            await status.edit("❌ Gemini API 404 Error: Model ချိတ်ဆက်မှု လွဲနေပါသည်။")
        else:
            await status.edit(f"❌ Error: {error_msg}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)

# --- EXECUTION ---
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is starting...")
    bot.run()

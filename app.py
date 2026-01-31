import os
import re
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from groq import Groq
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION (Environment Variables) ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING") # UserBot အတွက်
GROQ_KEY = os.getenv("GROQ_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

# Clients Setup
# Bot client
app = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
# User client (String Session သုံးပြီး login ဝင်မှာပါ)
user_app = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

groq_client = Groq(api_key=GROQ_KEY)
db = MongoClient(MONGO_URI)['movie_db']['posted_movies']

# Render အတွက် Web Server (Port error မတက်အောင်)
server = Flask('')
@server.route('/')
def home(): return "Bot is running!"
def run_web(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def is_burmese(text):
    if not text: return False
    return bool(re.search(r'[\u1000-\u109F]', text))

def ai_filter_mmsub(caption, context):
    try:
        prompt = f"Caption: {caption}\nContext: {context}\nIs this a Myanmar Subtitle movie post? Reply 'YES' or 'NO' only."
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192"
        )
        return completion.choices[0].message.content.strip().upper()
    except: return "NO"

@app.on_message(filters.command("find") & filters.private)
async def find_and_post(client, message):
    if len(message.command) < 2:
        return await message.reply("ရုပ်ရှင်နာမည်ပေးပါ။ ဥပမာ - /find Spider-man")
    
    movie_name = message.text.split(None, 1)[1]
    status = await message.reply(f"🔎 '{movie_name}' ကို ရှာဖွေနေပါသည်...")

    async with user_app:
        async for msg in user_app.search_global(movie_name, limit=30):
            if msg.video:
                caption = msg.caption or ""
                recent_msgs = []
                async for r in user_app.get_chat_history(msg.chat.id, limit=3):
                    recent_msgs.append(r.caption or r.text or "")
                
                context = " ".join(recent_msgs)

                if is_burmese(caption) or is_burmese(context):
                    if "YES" in ai_filter_mmsub(caption, context):
                        if not db.find_one({"file_id": msg.video.file_unique_id}):
                            # ၁။ ပထမပို့စ် - စာသားနဲ့ အညွှန်း
                            movie_info = f"🎬 **{movie_name}** (MMSUB)\n\n{caption}"
                            await app.send_message(DEST_CHANNEL, movie_info)
                            # ၂။ ဒုတိယပို့စ် - ရုပ်ရှင်ဖိုင်
                            await msg.copy(DEST_CHANNEL, caption=f"📁 {movie_name}")
                            
                            db.insert_one({"file_id": msg.video.file_unique_id, "name": movie_name})
                            return await status.edit(f"✅ '{movie_name}' ကို တင်ပေးလိုက်ပါပြီ။")

    await status.edit("❌ ရှာမတွေ့ပါဘူး။")

# စက်နှိုးမယ်
if __name__ == "__main__":
    Thread(target=run_web).start()
    print("Bot starting...")
    app.run()
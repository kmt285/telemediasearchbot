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

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")
GROQ_KEY = os.getenv("GROQ_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

# သင်ယုံကြည်ရတဲ့ MMSUB Channel Usernames တွေကို ဒီမှာ စာရင်းသွင်းပါ
SOURCE_CHANNELS = ["@moviesbydatahouse", "@moviesbydatahousefree", "@channelmyanmarfu"] 

app = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
groq_client = Groq(api_key=GROQ_KEY)
db = MongoClient(MONGO_URI)['movie_db']['posted_movies']

server = Flask('')
@server.route('/')
def home(): return "Bot is running!"
def run_web(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def is_burmese(text):
    if not text: return False
    return bool(re.search(r'[\u1000-\u109F]', text))

def ai_filter_mmsub(caption):
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Does this caption belong to a Myanmar Subtitle movie? Caption: {caption}. Answer ONLY 'YES' or 'NO'."}],
            model="llama3-70b-8192"
        )
        return completion.choices[0].message.content.strip().upper()
    except: return "NO"

@app.on_message(filters.command("find") & filters.private)
async def find_in_sources(client, message):
    if len(message.command) < 2:
        return await message.reply("ရုပ်ရှင်နာမည်ပေးပါ။")
    
    movie_name = message.text.split(None, 1)[1]
    status = await message.reply(f"🎯 သတ်မှတ်ထားသော Channel များတွင် '{movie_name}' ကို ရှာနေပါသည်...")

    async with user_app:
        for channel in SOURCE_CHANNELS:
            # သတ်မှတ်ထားတဲ့ channel တစ်ခုချင်းစီမှာ Keyword နဲ့ ရှာမယ်
            async for msg in user_app.search_messages(channel, query=movie_name, filter="video", limit=5):
                caption = msg.caption or ""
                
                # မြန်မာစာ ပါ၊ မပါ စစ်မယ် (AI မစစ်ခင် ရိုးရိုး regex နဲ့ အရင်စစ်တာက ပိုစိတ်ချရပါတယ်)
                if is_burmese(caption) or "MMSUB" in caption.upper():
                    # AI က နောက်ဆုံးအတည်ပြုမယ်
                    if "YES" in ai_filter_mmsub(caption):
                        if not db.find_one({"file_id": msg.video.file_unique_id}):
                            # ပို့စ်တင်မယ်
                            await app.send_message(DEST_CHANNEL, f"🎬 **{movie_name}**\n\n{caption}")
                            await msg.copy(DEST_CHANNEL, caption=f"📁 {movie_name}")
                            db.insert_one({"file_id": msg.video.file_unique_id})
                            return await status.edit(f"✅ '{channel}' မှ ရှာတွေ့၍ တင်ပေးလိုက်ပါပြီ။")
    
    await status.edit("❌ သတ်မှတ်ထားသော Channel များတွင် ရှာမတွေ့ပါ သို့မဟုတ် MMSUB မဟုတ်ပါ။")

if __name__ == "__main__":
    Thread(target=run_web).start()
    app.run()

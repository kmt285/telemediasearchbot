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

# Configuration
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")
GRO_KEY = os.getenv("GROQ_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

app = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
groq_client = Groq(api_key=GRO_KEY)
db = MongoClient(MONGO_URI)['movie_db']['posted_movies']

server = Flask('')
@server.route('/')
def home(): return "Bot is running!"
def run_web(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def is_burmese(text):
    if not text: return False
    # Unicode နှင့် Zawgyi နှစ်မျိုးလုံး ပါနိုင်ခြေကို စစ်သည်
    return bool(re.search(r'[\u1000-\u109F]', text))

def ai_filter_mmsub(caption, context):
    try:
        prompt = f"Caption: {caption}\nContext: {context}\nIs this a Myanmar Subtitle movie post? Reply only 'YES' or 'NO'."
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192"
        )
        answer = completion.choices[0].message.content.strip().upper()
        print(f"DEBUG AI Decision: {answer}") # Log မှာ ကြည့်ရန်
        return answer
    except Exception as e:
        print(f"DEBUG AI Error: {e}")
        return "NO"

@app.on_message(filters.command("find") & filters.private)
async def find_and_post(client, message):
    if len(message.command) < 2:
        return await message.reply("ရုပ်ရှင်နာမည်ပေးပါ။ ဥပမာ - /find Spider-man")
    
    movie_name = message.text.split(None, 1)[1]
    status = await message.reply(f"🔎 '{movie_name}' ကို ရှာဖွေနေပါသည်...")

    found_anything = False
    async with user_app:
        # Search ပိုမိအောင် limit ကို ၅၀ အထိ တိုးလိုက်ပါသည်
        async for msg in user_app.search_global(movie_name, limit=50):
            found_anything = True
            if msg.video:
                caption = msg.caption or ""
                print(f"DEBUG: Found video in {msg.chat.title if msg.chat else 'Unknown'}")
                
                recent_msgs = []
                try:
                    async for r in user_app.get_chat_history(msg.chat.id, limit=5):
                        recent_msgs.append(r.caption or r.text or "")
                except: pass
                
                context = " ".join(recent_msgs)

                # Filter logic ကို ပိုလျော့လိုက်ပါသည် (MMSUB keyword ပါရင်လည်း ပေးတင်မည်)
                is_mmsub_text = any(x in (caption + context).upper() for x in ["MMSUB", "မြန်မာစာတန်းထိုး", "ဘာသာပြန်"])
                
                if is_burmese(caption) or is_burmese(context) or is_mmsub_text:
                    ai_decision = ai_filter_mmsub(caption, context)
                    if "YES" in ai_decision:
                        if not db.find_one({"file_id": msg.video.file_unique_id}):
                            movie_info = f"🎬 **{movie_name}** (MMSUB)\n\n{caption}"
                            await app.send_message(DEST_CHANNEL, movie_info)
                            await msg.copy(DEST_CHANNEL, caption=f"📁 {movie_name}")
                            db.insert_one({"file_id": msg.video.file_unique_id, "name": movie_name})
                            return await status.edit(f"✅ '{movie_name}' ကို တင်ပေးလိုက်ပါပြီ။")

    if not found_anything:
        await status.edit("❌ Telegram Global Search မှာ ဘာမှ ရှာမတွေ့ပါဘူး။ အကောင့် Limit ကြောင့် ဖြစ်နိုင်ပါတယ်။")
    else:
        await status.edit("❌ ရှာတွေ့သော်လည်း မြန်မာစာတန်းထိုး (MMSUB) မဟုတ်၍ မတင်ပေးနိုင်ပါ။")

if __name__ == "__main__":
    Thread(target=run_web).start()
    app.run()

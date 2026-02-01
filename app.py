import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
MONGO_URI = os.getenv("MONGO_URI")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

# Clients Setup
app = Client("mirror_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
db_client = MongoClient(MONGO_URI)
db = db_client['mirror_db']['history']

# --- RENDER PORT BINDING (FLASK) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Super Forwarder is Active and Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@app.on_message(filters.private & filters.text)
async def mirror_logic(client, message):
    # Telegram Link ပါသလား စစ်ဆေးခြင်း
    if "t.me/" in message.text:
        status = await message.reply("⏳ Clone လုပ်နေပါသည်...")
        try:
            # Link မှ Chat ID နှင့် Message ID ကို ခွဲထုတ်ခြင်း
            parts = message.text.split('/')
            source_chat = parts[-2]
            msg_id = int(parts[-1])

            # Username အစား ID သုံးလျှင် -100 ထည့်ပေးရတတ်သည်
            if source_chat.isdigit():
                source_chat = int("-100" + source_chat)

            # တိုက်ရိုက်ကူးယူခြင်း (မူရင်း channel က ဖျက်လည်း မပျက်ပါ)
            cloned_msg = await client.copy_message(
                chat_id=DEST_CHANNEL,
                from_chat_id=source_chat,
                message_id=msg_id
            )

            # MongoDB တွင် မှတ်တမ်းတင်ခြင်း
            db.insert_one({
                "source": source_chat,
                "msg_id": msg_id,
                "new_msg_id": cloned_msg.id
            })

            await status.edit("✅ Clone အောင်မြင်ပြီး Channel ထဲသို့ တင်ပေးလိုက်ပါပြီ!")
            
        except Exception as e:
            await status.edit(f"❌ Error: {str(e)}")

# --- STARTING ---
if __name__ == "__main__":
    # Flask ကို Thread ဖြင့် အရင် Run ပါ
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("UserBot is starting...")
    app.run()

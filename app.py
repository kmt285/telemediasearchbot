import os
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, errors
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

app = Client("mirror_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# --- RENDER PORT FIX ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Online!"
def run_web(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- MIRROR LOGIC ---
@app.on_message(filters.private & filters.text)
async def super_copy(client, message):
    if "t.me/" not in message.text:
        return

    status = await message.reply("⏳ Processing...")
    try:
        # Link ကို ခွဲထုတ်ခြင်း
        parts = message.text.split('/')
        msg_id = int(parts[-1])
        source = parts[-2]

        # Private Channel ID ကို ပြောင်းလဲခြင်း
        if source.isdigit():
            source = int("-100" + source)

        # Peer ကို အရင်ဆုံး Resolve လုပ်ခြင်း (ဒါမှ Peer id invalid မဖြစ်မှာပါ)
        try:
            chat = await client.get_chat(source)
        except errors.RPCError:
            return await status.edit("❌ ဒီ Channel ကို Bot က မသိပါဘူး။ အရင် Join ထားဖို့ လိုအပ်ပါတယ်။")

        # တိုက်ရိုက်ကူးယူခြင်း
        await client.copy_message(
            chat_id=DEST_CHANNEL,
            from_chat_id=chat.id,
            message_id=msg_id
        )
        await status.edit(f"✅ Clone အောင်မြင်ပါပြီ!")

    except Exception as e:
        await status.edit(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    Thread(target=run_web).start() # Render အတွက် Web Port ဖွင့်ခြင်း
    print("UserBot is starting...")
    app.run()

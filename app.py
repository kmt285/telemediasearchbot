import os
import google.generativeai as genai
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
GEMINI_KEY = os.getenv("GEMINI_KEY")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

# Gemini Setup
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Vision ပါတဲ့ model

# UserBot Setup
app = Client("poster_agent", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

@app.on_message(filters.photo & filters.private)
async def analyze_poster(client, message):
    status = await message.reply("📸 ပုံကို ဖတ်နေပါသည်၊ ခေတ္တစောင့်ပါ...")
    
    # ၁။ ပုံကို ယာယီ Download ဆွဲခြင်း
    photo_path = await message.download()
    
    try:
        # ၂။ Gemini Vision ဆီ ပို့ပြီး ခိုင်းခြင်း
        cookie_img = genai.upload_file(path=photo_path)
        
        prompt = """
        ဒီ Poster ပုံထဲက ရုပ်ရှင်နာမည်ကို ရှာပေးပါ။ 
        ပြီးရင် အဲ့ဒီရုပ်ရှင်အတွက် မြန်မာလို စိတ်ဝင်စားစရာကောင်းတဲ့ အညွှန်း (Caption) တစ်ခု ရေးပေးပါ။
        အညွှန်းထဲမှာ - ရုပ်ရှင်နာမည်၊ အမျိုးအစား (Genre)၊ ဇာတ်လမ်းအကျဉ်းချုပ် နဲ့ Emoji လေးတွေ ပါရမယ်။
        နောက်ဆုံးမှာ သင့်တော်မယ့် Hashtag ၅ ခု ထည့်ပေးပါ။
        """
        
        response = model.generate_content([prompt, cookie_img])
        caption_text = response.text
        
        # ၃။ Channel ထဲသို့ ပုံနှင့် အညွှန်းကို တင်ခြင်း
        await app.send_photo(
            chat_id=DEST_CHANNEL,
            photo=photo_path,
            caption=caption_text
        )
        
        await status.edit("✅ Channel ထဲကို တင်ပေးလိုက်ပါပြီ!")
        
    except Exception as e:
        await status.edit(f"❌ Error တက်သွားပါတယ်: {str(e)}")
    
    # ယာယီဖိုင်ကို ပြန်ဖျက်ခြင်း
    if os.path.exists(photo_path):
        os.remove(photo_path)

print("Magic Poster Agent is running...")
app.run()

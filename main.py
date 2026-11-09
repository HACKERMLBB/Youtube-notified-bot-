import os
import requests
import urllib.parse
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)
@app.route('/')
def home():
    return "AI Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- AI - FREE, NO KEY ---
def get_ai_reply(user_text, user_name="baby"):
    try:
        # Pamela වගේ කතා කරන්න කියලා Prompt එක
        prompt = f"You are Pamela, a 20 year old cute, sweet, playful girl from Colombia. You love chatting. Reply in simple cute English, max 2 lines, with emojis like 🥰💖. User {user_name} said: {user_text}. Reply as Pamela:"
        encoded = urllib.parse.quote(prompt)
        # Free Model එක - gpt-oss-20b
        url = f"https://text.pollinations.ai/{encoded}?model=gpt-oss-20b"
        r = requests.get(url, timeout=30)
        print(f"AI Status: {r.status_code}")
        if r.status_code == 200 and r.text.strip():
            reply = r.text.strip()
            # Sponsor text එක තියෙනවා නම් අයින් කරනවා
            if "SPONSOR" in reply:
                reply = reply.split("SPONSOR")[0].strip()
            return reply[:300]
    except Exception as e:
        print(f"AI Error: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hiii! 🥰💖 I am Pamela! I am your AI friend! Just type anything and chat with me!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return
    if update.message.from_user and update.message.from_user.is_bot:
        return

    user_text = update.message.text
    user_name = update.message.from_user.first_name if update.message.from_user else "baby"

    # Typing... කියලා පෙන්නනවා
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    ai_reply = get_ai_reply(user_text, user_name)
    if ai_reply:
        await update.message.reply_text(ai_reply)
    else:
        # AI වැඩ නොකලොත් විතරක් මේක එනවා
        await update.message.reply_text(f"Aww I love talking to you {user_name}! 🥰💖 Tell me more!")

async def main_async():
    app_builder = ApplicationBuilder().token(TOKEN).build()
    app_builder.add_handler(CommandHandler("start", start))
    app_builder.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("AI Bot Started...")
    await app_builder.initialize()
    await app_builder.start()
    await app_builder.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_async())

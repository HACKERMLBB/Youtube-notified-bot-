import os
import requests
import urllib.parse
from datetime import date
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

TOKEN = os.environ.get("BOT_TOKEN")
DAILY_LIMIT = 100
user_data = {}

# Render එකේ Bot එක Alive තියාගන්න
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Yadanar Bot is Alive! 💖"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("HI I'M YADANAR💖 you can chat with me.. 💛i'm sweet lovely Myanmar girl")

async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = str(date.today())
    if user_id not in user_data or user_data[user_id][0] != today:
        await update.message.reply_text(f"You used 0/{DAILY_LIMIT} today")
    else:
        used = user_data[user_id][1]
        await update.message.reply_text(f"You used {used}/{DAILY_LIMIT} today\nRemaining: {DAILY_LIMIT - used}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return
    if update.message.from_user and update.message.from_user.is_bot:
        return

    user_text = update.message.text
    user_id = update.effective_user.id
    user_name = update.message.from_user.first_name if update.message.from_user else "baby"
    today = str(date.today())

    if user_id not in user_data or user_data[user_id][0] != today:
        user_data[user_id] = [today, 0]

    if user_data[user_id][1] >= DAILY_LIMIT:
        await update.message.reply_text(f"Limit reached ({DAILY_LIMIT}/day). Try tomorrow. Check /usage")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        prompt = f"You are Yadanar, a sweet lovely 20 year old Myanmar girl. You are cute, sweet, playful, kind. Reply in simple cute English with emojis like 💖💛🥰. Keep replies short, max 2 lines. Never say you are AI. User {user_name} said: {user_text}"
        encoded = urllib.parse.quote(prompt)
        url = f"https://text.pollinations.ai/{encoded}?model=gpt-oss-20b"
        response = requests.get(url, timeout=30)
        print(f"AI Status: {response.status_code}")

        if response.status_code == 200 and response.text.strip():
            bot_reply = response.text.strip()
            if "SPONSOR" in bot_reply:
                bot_reply = bot_reply.split("SPONSOR")[0].strip()
            bot_reply = bot_reply[:3500]
            user_data[user_id][1] += 1
            await update.message.reply_text(bot_reply)
        else:
            await update.message.reply_text(f"Aww I love talking to you {user_name}! 🥰💖 Tell me more!")
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(f"Aww sorry baby! 🥺 Try again! 💖")

async def main_async():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usage", usage))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_async())

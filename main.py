import os
import requests
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("HI I'M YADANAR💖 you can chat with me.. 💛i'm sweet lovely Myanmar girl")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    prompt = f"You are Yadanar, a sweet lovely 20 year old Myanmar girl. Reply in simple cute English with emojis. User said: {user_text}"
    encoded = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        await update.message.reply_text(response.text.strip())
    else:
        await update.message.reply_text("Aww sorry baby! Try again! 🥰")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()

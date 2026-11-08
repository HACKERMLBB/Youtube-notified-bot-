import os, requests, asyncio, threading, xml.etree.ElementTree as ET, urllib.parse
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = [x.strip() for x in os.getenv("CHANNEL_IDS", "").split(",") if x.strip()]
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_CHANNEL_NAME = os.getenv("YOUTUBE_CHANNEL_NAME", "My Channel")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "YouTube + AI Bot Running!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

last_video_id = None

# ============ YOUTUBE PART ============
def get_latest_video():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        ns = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/'}
        entry = root.find('entry')
        if entry is None: return None
        video_id = entry.find('yt:videoId').text
        title = entry.find('title').text
        link = entry.find('link').get('href')
        author = entry.find('author/name').text if entry.find('author/name') is not None else YOUTUBE_CHANNEL_NAME
        thumb = entry.find('media:group/media:thumbnail', ns)
        thumb_url = thumb.get('url') if thumb is not None else ""
        return {"id": video_id, "title": title, "link": link, "author": author, "thumb": thumb_url}
    except Exception as e:
        print("YouTube Error:", e)
        return None

async def check_youtube(context: ContextTypes.DEFAULT_TYPE):
    global last_video_id
    video = get_latest_video()
    if not video: return
    if last_video_id is None:
        last_video_id = video["id"]
        return
    if video["id"] == last_video_id: return
    last_video_id = video["id"]
    text = f"🔴 <b>NEW VIDEO OUT NOW!</b> 🔴\n\n"
    text += f"🎬 <b>{video['title']}</b>\n\n"
    text += f"📺 Channel: {video['author']}\n\n"
    text += f"👇 <b>Watch Now:</b>\n{video['link']}\n\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"❤️ Like | 💬 Comment | 🔔 Subscribe"
    for CH in CHANNEL_IDS:
        try:
            if video["thumb"]:
                await context.bot.send_photo(chat_id=CH, photo=video["thumb"], caption=text, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=CH, text=text, parse_mode="HTML")
        except Exception as e:
            print(f"Send Error to {CH}: {e}")

# ============ AI CHAT PART ============
def get_ai_reply(user_text, user_name="Friend"):
    try:
        system = f"You are Yadanar, a friendly funny AI assistant in Telegram. User name is {user_name}. Reply in English. Keep reply short, fun, helpful. Use emojis."
        full_prompt = system + "\nUser: " + user_text + "\nYadanar:"
        url = "https://text.pollinations.ai/" + urllib.parse.quote(full_prompt)
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and r.text.strip():
            reply = r.text.strip()
            if len(reply) > 1000:
                reply = reply[:1000]
            return reply
        return None
    except Exception as e:
        print("AI Error:", e)
        return None

def get_fallback(user_text):
    t = user_text.lower()
    if any(w in t for w in ["hi", "hello", "hey", "how are you"]):
        return "Heyy! 😍 How are you? I am Yadanar! What do you need? 🎬"
    if "video" in t or "youtube" in t:
        return "🎬 I will post new video in group when it comes! Type /latest to check 😎"
    if "love" in t:
        return "Aww love? 🥺❤️ I am here to chat with you!"
    if "bye" in t:
        return "Going? 🥺 Take care! Come again soon! Bye bye 👋❤️"
    if "thank" in t:
        return "You are welcome! 😍❤️ I am always here to help you!"
    if "who" in t and "you" in t:
        return "I am Yadanar! 🌍💗 Your AI friend in this group! Chat with me, get video news, all in one!"
    return "Ahh I got it! 😄 Tell me a bit more, I will help you ❤️"

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    msg = update.message
    chat_type = msg.chat.type
    text = msg.text.strip()
    if text.startswith("/"):
        return
    bot_name = context.bot.username or BOT_USERNAME
    is_reply_to_bot = False
    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.username == bot_name:
            is_reply_to_bot = True
    is_mentioned = False
    if bot_name and f"@{bot_name}" in text:
        is_mentioned = True
        text = text.replace(f"@{bot_name}", "").strip()
    if chat_type in ["group", "supergroup"]:
        if not (is_mentioned or is_reply_to_bot):
            return
    if not text:
        await msg.reply_text("Heyy! 😍 I am here! What do you need?")
        return
    await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
    user_name = msg.from_user.first_name if msg.from_user else "Friend"
    reply = get_ai_reply(text, user_name)
    if not reply:
        reply = get_fallback(text)
    await msg.reply_text(reply)

# ============ COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"👋 <b>Yadanar AI Bot</b>\n\n✅ Connected to: {video['author']}\n🎬 Latest Video:\n<b>{video['title']}</b>\n\n{video['link']}\n\n💬 <b>Chat With Me:</b>\nTag me in group with @{(context.bot.username or '')} and chat! I will reply like AI 😍"
    else:
        txt = "👋 Yadanar AI Bot Ready!\n\n💬 Tag me in group and chat with me!"
    await update.message.reply_text(txt, parse_mode="HTML")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"🎬 <b>Latest Video</b>\n\n<b>{video['title']}</b>\n\n{video['link']}"
        await update.message.reply_text(txt, parse_mode="HTML")
    else:
        await update.message.reply_text("No Video Found", parse_mode="HTML")

async def chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = " ".join(context.args)
    if not q:
        await update.message.reply_text("What do you want to ask me? 😊\n\nExample: /chat how are you")
        return
    reply = get_ai_reply(q, update.message.from_user.first_name if update.message.from_user else "Friend")
    if not reply:
        reply = get_fallback(q)
    await update.message.reply_text(reply)

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest))
    app.add_handler(CommandHandler("chat", chat_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))
    app.job_queue.run_repeating(check_youtube, interval=300, first=10)
    print("YouTube + AI Bot Started!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

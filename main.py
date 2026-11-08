import os, requests, asyncio, threading, xml.etree.ElementTree as ET
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = [x.strip() for x in os.getenv("CHANNEL_IDS", "").split(",") if x.strip()]
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_CHANNEL_NAME = os.getenv("YOUTUBE_CHANNEL_NAME", "My Channel")

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "YouTube Notifier Bot Running!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

last_video_id = None

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
        published = entry.find('published').text
        author = entry.find('author/name').text if entry.find('author/name') is not None else YOUTUBE_CHANNEL_NAME
        thumb = entry.find('media:group/media:thumbnail', ns)
        thumb_url = thumb.get('url') if thumb is not None else ""
        return {"id": video_id, "title": title, "link": link, "published": published, "author": author, "thumb": thumb_url}
    except Exception as e:
        print("YouTube Error:", e)
        return None

async def check_youtube(context: ContextTypes.DEFAULT_TYPE):
    global last_video_id
    video = get_latest_video()
    if not video: return
    if last_video_id is None:
        last_video_id = video["id"]
        print(f"First Check: {video['title']}")
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"👋 <b>YouTube Notifier Bot</b>\n\n✅ Connected to: {video['author']}\n🎬 Latest Video:\n<b>{video['title']}</b>\n\n{video['link']}"
    else:
        txt = "👋 YouTube Notifier Bot Ready!\n\nYouTube Channel Not Connected. Check Channel ID."
    await update.message.reply_text(txt, parse_mode="HTML")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"🎬 <b>Latest Video</b>\n\n<b>{video['title']}</b>\n\n{video['link']}"
        await update.message.reply_text(txt, parse_mode="HTML")
    else:
        await update.message.reply_text("No Video Found", parse_mode="HTML")

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest))
    app.job_queue.run_repeating(check_youtube, interval=300, first=10)
    print("YouTube Bot Started!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

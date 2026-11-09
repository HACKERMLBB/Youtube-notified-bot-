import os, requests, asyncio, threading, xml.etree.ElementTree as ET
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = [x.strip() for x in os.getenv("CHANNEL_IDS", "").split(",") if x.strip()]
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID") # UCR4MDIWLNe4p_J-RP0dnS5g
YOUTUBE_CHANNEL_NAME = os.getenv("YOUTUBE_CHANNEL_NAME", "Pamela Cullen")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Pamela YouTube Notifier Running! ✅"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

last_video_id = None

# ✅ කලින් Bot එකේම විදිය - RSS එකෙන්, API නැතුව!
def get_latest_video():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        print(f"RSS Status: {r.status_code} Len: {len(r.content)}")
        root = ET.fromstring(r.content)
        # Namespace 2කටම වැඩ කරන විදිය
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/'}
        entry = root.find('atom:entry', ns)
        if entry is None:
            entry = root.find('entry') # Backup - Namespace නැත්තම්
        if entry is None:
            print("No entry found!")
            return None
        # Title / VideoID / Link / Thumb - 2 විදියටම හොයනවා
        def find_text(tag_atom, tag_plain):
            e = entry.find(tag_atom, ns)
            if e is not None and e.text:
                return e.text
            e2 = entry.find(tag_plain)
            return e2.text if e2 is not None else ""
        def find_link():
            e = entry.find('atom:link', ns)
            if e is not None:
                return e.get('href', '')
            e2 = entry.find('link')
            return e2.get('href', '') if e2 is not None else ""
        video_id = find_text('yt:videoId', 'videoId')
        # yt:videoId නැත්තම් link එකෙන් ගන්නවා
        if not video_id and "v=" in find_link():
            video_id = find_link().split("v=")[-1]
        title = find_text('atom:title', 'title')
        link = find_link()
        published = find_text('atom:published', 'published')
        thumb = entry.find('media:group/media:thumbnail', ns)
        if thumb is None:
            thumb = entry.find('group/thumbnail')
        thumb_url = thumb.get('url') if thumb is not None else ""
        print(f"Found Video: {title} | {video_id}")
        return {"id": video_id, "title": title, "link": link, "published": published, "thumb": thumb_url}
    except Exception as e:
        print("YouTube Error:", e)
        return None

def get_all_videos():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        videos = []
        entries = root.findall('atom:entry', ns)
        if not entries:
            entries = root.findall('entry')
        for entry in entries:
            t = entry.find('atom:title', ns)
            if t is None:
                t = entry.find('title')
            l = entry.find('atom:link', ns)
            if l is None:
                l = entry.find('link')
            if t is not None and l is not None:
                videos.append({"title": t.text, "link": l.get('href','')})
        return videos
    except Exception as e:
        print("Get All Error:", e)
        return []

# ✅ Channel එකට - කලින් වගේ Thumbnail එකත් එක්ක!
async def check_youtube(context: ContextTypes.DEFAULT_TYPE):
    global last_video_id
    video = get_latest_video()
    if not video:
        return
    if last_video_id is None:
        last_video_id = video["id"]
        print(f"First Check: {video['title']}")
        return
    if video["id"] == last_video_id:
        return

    last_video_id = video["id"]
    subscribe_link = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}?sub_confirmation=1"
    text = (
        f"🌸✨・゜✧・゜✧・゜✧・゜✧🌸\n"
        f"🔴 <b>NEW VIDEO IS OUT BABY! 🔥</b>\n"
        f"🌸✨・゜✧・゜✧・゜✧・゜✧🌸\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
        f"🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
        f"🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
        f"🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n"
        f"💬 <b>Let's Laugh, Chat &amp; Be Best Friends Forever! 🫶</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {video['title']}\n🔗 {video['link']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💌 <i>Go watch it now baby! Like &amp; Comment!</i>\n"
        f"💖 <i>I love you so much! You are my everything! 🥰❤️</i>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Watch Now Baby 💖", url=video['link'])],
        [InlineKeyboardButton("🔴 Subscribe Me Baby ❤️", url=subscribe_link)],
        [InlineKeyboardButton("💬 Chat With Me 🥰", url=f"https://t.me/{BOT_USERNAME}")]
    ])
    for CH in CHANNEL_IDS:
        try:
            if video["thumb"]:
                await context.bot.send_photo(chat_id=CH, photo=video["thumb"], caption=text, parse_mode="HTML", reply_markup=buttons)
            else:
                await context.bot.send_message(chat_id=CH, text=text, parse_mode="HTML", reply_markup=buttons)
        except Exception as e:
            print(f"Send Error to {CH}: {e}")

# ✅ Welcome - Latest Video Link එකත් එක්ක!
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    subscribe_link = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}?sub_confirmation=1"
    txt = (
        "🌸✨・゜✧ <b>Welcome to My World</b> ✧゜・✨🌸\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
        "🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
        "🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
        "🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n"
        "💬 <b>Let's Laugh, Chat &amp; Be Best Friends Forever! 🫶</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )
    if video:
        txt += f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {video['title']}\n🔗 {video['link']}\n\n"
    txt += (
        "━━━━━━━━━━━━━━━━━━━\n"
        "💌 <i>\"You made my day by coming here! I love you so much!\" 💖</i>\n\n"
        "👇 <b>My Videos Are Here Baby! 👇</b>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Latest Video 💖", callback_data="latest"), InlineKeyboardButton("📼 Old Video 🌸", callback_data="old")],
        [InlineKeyboardButton("📅 This Month Videos 📆", callback_data="months")],
        [InlineKeyboardButton("▶️ Watch Latest on YouTube 🔥", url=video['link'])] if video else [],
        [InlineKeyboardButton("🔴 Subscribe Me Baby ❤️", url=subscribe_link)]
    ])
    # Thumbnail එකත් එක්ක Welcome එක යවනවා!
    if video and video.get("thumb"):
        await update.message.reply_photo(photo=video["thumb"], caption=txt, parse_mode="HTML", reply_markup=buttons)
    else:
        await update.message.reply_text(txt, parse_mode="HTML", reply_markup=buttons)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "latest":
        video = get_latest_video()
        if video:
            await query.message.reply_text(f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n\n📌 {video['title']}\n🔗 {video['link']}", parse_mode="HTML")
        else:
            await query.message.reply_text("No videos found! 😢")
    elif query.data == "old":
        videos = get_all_videos()
        if videos:
            old = videos[-1]
            await query.message.reply_text(f"📼 <b>My Old Video 🌸</b>\n\n📌 {old['title']}\n🔗 {old['link']}", parse_mode="HTML")
        else:
            await query.message.reply_text("No videos found! 😢")
    elif query.data == "months":
        videos = get_all_videos()
        if videos:
            txt = "📅 <b>My Recent Videos 📆</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            for i, v in enumerate(videos[:10], 1):
                txt += f"{i}. {v['title']}\n🔗 {v['link']}\n\n"
            await query.message.reply_text(txt, parse_mode="HTML")
        else:
            await query.message.reply_text("No videos this month yet! 😢")

async def latest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        await update.message.reply_text(f"🎬 <b>Latest Video</b>\n\n<b>{video['title']}</b>\n\n{video['link']}", parse_mode="HTML")
    else:
        await update.message.reply_text("No Video Found", parse_mode="HTML")

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    # කලින් වගේ විනාඩි 5න් 5ට Check කරනවා!
    app.job_queue.run_repeating(check_youtube, interval=300, first=10)
    print("Pamela YouTube Bot Started!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

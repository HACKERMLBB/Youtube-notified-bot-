import os
import time as time_module
import asyncio
import html
import threading
import xml.etree.ElementTree as ET
from datetime import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://www.youtube.com/@pamelacullen")
CHANNEL_IDS = os.environ.get("CHANNEL_IDS", "")
GROUP_IDS = os.environ.get("GROUP_IDS", "")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

WEBSITE_TEXT = "\n\n🌐 Website: https://pamelacullen.com"
CHANNEL_IDS_LIST = [x.strip() for x in CHANNEL_IDS.split(",") if x.strip()]
GROUP_IDS_LIST = [x.strip() for x in GROUP_IDS.split(",") if x.strip()]
ALL_TARGET_IDS = CHANNEL_IDS_LIST + GROUP_IDS_LIST

VIDEO_CACHE = {"videos": [], "time": 0, "last_id": None}
LAST_VIDEO_FILE = "last_video.txt"

# ================= FLASK KEEP ALIVE =================
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Alive!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_flask, daemon=True).start()

# ================= YOUTUBE FETCH =================
def fetch_rss():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.content and b"<entry" in r.content:
            return r.content
    except:
        pass
    return None

def parse_rss(content, count=10):
    try:
        root = ET.fromstring(content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        videos = []
        for entry in root.findall('atom:entry', ns)[:count]:
            title_elem = entry.find('atom:title', ns)
            link_elem = entry.find('atom:link', ns)
            id_elem = entry.find('yt:videoId', ns)
            if title_elem is None or link_elem is None or id_elem is None:
                continue
            title = title_elem.text or "New Video"
            link = link_elem.attrib.get('href', '')
            vid_id = id_elem.text
            videos.append({"title": title, "link": link, "id": vid_id, "thumb": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"})
        return videos
    except:
        return []

def get_videos_list(count=10):
    if VIDEO_CACHE["videos"]:
        return VIDEO_CACHE["videos"][:count]
    content = fetch_rss()
    if content:
        videos = parse_rss(content, count)
        if videos:
            VIDEO_CACHE["videos"] = videos
            VIDEO_CACHE["time"] = time_module.time()
            return videos
    return []

def get_latest_video():
    vids = get_videos_list(1)
    if vids:
        return vids[0]
    return None

def get_last_video_id():
    if VIDEO_CACHE.get("last_id"):
        return VIDEO_CACHE["last_id"]
    if os.path.exists(LAST_VIDEO_FILE):
        try:
            with open(LAST_VIDEO_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return None

def save_last_video_id(vid_id):
    VIDEO_CACHE["last_id"] = vid_id
    try:
        with open(LAST_VIDEO_FILE, "w") as f:
            f.write(vid_id)
    except:
        pass

def clean_title(raw):
    raw = (raw or "New Video").strip()
    if len(raw) > 80:
        raw = raw[:77] + "..."
    return html.escape(raw)

# ================= SEND FUNCTIONS =================
async def send_video_photo(bot, chat_id, video):
    title = clean_title(video.get('title'))
    new_msg = f"🔥 <b>NEW VIDEO ALERT Baby! 🔥</b>\n\n🎬 <b>{title}</b>\n\n👇 <b>Watch Now! 👇</b>"
    try:
        await bot.send_message(chat_id=chat_id, text=new_msg, parse_mode="HTML")
    except:
        pass
    caption = f"🎬 <b>{title}</b>\n\n👇 <b>Watch Now Baby! 👇</b>\n{video['link']}" + WEBSITE_TEXT
    try:
        msg = await bot.send_photo(chat_id=chat_id, photo=f"https://i.ytimg.com/vi/{video.get('id')}/hqdefault.jpg", caption=caption, parse_mode="HTML")
        return msg
    except:
        msg = await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", disable_web_page_preview=False)
        return msg

async def send_videos_with_thumbnails(message_obj, is_callback=False):
    vids = VIDEO_CACHE["videos"][:10] if VIDEO_CACHE["videos"] else get_videos_list(10)
    if not vids:
        await message_obj.reply_text(f"⏳ <b>Videos Loading Baby... Please wait 10 sec and try again! 🥰</b>\n\n🎬 <b>Watch Here:</b>\n{CHANNEL_URL}" + WEBSITE_TEXT, parse_mode="HTML", disable_web_page_preview=False)
        return
    header = "🎬 <b>Latest 10 Videos:</b> 🎬" + WEBSITE_TEXT
    await message_obj.reply_text(header, parse_mode="HTML", disable_web_page_preview=True)
    async def send_one(i, v):
        title = clean_title(v.get('title'))
        caption = f"🎬 <b>{i}. {title}</b>\n\n👇 <b>Watch Now Baby! 👇</b>\n{v['link']}" + WEBSITE_TEXT
        try:
            await message_obj.reply_photo(photo=f"https://i.ytimg.com/vi/{v.get('id')}/hqdefault.jpg", caption=caption, parse_mode="HTML")
        except:
            await message_obj.reply_text(caption, parse_mode="HTML", disable_web_page_preview=False)
    tasks = [send_one(i+1, v) for i, v in enumerate(vids)]
    await asyncio.gather(*tasks)

# ================= KEYBOARDS =================
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 All Videos", callback_data="all_videos")],
        [InlineKeyboardButton("📣 Promo", callback_data="promo"), InlineKeyboardButton("📌 Pin Latest", callback_data="pin_latest")],
        [InlineKeyboardButton("🌐 Website", url="https://pamelacullen.com"), InlineKeyboardButton("▶️ YouTube", url=CHANNEL_URL)]
    ])

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🌸 <b>Welcome Baby! Welcome to Pamela Cullen Official Bot! 🥰</b> 🌸\n\n"
        "💖 <b>I am here to give you all Pamela's Latest Videos, Updates & Love!</b> 💖\n\n"
        "🎬 <b>What can I do?</b>\n"
        "🎥 - Latest 10 Videos with Thumbnails\n"
        "🔥 - New Video Alerts Instantly!\n"
        "📌 - Auto Pin Latest Video\n"
        "📣 - Promo Every 5 Minutes\n\n"
        f"▶️ <b>Subscribe:</b> {CHANNEL_URL}"
        + WEBSITE_TEXT + "\n\n👇 <b>Choose Baby! 👇</b>"
    )
    await update.message.reply_text(welcome, parse_mode="HTML", reply_markup=get_main_keyboard())

async def all_videos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_videos_with_thumbnails(update.message)

async def latest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    v = get_latest_video()
    if v:
        await send_video_photo(context.bot, update.effective_chat.id, v)
    else:
        await update.message.reply_text("😢 <b>Video not found Baby!</b>", parse_mode="HTML")

async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    v = get_latest_video()
    if not v:
        await update.message.reply_text("😢 <b>No video to pin Baby!</b>", parse_mode="HTML")
        return
    msg = await send_video_photo(context.bot, update.effective_chat.id, v)
    try:
        await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        await update.message.reply_text("📌 <b>Pinned Baby!</b>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text("❌ <b>Pin Failed - Make me Admin with Pin Permission Baby! 🥺</b>", parse_mode="HTML")

async def new_member_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        name = html.escape(member.first_name or "Baby")
        txt = f"🌸 <b>Welcome {name} Baby! 🥰</b>\n\n💖 <b>Welcome to Pamela Cullen Family!</b> 💖\n\n🎬 <b>Latest Videos, Updates & Love - All Here!</b>\n\n👇 <b>Press All Videos Baby! 👇</b>" + WEBSITE_TEXT
        await update.message.reply_text(txt, parse_mode="HTML", reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "all_videos":
        await send_videos_with_thumbnails(query.message)
    elif data == "promo":
        v = get_latest_video()
        if v:
            title = clean_title(v.get('title'))
            txt = f"🎬 <b>{title}</b>\n\n👀 <b>Did You Watch This Video Baby? 🥺</b>\n👇 <b>Watch Now! 👇</b>\n{v['link']}" + WEBSITE_TEXT
            await query.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False)
    elif data == "pin_latest":
        v = get_latest_video()
        if v:
            msg = await send_video_photo(context.bot, query.message.chat_id, v)
            try:
                await context.bot.pin_chat_message(chat_id=query.message.chat_id, message_id=msg.message_id)
            except:
                pass

# ================= JOBS =================
async def update_video_cache_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        content = fetch_rss()
        if content:
            videos = parse_rss(content, 10)
            if videos:
                VIDEO_CACHE["videos"] = videos
                VIDEO_CACHE["time"] = time_module.time()
                print(f"Cache Updated: {len(videos)} videos")
    except Exception as e:
        print(f"Cache update failed: {e}")

async def check_new_video(context: ContextTypes.DEFAULT_TYPE):
    try:
        content = fetch_rss()
        if not content:
            return
        videos = parse_rss(content, 5)
        if not videos:
            return
        VIDEO_CACHE["videos"] = videos
        VIDEO_CACHE["time"] = time_module.time()
        latest = videos[0]
        last_id = get_last_video_id()
        if last_id is None:
            save_last_video_id(latest["id"])
            return
        if latest["id"] != last_id:
            save_last_video_id(latest["id"])
            print(f"NEW VIDEO: {latest['title']}")
            for ch in ALL_TARGET_IDS:
                try:
                    try:
                        await context.bot.unpin_all_chat_messages(chat_id=int(ch))
                    except:
                        pass
                    msg = await send_video_photo(context.bot, int(ch), latest)
                    try:
                        await context.bot.pin_chat_message(chat_id=int(ch), message_id=msg.message_id)
                        print(f"Pinned in {ch}")
                    except Exception as e:
                        print(f"PIN FAILED in {ch}: {e}")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Error sending to {ch}: {e}")
    except Exception as e:
        print(f"check_new_video error: {e}")

async def promo_message(context: ContextTypes.DEFAULT_TYPE):
    try:
        v = get_latest_video()
        if not v:
            return
        title = clean_title(v.get('title'))
        caption = f"🎬 <b>{title}</b>\n\n👀 <b>Did You Watch This Video Baby? 🥺</b>\n👇 <b>Watch Now Baby! 👇</b>\n{v['link']}" + WEBSITE_TEXT
        for ch in ALL_TARGET_IDS:
            try:
                try:
                    await context.bot.send_photo(chat_id=int(ch), photo=f"https://i.ytimg.com/vi/{v.get('id')}/hqdefault.jpg", caption=caption, parse_mode="HTML")
                except:
                    await context.bot.send_message(chat_id=int(ch), text=caption, parse_mode="HTML", disable_web_page_preview=False)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Promo failed {ch}: {e}")
    except Exception as e:
        print(f"promo error: {e}")

async def good_morning(context: ContextTypes.DEFAULT_TYPE):
    txt = "☀️ <b>Good Morning Baby! 🥰</b>\n\n💖 <b>Have a Beautiful Day!</b> 💖\n\n🎬 <b>Don't forget to watch Pamela's Latest Videos!</b>" + WEBSITE_TEXT
    for ch in ALL_TARGET_IDS:
        try:
            await context.bot.send_message(chat_id=int(ch), text=txt, parse_mode="HTML")
        except:
            pass

async def good_night(context: ContextTypes.DEFAULT_TYPE):
    txt = "🌙 <b>Good Night Baby! 😴💖</b>\n\n💖 <b>Sweet Dreams! Pamela Loves You!</b> 💖\n\n🎬 <b>Tomorrow New Video Coming!</b>" + WEBSITE_TEXT
    for ch in ALL_TARGET_IDS:
        try:
            await context.bot.send_message(chat_id=int(ch), text=txt, parse_mode="HTML")
        except:
            pass

# ================= MAIN =================
def main():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("videos", all_videos_cmd))
    app_bot.add_handler(CommandHandler("allvideos", all_videos_cmd))
    app_bot.add_handler(CommandHandler("latest", latest_cmd))
    app_bot.add_handler(CommandHandler("pin", pin_cmd))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_welcome))
    jq = app_bot.job_queue
    if jq:
        jq.run_repeating(check_new_video, interval=60, first=10)
        jq.run_repeating(promo_message, interval=300, first=30)
        jq.run_repeating(update_video_cache_job, interval=60, first=5)
        jq.run_daily(good_morning, time=time(hour=6, minute=0))
        jq.run_daily(good_night, time=time(hour=22, minute=0))
    print("Bot Started!")
    app_bot.run_polling()

if __name__ == "__main__":
    main()

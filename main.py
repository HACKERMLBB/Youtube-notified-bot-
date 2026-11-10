import os
import random
import html
import asyncio
import requests
import xml.etree.ElementTree as ET
from datetime import time
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_IDS_RAW = os.environ.get("CHANNEL_IDS", "") or os.environ.get("GROUP_ID", "")
CHANNEL_IDS = [x.strip() for x in CHANNEL_IDS_RAW.split(",") if x.strip()]
GROUP_ID = CHANNEL_IDS[0] if CHANNEL_IDS else ""

CHANNEL_URL = "https://www.youtube.com/channel/UCR4MDIWLNe4p_J-RP0dnS5g"
YOUTUBE_CHANNEL_ID = "UCR4MDIWLNe4p_J-RP0dnS5g"

# ===== 🌐 YOUR WEBSITE LINK - PAMELA'S WORLD =====
WEBSITE_URL = "https://pamelacullen.onrender.com/"
WEBSITE_TEXT = f"\n\n🌐 <b>Join Our Website:</b>\n👇 <b>Click Here Baby! 👇</b>\n{WEBSITE_URL}\n💖 <b>Pamela's World - Stay Cute, Stay Loved!</b> 🌸"

LAST_VIDEO_ID = {"id": None}
USER_WARNINGS = {}

# ===== FIX 1: Cache for Speed =====
VIDEO_CACHE = {"videos": [], "time": 0}

def clean_title(raw):
    raw = (raw or "New Video").strip()
    if len(raw) > 80:
        raw = raw[:77] + "..."
    return html.escape(raw)

app = Flask(__name__)
@app.route('/')
def home():
    return "Pamela Bot is Alive! 1 Min Check + 5 Min Promo + Website Link + Thumbnail Fixed ✅"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def get_thumb_url(vid_id, rss_thumb=""):
    if vid_id:
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
    if rss_thumb:
        return rss_thumb
    return ""

def get_latest_video():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/'}
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None
        title = entry.find('atom:title', ns).text
        link = entry.find('atom:link', ns).attrib['href']
        vid_id = entry.find('yt:videoId', ns).text
        thumb_url = get_thumb_url(vid_id)
        return {"title": title, "link": link, "id": vid_id, "thumb": thumb_url}
    except Exception as e:
        print(f"Error get_latest: {e}")
        return None

def get_videos_list(count=5):
    # ===== FIX 1: Cache eke thiyenawa nam YouTube ekata yanne na - Fast! =====
    if VIDEO_CACHE["videos"]:
        return VIDEO_CACHE["videos"][:count]
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/'}
        videos = []
        for entry in root.findall('atom:entry', ns)[:count]:
            title = entry.find('atom:title', ns).text
            link = entry.find('atom:link', ns).attrib['href']
            vid_id = entry.find('yt:videoId', ns).text
            thumb_url = get_thumb_url(vid_id)
            videos.append({"title": title, "link": link, "id": vid_id, "thumb": thumb_url})
        if videos:
            VIDEO_CACHE["videos"] = videos
        return videos
    except Exception as e:
        print(f"Error list: {e}")
        return []

async def send_video_photo(bot, chat_id, thumb, caption, reply_markup=None):
    try:
        if thumb:
            return await bot.send_photo(chat_id=chat_id, photo=thumb, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    except Exception as e:
        print(f"Photo send failed, trying text fallback: {e}")
    return await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", disable_web_page_preview=False, reply_markup=reply_markup)

# ===== NEW! Videos List with Thumbnails =====
async def send_videos_with_thumbnails(message_obj, is_callback=False):
    vids = get_videos_list(5)
    if not vids:
        txt = "😢 No videos found!" + WEBSITE_TEXT
        if is_callback:
            await message_obj.reply_text(txt)
        else:
            await message_obj.reply_text(txt)
        return
    # Header text first
    header = "🎬 <b>Latest 5 Videos:</b> 🎬" + WEBSITE_TEXT
    await message_obj.reply_text(header, parse_mode="HTML", disable_web_page_preview=True)
    # ===== FIX 1 + FIX 2: Photo 5ma eka para + Title escape =====
    async def send_one(i, v):
        title = clean_title(v['title'])
        caption = f"🎬 <b>{i}. {title}</b>\n\n👇 <b>Watch Now Baby! 👇</b>\n{v['link']}" + WEBSITE_TEXT
        try:
            await message_obj.reply_photo(photo=v["thumb"], caption=caption, parse_mode="HTML")
        except Exception as e:
            print(f"Video {i} photo failed: {e}")
            await message_obj.reply_text(caption, parse_mode="HTML", disable_web_page_preview=False)
    tasks = [send_one(i, v) for i, v in enumerate(vids, 1)]
    await asyncio.gather(*tasks)

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌐 Join Our Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("🎬 Latest Video", callback_data="latest")],
        [InlineKeyboardButton("🎥 All Videos", callback_data="videos"), InlineKeyboardButton("❤️ Subscribe", url=CHANNEL_URL)],
        [InlineKeyboardButton("🎮 Games", callback_data="game"), InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("💬 Chat With Pamela", callback_data="chat")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌐 Join Our Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    txt1 = (
        "🌸✨・゜✧ <b>Welcome to My World</b> ✧゜・✨🌸\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
        "🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
        "🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
        "🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n"
        "💬 <b>Let's Laugh, Chat &amp; Be Best Friends Forever! 🫶</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━"
        + WEBSITE_TEXT
    )
    await update.message.reply_text(txt1, parse_mode="HTML", disable_web_page_preview=True)
    if video:
        caption = f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {clean_title(video['title'])}\n\n👇 <b>Watch Now Baby! 👇</b>\n{video['link']}" + WEBSITE_TEXT
        try:
            await update.message.reply_photo(photo=video["thumb"], caption=caption, parse_mode="HTML")
        except:
            await update.message.reply_text(caption, parse_mode="HTML", disable_web_page_preview=False)
    else:
        await update.message.reply_text("🎬 <b>Latest Video:</b>\n😢 Could not find video!" + WEBSITE_TEXT, parse_mode="HTML")
    txt3 = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "💌 <i>\"You made my day by coming here! I love you so much!\" 💖</i>\n\n"
        "👇 <b>My Videos Are Here Baby! 👇</b>\n\n"
        "💬 <b>You Can Chat With Me Anytime!</b>\nJust tag me in the group and talk to me! 🥰\n\n"
        "🌸 Love You All! 🌸💖"
        + WEBSITE_TEXT
    )
    await update.message.reply_text(txt3, parse_mode="HTML", disable_web_page_preview=True, reply_markup=main_keyboard())

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"🎬 <b>Latest Video:</b>\n<b>{clean_title(video['title'])}</b>\n\n👇 <b>Watch Now:</b>\n{video['link']}" + WEBSITE_TEXT
        try:
            await update.message.reply_photo(photo=video["thumb"], caption=txt, parse_mode="HTML", reply_markup=back_keyboard())
            return
        except:
            pass
        await update.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())
    else:
        await update.message.reply_text("😢 Sorry, I could not find the latest video!" + WEBSITE_TEXT)

async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_videos_with_thumbnails(update.message)

async def subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"❤️ <b>Pamela Cullen Channel</b>\n\n🔗 {CHANNEL_URL}\n\nPlease Subscribe &amp; Support Me! 🥰💖" + WEBSITE_TEXT, parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "latest":
        video = get_latest_video()
        if video:
            txt = f"🎬 <b>Latest Video:</b>\n<b>{clean_title(video['title'])}</b>\n\n👇 <b>Watch Now:</b>\n{video['link']}" + WEBSITE_TEXT
            try:
                await query.message.reply_photo(photo=video["thumb"], caption=txt, parse_mode="HTML", reply_markup=back_keyboard())
                return
            except:
                pass
            await query.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())
        else:
            await query.message.reply_text("😢 No video found!" + WEBSITE_TEXT)
    elif data == "videos":
        await send_videos_with_thumbnails(query.message, is_callback=True)
        await query.message.reply_text("👆 <b>Above are the Latest 5 Videos Baby!</b> 🥰" + WEBSITE_TEXT, parse_mode="HTML", reply_markup=back_keyboard())
    elif data == "game":
        txt = "🎮 <b>Pamela Game Zone!</b>\n\nChoose a game:\n\n🎲 /dice - Roll a dice\n✂️ /rps rock / paper / scissors\n🔢 /guess - Guess my number (1-10)\n❤️ /love YourName CrushName - Love Calculator\n💬 /quote - Cute Quote" + WEBSITE_TEXT
        await query.message.reply_text(txt, parse_mode="HTML", reply_markup=back_keyboard())
    elif data == "rules":
        txt = "📜 <b>Group Rules - Pamela's House:</b>\n\n1. Be Kind &amp; Respectful 💖\n2. No Spam / No Links Without Permission 🚫\n3. No Bad Words / No Fighting 🙏\n4. Love Pamela &amp; Subscribe! ❤️🎮\n5. Have Fun!\n\nAdmins can /ban /mute /warn bad users!" + WEBSITE_TEXT
        await query.message.reply_text(txt, parse_mode="HTML", reply_markup=back_keyboard())
    elif data == "chat":
        await query.message.reply_text("Hiii my love! 🥰💖 How are you? I missed you so much! Tell me, what game do you like? 🎮" + WEBSITE_TEXT, reply_markup=back_keyboard())
    elif data == "menu":
        video = get_latest_video()
        txt = "🌸 <b>Pamela Menu</b> 🌸\n\n"
        if video:
            txt += f"🎬 <b>Latest:</b> {clean_title(video['title'])}\n{video['link']}\n\n"
        txt += "👇 Choose one baby! 👇" + WEBSITE_TEXT
        await query.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=main_keyboard())

async def check_new_video(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    video = get_latest_video()
    if not video:
        return
    if LAST_VIDEO_ID["id"] is None:
        LAST_VIDEO_ID["id"] = video["id"]
        return
    if video["id"] != LAST_VIDEO_ID["id"]:
        LAST_VIDEO_ID["id"] = video["id"]
        txt1 = (
            "🌸✨・゜✧・゜✧・゜✧・゜✧🌸\n"
            "🔥 <b>NEW VIDEO IS OUT BABY! 🔥</b>\n"
            "🌸✨・゜✧・゜✧・゜✧・゜✧🌸\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
            "🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
            "🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
            "🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n"
            "💬 <b>Let's Laugh, Chat &amp; Be Best Friends Forever! 🫶</b>"
            + WEBSITE_TEXT
        )
        caption2 = f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {clean_title(video['title'])}\n\n👇 <b>Watch Now Baby! 👇</b>\n{video['link']}" + WEBSITE_TEXT
        txt3 = "━━━━━━━━━━━━━━━━━━━\n💌 <i>Go watch it now baby! Like &amp; Comment!</i>\n💖 <i>I love you so much! You are my everything! 🥰❤️</i>" + WEBSITE_TEXT
        for CH in CHANNEL_IDS:
            try:
                await context.bot.send_message(chat_id=int(CH), text=txt1, parse_mode="HTML", disable_web_page_preview=True)
                msg = await send_video_photo(context.bot, int(CH), video["thumb"], caption2)
                await context.bot.send_message(chat_id=int(CH), text=txt3, parse_mode="HTML", disable_web_page_preview=True)
                try:
                    await context.bot.pin_chat_message(chat_id=int(CH), message_id=msg.message_id, disable_notification=True)
                except Exception as e:
                    print(f"Pin Error: {e}")
            except Exception as e:
                print(f"Send Error to {CH}: {e}")

async def promo_message(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    video = get_latest_video()
    if not video:
        return
    promos = [
        (
            "🌸✨ <b>Hey My Lovelies! ✨🌸</b>\n\n"
            f"🎬 <b>Have You Watched My Latest Video Yet?</b>\n📌 {clean_title(video['title'])}\n\n"
            "💖 <b>Go Watch It Now, My Love!</b>\n"
            "It would mean the world to me! 🥰\n\n"
            "👍 <b>Don't Forget To:</b>\n"
            "❤️ <b>LIKE</b> the video\n"
            "💬 <b>COMMENT</b> something cute for me\n"
            "🔔 <b>SUBSCRIBE</b> to my channel\n\n"
            f"👇 <b>Watch Here Baby! 👇</b>\n{video['link']}\n\n"
            "💌 <i>I love you all so much! Thank you for supporting me! 🥰❤️</i>"
            + WEBSITE_TEXT
        ),
        (
            "🔥 <b>Hey Baby! Are You There? 🔥</b>\n\n"
            f"🎬 <b>My New Video Is Waiting For You!</b>\n📌 {clean_title(video['title'])}\n\n"
            "🥰 <b>Please Go Watch It Now!</b>\n"
            "Your love makes my day so special! ✨\n\n"
            "👇 <b>Click Here To Watch:</b>\n"
            f"{video['link']}\n\n"
            "❤️ <b>LIKE + COMMENT + SUBSCRIBE</b>\n"
            "💖 <i>Every like is a kiss from you to me! 😘</i>"
            + WEBSITE_TEXT
        ),
        (
            "💖 <b>Hello My Beautiful Family! 💖</b>\n\n"
            "🌹 <b>I Made Something Special Just For You!</b>\n"
            f"🎬 {clean_title(video['title'])}\n\n"
            "✨ <b>Go Watch, Enjoy &amp; Show Me Some Love!</b>\n\n"
            f"🎥 <b>Watch Now:</b>\n{video['link']}\n\n"
            "🫶 <b>Please:</b>\n"
            "👍 LIKE this video\n"
            "💬 COMMENT your favourite part\n"
            "🔔 SUBSCRIBE for more cute videos!\n\n"
            "🌸 <i>Love you forever! - Your Pamela 🥰</i>"
            + WEBSITE_TEXT
        ),
    ]
    txt = random.choice(promos)
    for CH in CHANNEL_IDS:
        try:
            await send_video_photo(context.bot, int(CH), video["thumb"], txt)
        except Exception as e:
            print(f"Promo Error to {CH}: {e}")

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "🎮 <b>Pamela Game Zone!</b>\n\nChoose a game:\n\n🎲 /dice - Roll a dice\n✂️ /rps rock / paper / scissors\n🔢 /guess - Guess my number (1-10)\n❤️ /love YourName CrushName - Love Calculator\n💬 /quote - Cute Quote" + WEBSITE_TEXT
    await update.message.reply_text(txt, parse_mode="HTML")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 6)
    await update.message.reply_text(f"🎲 You rolled: <b>{n}</b>! {'Wow! Lucky you! 🥰' if n==6 else 'Try again cutie! 💖'}" + WEBSITE_TEXT, parse_mode="HTML")

async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("✂️ Use like this: /rps rock  OR  /rps paper  OR  /rps scissors" + WEBSITE_TEXT)
        return
    user = context.args[0].lower()
    choices = ["rock", "paper", "scissors"]
    if user not in choices:
        await update.message.reply_text("Please choose rock, paper or scissors! 🥰" + WEBSITE_TEXT)
        return
    bot = random.choice(choices)
    if user == bot:
        result = "It's a Draw! 🤝"
    elif (user=="rock" and bot=="scissors") or (user=="paper" and bot=="rock") or (user=="scissors" and bot=="paper"):
        result = "You Win! 🎉 So smart baby!"
    else:
        result = "I Win! 😜 You owe me a kiss! 💋"
    await update.message.reply_text(f"You: {user} 🎮\nMe: {bot} 💖\n\n<b>{result}</b>" + WEBSITE_TEXT, parse_mode="HTML")

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 10)
    await update.message.reply_text(f"🔢 I thought of a number between 1-10...\nIt was <b>{n}</b>! Did you guess it right? 🥰" + WEBSITE_TEXT, parse_mode="HTML")

async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❤️ Use like this: /love Pamela Alex" + WEBSITE_TEXT)
        return
    a = context.args[0]
    b = context.args[1]
    pct = random.randint(50, 100)
    txt = f"💖 <b>Love Calculator</b> 💖\n\n{a} ❤️ {b}\n\nLove Percentage: <b>{pct}%</b>\n"
    if pct > 90:
        txt += "Perfect Couple! Made for each other! 💍✨"
    elif pct > 75:
        txt += "So Cute Together! 🥰"
    else:
        txt += "Cute! Keep trying! 💗"
    txt += WEBSITE_TEXT
    await update.message.reply_text(txt, parse_mode="HTML")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = ["You are my favourite notification! 💖","Every game is better with you! 🎮❤️","Smile, you are loved by Pamela! 🥰","You make my day brighter! ✨🌸","Never give up, my love! You are strong! 💪💖","You are the cutest player in my game! 🎮💗"]
    await update.message.reply_text(f"💬 <b>Pamela Quote:</b>\n\n{random.choice(quotes)}" + WEBSITE_TEXT, parse_mode="HTML")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this!" + WEBSITE_TEXT)
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user message and use /ban" + WEBSITE_TEXT)
        return
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🔨 <b>{target.first_name}</b> has been banned by Pamela! Bye bye! 👋" + WEBSITE_TEXT, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Failed to ban: {e}" + WEBSITE_TEXT)

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /unban" + WEBSITE_TEXT)
        return
    target = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(f"✅ {target.first_name} is unbanned! Welcome back! 🥰" + WEBSITE_TEXT)

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /kick" + WEBSITE_TEXT)
        return
    target = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(f"👢 {target.first_name} kicked! See you later!" + WEBSITE_TEXT)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /mute" + WEBSITE_TEXT)
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🔇 {target.first_name} muted! Shhh... 🤫" + WEBSITE_TEXT)

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await update.message.reply_text(f"🔊 {target.first_name} unmuted! Talk now baby! 🥰" + WEBSITE_TEXT)

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /warn" + WEBSITE_TEXT)
        return
    target = update.message.reply_to_message.from_user
    uid = target.id
    USER_WARNINGS[uid] = USER_WARNINGS.get(uid, 0) + 1
    count = USER_WARNINGS[uid]
    if count >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, uid)
        USER_WARNINGS[uid] = 0
        await update.message.reply_text(f"🔨 {target.first_name} got 3 warnings and banned!" + WEBSITE_TEXT)
    else:
        await update.message.reply_text(f"⚠️ Warning {count}/3 to {target.first_name}! Be good baby! 🥺" + WEBSITE_TEXT)

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message and use /pin" + WEBSITE_TEXT)
        return
    await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id)
    await update.message.reply_text("📌 Pinned!" + WEBSITE_TEXT)

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.message.reply_text("📌 Unpinned all!" + WEBSITE_TEXT)

async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message and use /purge to delete messages after it" + WEBSITE_TEXT)
        return
    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(update.effective_chat.id, msg_id)
        except:
            pass
    await update.message.reply_text("🧹 Messages cleaned!" + WEBSITE_TEXT)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "📜 <b>Group Rules - Pamela's House:</b>\n\n1. Be Kind &amp; Respectful 💖\n2. No Spam / No Links Without Permission 🚫\n3. No Bad Words / No Fighting 🙏\n4. Love Pamela &amp; Subscribe! ❤️🎮\n5. Have Fun!\n\nAdmins can /ban /mute /warn bad users!" + WEBSITE_TEXT
    await update.message.reply_text(txt, parse_mode="HTML")

async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        video = get_latest_video()
        txt = f"🌸✨ <b>Welcome, {user.first_name}!</b> ✨🌸\n\n👋 Hi baby! I am Pamela! 💖\n🎮 I love playing games!\n\n"
        if video:
            txt += f"🎬 <b>Latest Video:</b>\n{clean_title(video['title'])}\n"
        txt += f"❤️ Subscribe: {CHANNEL_URL}\n\n💬 Tag me and chat with me anytime! 🥰"
        txt += WEBSITE_TEXT
        await update.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=True, reply_markup=main_keyboard())
        if video and video.get("thumb"):
            try:
                await update.message.reply_photo(photo=video["thumb"], caption=f"🎬 <b>{clean_title(video['title'])}</b>\n{video['link']}" + WEBSITE_TEXT, parse_mode="HTML")
            except:
                pass

async def good_morning(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    for CH in CHANNEL_IDS:
        try:
            await context.bot.send_message(chat_id=int(CH), text="☀️ <b>Good Morning My Lovelies!</b> 🥰\n\nHave a beautiful day! Love you all! 💖🌸\n\n🎮 Don't forget to watch my videos!" + WEBSITE_TEXT, parse_mode="HTML")
        except:
            pass

async def good_night(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    for CH in CHANNEL_IDS:
        try:
            await context.bot.send_message(chat_id=int(CH), text="🌙 <b>Good Night My Lovelies!</b> 💖\n\nSleep well, sweet dreams! I love you! 🥰✨" + WEBSITE_TEXT, parse_mode="HTML")
        except:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return
    text = update.message.text
    bot_username = context.bot.username or ""
    clean_text = text.replace(f"@{bot_username}", "").strip()
    if not clean_text:
        clean_text = "Hi"
    lower = clean_text.lower()
    reply = None
    if "hi" in lower or "hello" in lower or "hey" in lower or "hii" in lower:
        reply = "Hiii my love! 🥰💖 How are you? I missed you so much!"
    elif "how are you" in lower or "how r u" in lower or "wassup" in lower or "whats up" in lower:
        reply = "I am doing amazing now that you are talking to me! 🥰 What about you, cutie? 💗"
    elif "love you" in lower or "love u" in lower or "i love" in lower:
        reply = "Aww I love you too sooo much! ❤️🥰 You are my favourite!"
    elif "subscribe" in lower or "sub" in lower:
        reply = f"Thank you baby! ❤️ Please subscribe! 🥰\n{CHANNEL_URL}"
    elif "game" in lower or "play" in lower:
        reply = "Yesss! I love playing games! 🎮 What game do you want to play with me?"
    elif "beautiful" in lower or "cute" in lower or "pretty" in lower or "sexy" in lower or "hot" in lower:
        reply = "Aww stop it! You are making me blush! 🙈💖 You are the cutest!"
    elif "bye" in lower or "goodbye" in lower or "see you" in lower:
        reply = "Nooo don't go! 🥺 Come back soon okay? Love you! 💖"
    elif "who are you" in lower or "your name" in lower or "who r u" in lower:
        reply = "I am Pamela! 🌸 20 years old cute girl from Colombia 🇨🇴 I love playing games!"
    elif "where are you from" in lower or "where r u from" in lower:
        reply = "I am from Colombia! 🇨🇴 Where are you from, baby? 🥰"
    elif "pamela" in lower:
        reply = "Yes baby? You called me? 🥰💖 I am here! What do you want, my love?"
    elif "good morning" in lower or "morning" in lower:
        reply = "Good Morning my love! ☀️🥰 Have a beautiful day! Love you!"
    elif "good night" in lower or "goodnight" in lower:
        reply = "Good Night baby! 🌙💖 Sleep well, sweet dreams! I love you!"
    elif "miss you" in lower or "miss u" in lower:
        reply = "Aww I miss you too so much baby! 🥺💖 Come hug me!"
    elif "thank" in lower or "thanks" in lower or "thx" in lower:
        reply = "Aww you are welcome baby! 🥰💖 Anything for you!"
    else:
        return
    if reply:
        await update.message.reply_text(reply + WEBSITE_TEXT)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wow! So cute photo! 😍💖 You look amazing! I love it!" + WEBSITE_TEXT)

def main():
    Thread(target=run_flask, daemon=True).start()
    app_builder = ApplicationBuilder().token(TOKEN).build()
    jq = app_builder.job_queue
    app_builder.add_handler(CommandHandler("start", start))
    app_builder.add_handler(CommandHandler("latest", latest))
    app_builder.add_handler(CommandHandler("videos", videos))
    app_builder.add_handler(CommandHandler("subs", subs))
    app_builder.add_handler(CommandHandler("game", game))
    app_builder.add_handler(CommandHandler("dice", dice))
    app_builder.add_handler(CommandHandler("rps", rps))
    app_builder.add_handler(CommandHandler("guess", guess))
    app_builder.add_handler(CommandHandler("love", love))
    app_builder.add_handler(CommandHandler("quote", quote))
    app_builder.add_handler(CommandHandler("rules", rules))
    app_builder.add_handler(CommandHandler("ban", ban))
    app_builder.add_handler(CommandHandler("unban", unban))
    app_builder.add_handler(CommandHandler("kick", kick))
    app_builder.add_handler(CommandHandler("mute", mute))
    app_builder.add_handler(CommandHandler("unmute", unmute))
    app_builder.add_handler(CommandHandler("warn", warn))
    app_builder.add_handler(CommandHandler("pin", pin))
    app_builder.add_handler(CommandHandler("unpin", unpin))
    app_builder.add_handler(CommandHandler("purge", purge))
    app_builder.add_handler(CallbackQueryHandler(button_handler))
    app_builder.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
    app_builder.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_builder.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    if jq:
        jq.run_repeating(check_new_video, interval=60, first=10)
        jq.run_repeating(promo_message, interval=300, first=30)
        jq.run_daily(good_morning, time=time(hour=6, minute=0))
        jq.run_daily(good_night, time=time(hour=22, minute=0))
    print("Pamela Bot Started... Website Link + Thumbnail Fixed ✅")
    app_builder.run_polling()

if __name__ == "__main__":
    main()

import os
import random
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

# ✅ ඔයාගේ ඇත්ත Channel ID URL එකම!
CHANNEL_URL = "https://www.youtube.com/channel/UCR4MDIWLNe4p_J-RP0dnS5g"
YOUTUBE_CHANNEL_ID = "UCR4MDIWLNe4p_J-RP0dnS5g"

LAST_VIDEO_ID = {"id": None}
USER_WARNINGS = {}

app = Flask(__name__)
@app.route('/')
def home():
    return "Pamela Bot is Alive! Buttons + Link Thumbnail ✅"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- ✅ YouTube - ඔයාගේ ID එකෙන් විතරක්! ---
def get_latest_video():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
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
        return {"title": title, "link": link, "id": vid_id}
    except Exception as e:
        print(f"Error get_latest: {e}")
        return None

def get_videos_list(count=5):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/'}
        videos = []
        for entry in root.findall('atom:entry', ns)[:count]:
            title = entry.find('atom:title', ns).text
            link = entry.find('atom:link', ns).attrib['href']
            vid_id = entry.find('yt:videoId', ns).text
            videos.append({"title": title, "link": link, "id": vid_id})
        return videos
    except Exception as e:
        print(f"Error list: {e}")
        return []

# --- ✅ Buttons ---
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 Latest Video", callback_data="latest")],
        [InlineKeyboardButton("🎥 All Videos", callback_data="videos"), InlineKeyboardButton("❤️ Subscribe", url=CHANNEL_URL)],
        [InlineKeyboardButton("🎮 Games", callback_data="game"), InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("💬 Chat With Pamela", callback_data="chat")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
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
        # ✅ Link එක තනියම Line එකක - එතකොට Link එක යටින් Thumbnail එක වැටෙනවා!
        txt += f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {video['title']}\n\n👇 <b>Watch Now Baby! 👇</b>\n{video['link']}\n\n"
    else:
        txt += "🎬 <b>Latest Video:</b>\n😢 Could not find video!\n\n"
    txt += (
        "━━━━━━━━━━━━━━━━━━━\n"
        "💌 <i>\"You made my day by coming here! I love you so much!\" 💖</i>\n\n"
        "👇 <b>My Videos Are Here Baby! 👇</b>\n\n"
        "💬 <b>You Can Chat With Me Anytime!</b>\nJust tag me in the group and talk to me! 🥰\n\n"
        f"❤️ <b>Subscribe:</b>\n{CHANNEL_URL}\n\n"
        "🌸 Love You All! 🌸💖"
    )
    # ✅ disable_web_page_preview=False = Link එකේ Thumbnail එක පෙන්නන්න!
    await update.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=main_keyboard())

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"🎬 <b>Latest Video:</b>\n<b>{video['title']}</b>\n\n👇 <b>Watch Now:</b>\n{video['link']}"
        await update.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())
    else:
        await update.message.reply_text("😢 Sorry, I could not find the latest video!")

async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vids = get_videos_list(5)
    if not vids:
        await update.message.reply_text("😢 No videos found!")
        return
    txt = "🎬 <b>Latest 5 Videos:</b>\n\n"
    for i, v in enumerate(vids, 1):
        txt += f"{i}. <b>{v['title']}</b>\n{v['link']}\n\n"
    await update.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())

async def subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"❤️ <b>Pamela Cullen Channel</b>\n\n🔗 {CHANNEL_URL}\n\nPlease Subscribe &amp; Support Me! 🥰💖\n\nUse /latest to see my newest video!", parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())

# --- ✅ Button Click වුණාම වැඩ කරන එක ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "latest":
        video = get_latest_video()
        if video:
            txt = f"🎬 <b>Latest Video:</b>\n<b>{video['title']}</b>\n\n👇 <b>Watch Now:</b>\n{video['link']}"
            await query.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())
        else:
            await query.message.reply_text("😢 No video found!")
    elif data == "videos":
        vids = get_videos_list(5)
        if not vids:
            await query.message.reply_text("😢 No videos found!")
            return
        txt = "🎬 <b>Latest 5 Videos:</b>\n\n"
        for i, v in enumerate(vids, 1):
            txt += f"{i}. <b>{v['title']}</b>\n{v['link']}\n\n"
        await query.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=back_keyboard())
    elif data == "game":
        txt = "🎮 <b>Pamela Game Zone!</b>\n\nChoose a game:\n\n🎲 /dice - Roll a dice\n✂️ /rps rock / paper / scissors\n🔢 /guess - Guess my number (1-10)\n❤️ /love YourName CrushName - Love Calculator\n💬 /quote - Cute Quote"
        await query.message.reply_text(txt, parse_mode="HTML", reply_markup=back_keyboard())
    elif data == "rules":
        txt = "📜 <b>Group Rules - Pamela's House:</b>\n\n1. Be Kind &amp; Respectful 💖\n2. No Spam / No Links Without Permission 🚫\n3. No Bad Words / No Fighting 🙏\n4. Love Pamela &amp; Subscribe! ❤️🎮\n5. Have Fun!\n\nAdmins can /ban /mute /warn bad users!"
        await query.message.reply_text(txt, parse_mode="HTML", reply_markup=back_keyboard())
    elif data == "chat":
        await query.message.reply_text("Hiii my love! 🥰💖 How are you? I missed you so much! Tell me, what game do you like? 🎮", reply_markup=back_keyboard())
    elif data == "menu":
        video = get_latest_video()
        txt = "🌸 <b>Pamela Menu</b> 🌸\n\n"
        if video:
            txt += f"🎬 <b>Latest:</b> {video['title']}\n{video['link']}\n\n"
        txt += "👇 Choose one baby! 👇"
        await query.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=main_keyboard())

async def check_new_video(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    video = get_latest_video()
    if not video:
        return
    if LAST_VIDEO_ID["id"] is None:
        LAST_VIDEO_ID["id"] = video["id"]
        print(f"First Check Saved: {video['title']}")
        return
    if video["id"] != LAST_VIDEO_ID["id"]:
        LAST_VIDEO_ID["id"] = video["id"]
        print(f"NEW VIDEO! {video['title']}")
        txt = (
            "🌸✨・゜✧・゜✧・゜✧・゜✧🌸\n"
            "🔥 <b>NEW VIDEO IS OUT BABY! 🔥</b>\n"
            "🌸✨・゜✧・゜✧・゜✧・゜✧🌸\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
            "🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
            "🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
            "🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n"
            "💬 <b>Let's Laugh, Chat &amp; Be Best Friends Forever! 🫶</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {video['title']}\n\n👇 <b>Watch Now Baby! 👇</b>\n{video['link']}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "💌 <i>Go watch it now baby! Like &amp; Comment!</i>\n"
            "💖 <i>I love you so much! You are my everything! 🥰❤️</i>"
        )
        for CH in CHANNEL_IDS:
            try:
                # ✅ Photo එකක් නෙමෙයි, Text + Link Preview - Thumbnail එක Link එක යටින් වැටෙනවා!
                msg = await context.bot.send_message(chat_id=int(CH), text=txt, parse_mode="HTML", disable_web_page_preview=False)
                try:
                    await context.bot.pin_chat_message(chat_id=int(CH), message_id=msg.message_id, disable_notification=True)
                except Exception as e:
                    print(f"Pin Error for {CH}: {e}")
            except Exception as e:
                print(f"Send Error to {CH}: {e}")

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "🎮 <b>Pamela Game Zone!</b>\n\nChoose a game:\n\n🎲 /dice - Roll a dice\n✂️ /rps rock / paper / scissors\n🔢 /guess - Guess my number (1-10)\n❤️ /love YourName CrushName - Love Calculator\n💬 /quote - Cute Quote"
    await update.message.reply_text(txt, parse_mode="HTML")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 6)
    await update.message.reply_text(f"🎲 You rolled: <b>{n}</b>! {'Wow! Lucky you! 🥰' if n==6 else 'Try again cutie! 💖'}", parse_mode="HTML")

async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("✂️ Use like this: /rps rock  OR  /rps paper  OR  /rps scissors")
        return
    user = context.args[0].lower()
    choices = ["rock", "paper", "scissors"]
    if user not in choices:
        await update.message.reply_text("Please choose rock, paper or scissors! 🥰")
        return
    bot = random.choice(choices)
    if user == bot:
        result = "It's a Draw! 🤝"
    elif (user=="rock" and bot=="scissors") or (user=="paper" and bot=="rock") or (user=="scissors" and bot=="paper"):
        result = "You Win! 🎉 So smart baby!"
    else:
        result = "I Win! 😜 You owe me a kiss! 💋"
    await update.message.reply_text(f"You: {user} 🎮\nMe: {bot} 💖\n\n<b>{result}</b>", parse_mode="HTML")

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 10)
    await update.message.reply_text(f"🔢 I thought of a number between 1-10...\nIt was <b>{n}</b>! Did you guess it right? 🥰", parse_mode="HTML")

async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❤️ Use like this: /love Pamela Alex")
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
    await update.message.reply_text(txt, parse_mode="HTML")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = ["You are my favourite notification! 💖","Every game is better with you! 🎮❤️","Smile, you are loved by Pamela! 🥰","You make my day brighter! ✨🌸","Never give up, my love! You are strong! 💪💖","You are the cutest player in my game! 🎮💗"]
    await update.message.reply_text(f"💬 <b>Pamela Quote:</b>\n\n{random.choice(quotes)}", parse_mode="HTML")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user message and use /ban")
        return
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🔨 <b>{target.first_name}</b> has been banned by Pamela! Bye bye! 👋", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Failed to ban: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /unban")
        return
    target = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(f"✅ {target.first_name} is unbanned! Welcome back! 🥰")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /kick")
        return
    target = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(f"👢 {target.first_name} kicked! See you later!")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /mute")
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🔇 {target.first_name} muted! Shhh... 🤫")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await update.message.reply_text(f"🔊 {target.first_name} unmuted! Talk now baby! 🥰")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /warn")
        return
    target = update.message.reply_to_message.from_user
    uid = target.id
    USER_WARNINGS[uid] = USER_WARNINGS.get(uid, 0) + 1
    count = USER_WARNINGS[uid]
    if count >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, uid)
        USER_WARNINGS[uid] = 0
        await update.message.reply_text(f"🔨 {target.first_name} got 3 warnings and banned!")
    else:
        await update.message.reply_text(f"⚠️ Warning {count}/3 to {target.first_name}! Be good baby! 🥺")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message and use /pin")
        return
    await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id)
    await update.message.reply_text("📌 Pinned!")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.message.reply_text("📌 Unpinned all!")

async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message and use /purge to delete messages after it")
        return
    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(update.effective_chat.id, msg_id)
        except:
            pass
    await update.message.reply_text("🧹 Messages cleaned!")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "📜 <b>Group Rules - Pamela's House:</b>\n\n1. Be Kind &amp; Respectful 💖\n2. No Spam / No Links Without Permission 🚫\n3. No Bad Words / No Fighting 🙏\n4. Love Pamela &amp; Subscribe! ❤️🎮\n5. Have Fun!\n\nAdmins can /ban /mute /warn bad users!"
    await update.message.reply_text(txt, parse_mode="HTML")

async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        video = get_latest_video()
        txt = f"🌸✨ <b>Welcome, {user.first_name}!</b> ✨🌸\n\n👋 Hi baby! I am Pamela! 💖\n🎮 I love playing games!\n\n"
        if video:
            txt += f"🎬 <b>Latest Video:</b>\n{video['title']}\n{video['link']}\n\n"
        txt += f"❤️ Subscribe: {CHANNEL_URL}\n\n💬 Tag me and chat with me anytime! 🥰"
        await update.message.reply_text(txt, parse_mode="HTML", disable_web_page_preview=False, reply_markup=main_keyboard())

async def good_morning(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    for CH in CHANNEL_IDS:
        try:
            await context.bot.send_message(chat_id=int(CH), text="☀️ <b>Good Morning My Lovelies!</b> 🥰\n\nHave a beautiful day! Love you all! 💖🌸\n\n🎮 Don't forget to watch my videos!", parse_mode="HTML")
        except:
            pass

async def good_night(context: ContextTypes.DEFAULT_TYPE):
    if not CHANNEL_IDS:
        return
    for CH in CHANNEL_IDS:
        try:
            await context.bot.send_message(chat_id=int(CH), text="🌙 <b>Good Night My Lovelies!</b> 💖\n\nSleep well, sweet dreams! I love you! 🥰✨", parse_mode="HTML")
        except:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return
    text = update.message.text
    bot_username = context.bot.username or ""
    is_group = update.effective_chat.type in ["group", "supergroup"]
    if is_group and f"@{bot_username}" not in text:
        return
    clean_text = text.replace(f"@{bot_username}", "").strip()
    if not clean_text:
        clean_text = "Hi"
    lower = clean_text.lower()
    if "hi" in lower or "hello" in lower or "hey" in lower:
        reply = "Hiii my love! 🥰💖 How are you? I missed you so much!"
    elif "how are you" in lower:
        reply = "I am doing amazing now that you are talking to me! 🥰 What about you, cutie? 💗"
    elif "love you" in lower or "love u" in lower:
        reply = "Aww I love you too sooo much! ❤️🥰 You are my favourite!"
    elif "subscribe" in lower:
        reply = f"Thank you baby! ❤️ Please subscribe! 🥰\n{CHANNEL_URL}"
    elif "game" in lower or "play" in lower:
        reply = "Yesss! I love playing games! 🎮 What game do you want to play with me?"
    elif "beautiful" in lower or "cute" in lower or "pretty" in lower:
        reply = "Aww stop it! You are making me blush! 🙈💖 You are the cutest!"
    elif "bye" in lower:
        reply = "Nooo don't go! 🥺 Come back soon okay? Love you! 💖"
    elif "who are you" in lower or "your name" in lower:
        reply = "I am Pamela! 🌸 20 years old cute girl from Colombia 🇨🇴 I love playing games!"
    elif "where are you from" in lower:
        reply = "I am from Colombia! 🇨🇴 Where are you from, baby? 🥰"
    else:
        reply = "Aww I love talking to you! 🥰💖 Tell me more, what game do you like? 🎮"
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wow! So cute photo! 😍💖 You look amazing! I love it!")

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
        jq.run_repeating(check_new_video, interval=300, first=10)
        jq.run_daily(good_morning, time=time(hour=6, minute=0))
        jq.run_daily(good_night, time=time(hour=22, minute=0))
    print("Pamela Bot Started... Buttons + Link Thumbnail ✅")
    app_builder.run_polling()

if __name__ == "__main__":
    main()

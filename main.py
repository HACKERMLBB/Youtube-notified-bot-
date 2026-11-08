import os
import random
import requests
import asyncio
import xml.etree.ElementTree as ET
from datetime import time
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode

# --- Config - Your Env Names ---
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = os.environ.get("CHANNEL_IDS", "")
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")
CHANNEL_NAME = os.environ.get("YOUTUBE_CHANNEL_NAME", "Pamela Cullen")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
CHANNEL_URL = "https://youtube.com/@pamela_cullen?si=NAgcuWJptFGxc9I6"

LAST_VIDEO_ID = {"id": None}
USER_WARNINGS = {}

# --- Flask Keep Alive ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Pamela Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- YouTube Helper ---
def get_latest_video():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None
        title = entry.find('atom:title', ns).text
        link = entry.find('atom:link', ns).attrib['href']
        vid_id = entry.find('yt:videoId', ns).text
        author = entry.find('atom:author/atom:name', ns).text
        return {"title": title, "link": link, "id": vid_id, "author": author}
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_videos_list(count=5):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        videos = []
        for entry in root.findall('atom:entry', ns)[:count]:
            title = entry.find('atom:title', ns).text
            link = entry.find('atom:link', ns).attrib['href']
            videos.append({"title": title, "link": link})
        return videos
    except:
        return []

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"🌸✨ <b>Hello, My Lovelies!</b> ✨🌸\n\n"
        txt += f"👋 <b>Hi, My Name Is Pamela!</b> 💖\n\n"
        txt += f"🇨🇴 I Am From Colombia\n🎂 I Am 20 Years Old\n🎮 I Love Playing Games\n💗 And I Love You All So Much!\n\n"
        txt += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        txt += f"🎬 <b>Latest Video:</b>\n<b>{video['title']}</b>\n\n👇 <b>Watch Now:</b>\n{video['link']}\n\n"
        txt += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        txt += f"💬 <b>You Can Chat With Me Anytime!</b>\nJust tag me in the group and talk to me! 🥰\n\n"
        txt += f"❤️ <b>Subscribe:</b>\n{CHANNEL_URL}\n\n🌸 Love You All! 🌸💖"
    else:
        txt = f"🌸✨ <b>Hello, My Lovelies!</b> ✨🌸\n\n👋 <b>Hi, My Name Is Pamela!</b> 💖\n\n🇨🇴 I Am From Colombia\n🎂 I Am 20 Years Old\n🎮 I Love Playing Games\n💗 And I Love You All So Much!\n\n💬 Chat With Me Anytime! 🥰\n\n❤️ Subscribe: {CHANNEL_URL}\n\n🌸 Love You All! 🌸💖"
    await update.message.reply_text(txt, parse_mode="HTML")

# --- YouTube Commands ---
async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        await update.message.reply_text(f"🎬 <b>Latest Video:</b>\n<b>{video['title']}</b>\n\n{video['link']}", parse_mode="HTML")
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
    await update.message.reply_text(txt, parse_mode="HTML")

async def subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"❤️ <b>{CHANNEL_NAME} Channel</b>\n\n🔗 {CHANNEL_URL}\n\nPlease Subscribe & Support Me! 🥰💖\n\nUse /latest to see my newest video!", parse_mode="HTML")

# --- Auto Post New Video + Pin ---
async def check_new_video(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_ID:
        return
    video = get_latest_video()
    if not video:
        return
    if LAST_VIDEO_ID["id"] is None:
        LAST_VIDEO_ID["id"] = video["id"]
        return
    if video["id"] != LAST_VIDEO_ID["id"]:
        LAST_VIDEO_ID["id"] = video["id"]
        txt = f"🔥🔥 <b>NEW VIDEO OUT NOW!</b> 🔥🔥\n\n🎬 <b>{video['title']}</b>\n\n👇 <b>Watch Now:</b>\n{video['link']}\n\n❤️ Like, Comment & Subscribe! 🥰\n{CHANNEL_URL}"
        try:
            msg = await context.bot.send_message(chat_id=int(GROUP_ID), text=txt, parse_mode="HTML")
            await context.bot.pin_chat_message(chat_id=int(GROUP_ID), message_id=msg.message_id, disable_notification=True)
        except Exception as e:
            print(f"Pin Error: {e}")

# --- Games & Fun ---
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
    quotes = [
        "You are my favourite notification! 💖",
        "Every game is better with you! 🎮❤️",
        "Smile, you are loved by Pamela! 🥰",
        "You make my day brighter! ✨🌸",
        "Never give up, my love! You are strong! 💪💖",
        "You are the cutest player in my game! 🎮💗"
    ]
    await update.message.reply_text(f"💬 <b>Pamela Quote:</b>\n\n{random.choice(quotes)}", parse_mode="HTML")

# --- Group Management Like Rose Bot ---
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
    txt = "📜 <b>Group Rules - Pamela's House:</b>\n\n1. Be Kind & Respectful 💖\n2. No Spam / No Links Without Permission 🚫\n3. No Bad Words / No Fighting 🙏\n4. Love Pamela & Subscribe! ❤️🎮\n5. Have Fun!\n\nAdmins can /ban /mute /warn bad users!"
    await update.message.reply_text(txt, parse_mode="HTML")

# --- Welcome New Members ---
async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        txt = f"🌸✨ <b>Welcome, {user.first_name}!</b> ✨🌸\n\n👋 Hi baby! I am Pamela! 💖\n🎮 I love playing games!\n\n❤️ Subscribe: {CHANNEL_URL}\n\n💬 Tag me and chat with me anytime! 🥰"
        await update.message.reply_text(txt, parse_mode="HTML")

# --- Good Morning / Good Night Auto ---
async def good_morning(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_ID:
        return
    try:
        await context.bot.send_message(chat_id=int(GROUP_ID), text="☀️ <b>Good Morning My Lovelies!</b> 🥰\n\nHave a beautiful day! Love you all! 💖🌸\n\n🎮 Don't forget to watch my videos!", parse_mode="HTML")
    except:
        pass

async def good_night(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_ID:
        return
    try:
        await context.bot.send_message(chat_id=int(GROUP_ID), text="🌙 <b>Good Night My Lovelies!</b> 💖\n\nSleep well, sweet dreams! I love you! 🥰✨", parse_mode="HTML")
    except:
        pass

# --- Chat AI Reply ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return
    text = update.message.text
    bot_username = BOT_USERNAME or context.bot.username or ""
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
        reply = f"Aww I love talking to you! 🥰💖 Tell me more, what game do you like? 🎮"
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wow! So cute photo! 😍💖 You look amazing! I love it!")

# --- Main - FIXED for Python 3.14 ---
async def main_async():
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
    app_builder.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
    app_builder.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_builder.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    if jq:
        jq.run_repeating(check_new_video, interval=300, first=10)
        jq.run_daily(good_morning, time=time(hour=6, minute=0))
        jq.run_daily(good_night, time=time(hour=22, minute=0))
    print("Pamela Bot Started...")
    await app_builder.initialize()
    await app_builder.start()
    await app_builder.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_async())

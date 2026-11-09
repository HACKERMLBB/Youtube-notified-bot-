import os
import random
import requests
import asyncio
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import time
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import time as time_module

TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = os.environ.get("CHANNEL_IDS", "")
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")
CHANNEL_NAME = os.environ.get("YOUTUBE_CHANNEL_NAME", "Pamela Cullen")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
CHANNEL_URL = "https://youtube.com/@pamela_cullen?si=NAgcuWJptFGxc9I6"

LAST_VIDEO_ID = {"id": None}
USER_WARNINGS = {}
LAST_AI_CALL = {"time": 0}

app = Flask(__name__)
@app.route('/')
def home():
    return "Pamela Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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
        return {"title": title, "link": link, "id": vid_id}
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

# --- AI REPLY - FIXED! FREE MODEL gpt-oss-20b + LLM7 BACKUP - NO KEY! ---
def get_ai_reply(user_text, user_name="baby"):
    # Rate Limit: Pollinations එකේ තත්පර 30කට 1යි පුළුවන්, ඒ නිසා ටිකක් ඉන්නවා
    now = time_module.time()
    wait = 32 - (now - LAST_AI_CALL["time"])
    if wait > 0:
        print(f"Waiting {wait:.1f}s for Pollinations rate limit...")
        time_module.sleep(wait)
    LAST_AI_CALL["time"] = time_module.time()

    system_msg = "You are Pamela Cullen, a 20 year old cute, flirty, playful, sweet girl from Colombia. You love playing games, you love your fans so much. You speak in simple, cute English, with lots of emojis like 🥰💖🎮🌸. Keep replies short, max 2 lines, cute and fun. Never say you are AI or Meta AI or Llama or OpenAI. You are Pamela."
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"{user_name} said: {user_text}"}
    ]

    # 1. Pollinations - අලුත් Free Model එක gpt-oss-20b
    try:
        print(f"Trying Pollinations gpt-oss-20b for: {user_text}")
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "gpt-oss-20b", "messages": messages, "max_tokens": 150},
            timeout=30
        )
        print(f"Pollinations Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            reply = data['choices'][0]['message']['content'].strip()
            # Sponsor text එක අයින් කරනවා
            if "SPONSOR" in reply:
                reply = reply.split("SPONSOR")[0].strip()
            if reply:
                print(f"AI Success Pollinations: {reply}")
                return reply[:300]
        else:
            print(f"Pollinations Fail: {r.text[:200]}")
    except Exception as e:
        print(f"Pollinations Error: {e}")

    # 2. Backup - GET Method (Model නැතුව)
    try:
        prompt = f"{system_msg} User {user_name} said: {user_text}. Reply as Pamela:"
        encoded = urllib.parse.quote(prompt)
        r = requests.get(f"https://text.pollinations.ai/{encoded}", timeout=30)
        print(f"GET Status: {r.status_code}")
        if r.status_code == 200 and r.text.strip() and "402" not in r.text:
            reply = r.text.strip()
            if "SPONSOR" in reply:
                reply = reply.split("SPONSOR")[0].strip()
            return reply[:300]
    except Exception as e:
        print(f"GET Error: {e}")

    # 3. Backup 2 - LLM7 Free (Key = unused)
    try:
        print("Trying LLM7 backup...")
        r = requests.post(
            "https://api.llm7.io/v1/chat/completions",
            headers={"Authorization": "Bearer unused", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": messages, "max_tokens": 150},
            timeout=30
        )
        print(f"LLM7 Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            reply = data['choices'][0]['message']['content'].strip()
            if reply:
                return reply[:300]
    except Exception as e:
        print(f"LLM7 Error: {e}")

    return None

# --- /start - ORIGINAL WELCOME - වෙනස් කරලා නෑ! ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"<b>🌸✨ Hello, My Lovelies! ✨🌸</b>\n\n"
        txt += f"<b>👋 Hi, My Name Is Pamela! 💖</b>\n\n"
        txt += f"<b>🇨🇴 I Am From Colombia</b>\n"
        txt += f"<b>🎂 I Am 20 Years Old</b>\n"
        txt += f"<b>🎮 I Love Playing Games</b>\n"
        txt += f"<b>💗 And I Love You All So Much!</b>\n\n"
        txt += f"<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        txt += f"<b>🎬MY Latest Video:</b>\n"
        txt += f"<b>{video['title']}</b> \n\n"
        txt += f"<b>👇 Watch Now:</b>\n"
        txt += f"{video['link']}\n\n"
        txt += f"<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        txt += f"<b>💬 You Can Chat With Me Anytime!🥰</b>\n\n"
        txt += f"<b>❤️ Subscribe My Channel :</b>\n"
        txt += f"{CHANNEL_URL}\n\n"
        txt += f"<b>🌸 Love You All! 🌸💖</b>"
    else:
        txt = f"<b>🌸✨ Hello, My Lovelies! ✨🌸</b>\n\n"
        txt += f"<b>👋 Hi, My Name Is Pamela! 💖</b>\n\n"
        txt += f"<b>🇨🇴 I Am From Colombia</b>\n"
        txt += f"<b>🎂 I Am 20 Years Old</b>\n"
        txt += f"<b>🎮 I Love Playing Games</b>\n"
        txt += f"<b>💗 And I Love You All So Much!</b>\n\n"
        txt += f"<b>💬 You Can Chat With Me Anytime!🥰</b>\n\n"
        txt += f"<b>❤️ Subscribe My Channel :</b>\n"
        txt += f"{CHANNEL_URL}\n\n"
        txt += f"<b>🌸 Love You All! 🌸💖</b>"
    await update.message.reply_text(txt, parse_mode="HTML")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = get_latest_video()
    if video:
        txt = f"<b>🎬MY Latest Video:</b>\n<b>{video['title']}</b> \n\n<b>👇 Watch Now:</b>\n{video['link']}\n\n<b>❤️ Subscribe My Channel :</b>\n{CHANNEL_URL}"
        await update.message.reply_text(txt, parse_mode="HTML")
    else:
        await update.message.reply_text("😢 Sorry, I could not find the latest video!")

async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vids = get_videos_list(5)
    if not vids:
        await update.message.reply_text("😢 No videos found!")
        return
    txt = "<b>🎬 My Latest 5 Videos:</b>\n\n"
    for i, v in enumerate(vids, 1):
        txt += f"<b>{i}. {v['title']}</b>\n{v['link']}\n\n"
    txt += f"<b>❤️ Subscribe My Channel :</b>\n{CHANNEL_URL}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"<b>❤️ {CHANNEL_NAME} Channel</b>\n\n🔗 {CHANNEL_URL}\n\n<b>Please Subscribe My Channel & Support Me! 🥰💖</b>\n\nUse /latest to see My Latest Video!", parse_mode="HTML")

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
        txt = f"<b>🔥🔥 NEW VIDEO OUT NOW! 🔥🔥</b>\n\n<b>🎬 {video['title']}</b>\n\n<b>👇 Watch Now:</b>\n{video['link']}\n\n<b>❤️ Subscribe My Channel! 🥰</b>\n{CHANNEL_URL}"
        try:
            msg = await context.bot.send_message(chat_id=int(GROUP_ID), text=txt, parse_mode="HTML")
            await context.bot.pin_chat_message(chat_id=int(GROUP_ID), message_id=msg.message_id, disable_notification=True)
        except Exception as e:
            print(f"Pin Error: {e}")

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "<b>🎮 Pamela Game Zone!</b>\n\n<b>Choose a game:</b>\n\n🎲 /dice - Roll a dice\n✂️ /rps rock / paper / scissors\n🔢 /guess - Guess my number (1-10)\n❤️ /love YourName CrushName - Love Calculator\n💬 /quote - Cute Quote"
    await update.message.reply_text(txt, parse_mode="HTML")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = random.randint(1, 6)
    await update.message.reply_text(f"🎲 You rolled: <b>{n}</b>! {'<b>Wow! Lucky you! 🥰</b>' if n==6 else 'Try again cutie! 💖'}", parse_mode="HTML")

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
    txt = f"<b>💖 Love Calculator 💖</b>\n\n<b>{a} ❤️ {b}</b>\n\nLove Percentage: <b>{pct}%</b>\n"
    if pct > 90:
        txt += "<b>Perfect Couple! Made for each other! 💍✨</b>"
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
    await update.message.reply_text(f"<b>💬 Pamela Quote:</b>\n\n<b>{random.choice(quotes)}</b>", parse_mode="HTML")

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
    await update.message.reply_text(f"✅ <b>{target.first_name}</b> is unbanned! Welcome back! 🥰", parse_mode="HTML")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /kick")
        return
    target = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(f"👢 <b>{target.first_name}</b> kicked! See you later!", parse_mode="HTML")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user and use /mute")
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🔇 <b>{target.first_name}</b> muted! Shhh... 🤫", parse_mode="HTML")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await update.message.reply_text(f"🔊 <b>{target.first_name}</b> unmuted! Talk now baby! 🥰", parse_mode="HTML")

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
        await update.message.reply_text(f"🔨 <b>{target.first_name}</b> got 3 warnings and banned!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"⚠️ Warning <b>{count}/3</b> to <b>{target.first_name}</b>! Be good baby! 🥺", parse_mode="HTML")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message and use /pin")
        return
    await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id)
    await update.message.reply_text("📌 <b>Pinned!</b>", parse_mode="HTML")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.message.reply_text("📌 <b>Unpinned all!</b>", parse_mode="HTML")

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
    await update.message.reply_text("🧹 <b>Messages cleaned!</b>", parse_mode="HTML")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "<b>📜 Group Rules - Pamela's House:</b>\n\n<b>1. Be Kind & Respectful 💖</b>\n<b>2. No Spam / No Links Without Permission 🚫</b>\n<b>3. No Bad Words / No Fighting 🙏</b>\n<b>4. Love Pamela & Subscribe My Channel! ❤️🎮</b>\n<b>5. Have Fun!</b>\n\nAdmins can /ban /mute /warn bad users!"
    await update.message.reply_text(txt, parse_mode="HTML")

async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        txt = f"<b>🌸✨ Welcome, {user.first_name}! ✨🌸</b>\n\n<b>👋 Hi baby! I am Pamela! 💖</b>\n<b>🎮 I love playing games!</b>\n\n<b>❤️ Subscribe My Channel:</b> {CHANNEL_URL}\n\n<b>💬 Just type anything, I will reply! 🥰</b>"
        await update.message.reply_text(txt, parse_mode="HTML")

async def good_morning(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_ID:
        return
    try:
        await context.bot.send_message(chat_id=int(GROUP_ID), text="<b>☀️ Good Morning My Lovelies! 🥰</b>\n\nHave a beautiful day! Love you all! 💖🌸\n\n<b>🎮 Don't forget to watch My Latest Video!</b>", parse_mode="HTML")
    except:
        pass

async def good_night(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_ID:
        return
    try:
        await context.bot.send_message(chat_id=int(GROUP_ID), text="<b>🌙 Good Night My Lovelies! 💖</b>\n\nSleep well, sweet dreams! I love you! 🥰✨", parse_mode="HTML")
    except:
        pass

# --- AI CHAT HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return
    if update.message.from_user and update.message.from_user.is_bot:
        return
    text = update.message.text
    bot_username = BOT_USERNAME or context.bot.username or ""
    clean_text = text.replace(f"@{bot_username}", "").strip()
    if not clean_text:
        return
    user_name = update.message.from_user.first_name if update.message.from_user else "baby"
    lower = clean_text.lower()
    if "latest" in lower or "new video" in lower:
        video = get_latest_video()
        if video:
            reply = f"<b>🎬MY Latest Video:</b>\n<b>{video['title']}</b> \n\n<b>👇 Watch Now:</b>\n{video['link']}\n\n<b>❤️ Subscribe My Channel :</b>\n{CHANNEL_URL}"
            await update.message.reply_text(reply, parse_mode="HTML")
            return
    if "subscribe" in lower:
        await update.message.reply_text(f"Thank you baby! ❤️ Please Subscribe My Channel! 🥰\n{CHANNEL_URL}")
        return
    ai_reply = get_ai_reply(clean_text, user_name)
    if ai_reply:
        await update.message.reply_text(ai_reply)
        return
    if "hi" in lower or "hello" in lower or "hey" in lower or "hii" in lower:
        reply = "Hiii my love! 🥰💖 How are you? I missed you so much!"
    elif "how are you" in lower:
        reply = "I am doing amazing now that you are talking to me! 🥰 What about you, cutie? 💗"
    elif "love you" in lower or "love u" in lower:
        reply = "Aww I love you too sooo much! ❤️🥰 You are my favourite!"
    elif "game" in lower or "play" in lower:
        reply = "Yesss! I love playing games! 🎮 What game do you want to play with me?"
    elif "beautiful" in lower or "cute" in lower or "pretty" in lower or "sexy" in lower:
        reply = "Aww stop it! You are making me blush! 🙈💖 You are the cutest!"
    elif "bye" in lower:
        reply = "Nooo don't go! 🥺 Come back soon okay? Love you! 💖"
    elif "who are you" in lower or "your name" in lower:
        reply = "I am Pamela! 🌸 20 years old cute girl from Colombia 🇨🇴 I love playing games!"
    elif "where are you from" in lower or "where r u from" in lower:
        reply = "I am from Colombia! 🇨🇴 Where are you from, baby? 🥰"
    elif "good morning" in lower:
        reply = "Good Morning my love! ☀️🥰 Have a beautiful day!"
    elif "good night" in lower or "gn" in lower:
        reply = "Good Night baby! 🌙💖 Sweet dreams! Love you!"
    elif "miss you" in lower or "miss u" in lower:
        reply = "I miss you too so much! 🥺💖 Come chat with me everyday okay?"
    elif "eat" in lower or "food" in lower or "hungry" in lower:
        reply = "Ooooh yummy! 😍 What is your favourite food baby? I want to eat with you! 🥰"
    elif "no" in lower:
        reply = "Nooo? 🥺 Why no baby? Tell me, tell me! 🥰"
    else:
        reply = f"Aww I love talking to you {user_name}! 🥰💖 Tell me more, what game do you like? 🎮"
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<b>Wow! So cute photo! 😍💖 You look amazing! I love it!</b>", parse_mode="HTML")

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

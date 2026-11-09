import os, time, requests, threading
import xml.etree.ElementTree as ET
from flask import Flask
from datetime import datetime

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_IDS_RAW = os.environ.get("CHANNEL_IDS", "")
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")
YOUTUBE_CHANNEL_NAME = os.environ.get("YOUTUBE_CHANNEL_NAME", "My Channel")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

CHANNELS = [c.strip() for c in CHANNEL_IDS_RAW.split(",") if c.strip()]

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot is Alive! ✅ | Channels: {CHANNELS} | YT: {YOUTUBE_CHANNEL_NAME} | Bot: @{BOT_USERNAME}"

def send_message(chat_id, text, reply_markup=None):
    try:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload, timeout=20)
        print(f"Sent to {chat_id} | Status: {r.status_code}")
        return r.json()
    except Exception as e:
        print(f"Send Error: {e}")
        return None

def send_to_all_channels(text, reply_markup=None):
    for ch in CHANNELS:
        send_message(ch, text, reply_markup=reply_markup)

def get_all_videos():
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        r = requests.get(url, timeout=20)
        root = ET.fromstring(r.content)
        videos = []
        for entry in root.findall('entry'):
            title = entry.find('title').text
            link = entry.find('link').attrib['href']
            published = entry.find('published').text
            videos.append({"title": title, "link": link, "published": published})
        return videos
    except Exception as e:
        print(f"Get Videos Error: {e}")
        return []

def get_latest_video():
    videos = get_all_videos()
    if videos:
        return videos[0]["title"], videos[0]["link"]
    return None, None

def send_latest(chat_id):
    title, link = get_latest_video()
    if title and link:
        msg_text = f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n━━━━━━━━━━━━━━━━━━━\n\n📌 {title}\n\n💌 <i>Go watch it now baby! 🥰</i>"
        buttons = {"inline_keyboard": [[{"text": "▶️ Watch Now 💖", "url": link}]]}
        send_message(chat_id, msg_text, reply_markup=buttons)
    else:
        send_message(chat_id, "No videos found! 😢")

def send_old(chat_id):
    videos = get_all_videos()
    if videos:
        old = videos[-1]
        msg_text = f"📼 <b>My Old Video 🌸</b>\n━━━━━━━━━━━━━━━━━━━\n\n📌 {old['title']}\n\n💌 <i>This is where it all started! 🥰</i>"
        buttons = {"inline_keyboard": [[{"text": "▶️ Watch Old Video", "url": old['link']}]]}
        send_message(chat_id, msg_text, reply_markup=buttons)
    else:
        send_message(chat_id, "No videos found! 😢")

def send_months(chat_id):
    videos = get_all_videos()
    now = datetime.now()
    month_videos = []
    for v in videos:
        try:
            pub = datetime.fromisoformat(v["published"].replace("Z", "+00:00"))
            if pub.year == now.year and pub.month == now.month:
                month_videos.append(v)
        except:
            pass
    if month_videos:
        msg_text = "📅 <b>This Month's Videos 📆</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
        for i, v in enumerate(month_videos, 1):
            msg_text += f"{i}. {v['title']}\n{v['link']}\n\n"
        msg_text += "💌 <i>Which one is your favorite? 🥰</i>"
        send_message(chat_id, msg_text)
    else:
        send_message(chat_id, "No videos this month yet! 😢\nNew video coming soon! 💖")

def send_welcome(chat_id):
    latest_title, latest_link = get_latest_video()
    subscribe_link = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}?sub_confirmation=1"
    welcome_text = (
        "🌸✨・゜✧ <b>Welcome to My World</b> ✧゜・✨🌸\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
        "🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
        "🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
        "🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n"
        "💬 <b>Let's Laugh, Chat &amp; Be Best Friends Forever! 🫶</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )
    if latest_title and latest_link:
        welcome_text += f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {latest_title}\n\n"
    welcome_text += (
        "━━━━━━━━━━━━━━━━━━━\n"
        "💌 <i>\"You made my day by coming here! I love you so much!\" 💖</i>\n\n"
        "👇 <b>My Videos Are Here Baby! 👇</b>"
    )
    buttons = {
        "inline_keyboard": [
            [{"text": "▶️ Latest Video 💖", "callback_data": "latest"}, {"text": "📼 Old Video 🌸", "callback_data": "old"}],
            [{"text": "📅 This Month Videos 📆", "callback_data": "months"}],
            [{"text": "▶️ Watch Latest on YouTube 🔥", "url": latest_link}] if latest_link else [],
            [{"text": "🔴 Subscribe Me Baby ❤️", "url": subscribe_link}]
        ]
    }
    buttons["inline_keyboard"] = [row for row in buttons["inline_keyboard"] if row]
    send_message(chat_id, welcome_text, reply_markup=buttons)

last_id = None

def handle_start():
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(url, params=params, timeout=35)
            data = r.json()
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        chat_id = cb["message"]["chat"]["id"]
                        cb_data = cb.get("data", "")
                        try:
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={"callback_query_id": cb["id"]}, timeout=10)
                        except:
                            pass
                        if cb_data == "latest":
                            send_latest(chat_id)
                        elif cb_data == "old":
                            send_old(chat_id)
                        elif cb_data == "months":
                            send_months(chat_id)
                        continue
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id")
                    if not chat_id:
                        continue
                    if text == "/start":
                        send_welcome(chat_id)
                    elif text == "/latest":
                        send_latest(chat_id)
                    elif text == "/old":
                        send_old(chat_id)
                    elif text == "/months":
                        send_months(chat_id)
        except Exception as e:
            print(f"Start Handler Error: {e}")
            time.sleep(5)

def check_loop():
    global last_id
    print(f"Bot Started! Channels={CHANNELS} YT={YOUTUBE_CHANNEL_NAME}")
    send_to_all_channels(f"✅ Bot Started! 🔥\n\n📺 Channel: {YOUTUBE_CHANNEL_NAME}\n🤖 Bot: @{BOT_USERNAME}\n\nNew videos will be posted here automatically! 💖")
    while True:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
            r = requests.get(url, timeout=20)
            root = ET.fromstring(r.content)
            entry = root.find('entry')
            if entry is None:
                time.sleep(60)
                continue
            vid = entry.find('{http://www.youtube.com/xml/schemas/2015}videoId').text
            title = entry.find('title').text
            link = entry.find('link').attrib['href']
            if last_id is None:
                last_id = vid
                print(f"First video saved: {title}")
            elif vid != last_id:
                last_id = vid
                subscribe_link = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}?sub_confirmation=1"
                # ✅ ඔයා දුන්න Message එකම!
                msg = (
                    "🌸✨ <b>NEW VIDEO IS OUT BABY! 🔥✨</b> 🌸\n"
                    "━━━━━━━━━━━━━━━━━━━\n\n"
                    "💖 <b>Hi Baby! I'm Pamela 🥰</b>\n"
                    "🌹 <b>Your Cutest Live Streamer from Colombia 🇨🇴</b>\n"
                    "🎂 <b>20 Years Old | Sweet, Cute &amp; Full of Love 💕</b>\n"
                    "🔴 <b>I Go LIVE Every Day! Come Talk With Me!</b>\n\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"🎬 <b>My Latest Video Just Dropped! 🔥</b>\n📌 {title}\n\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "💌 <i>Go watch it now baby! Like &amp; Comment! I love you so much! 🥰❤️</i>"
                )
                buttons = {
                    "inline_keyboard": [
                        [{"text": "▶️ Watch Now 💖", "url": link}],
                        [{"text": "🔴 Subscribe Me Baby ❤️", "url": subscribe_link}]
                    ]
                }
                send_to_all_channels(msg, reply_markup=buttons)
            else:
                print("No new video...")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=check_loop, daemon=True).start()
    threading.Thread(target=handle_start, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

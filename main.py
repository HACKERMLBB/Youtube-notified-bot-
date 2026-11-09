import os, time, requests, threading
import xml.etree.ElementTree as ET
from flask import Flask

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

def send_message(chat_id, text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=20
        )
        print(f"Sent to {chat_id} | Status: {r.status_code} | {r.text[:300]}")
        return r.json()
    except Exception as e:
        print(f"Send Error to {chat_id}: {e}")
        return None

def send_to_all_channels(text):
    for ch in CHANNELS:
        send_message(ch, text)

last_id = None

# ✅ /start වලට Reply කරන Function එක!
def handle_start():
    offset = None
    print("Start handler started - listening for /start...")
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
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id")
                    if text == "/start":
                        send_message(chat_id, f"👋 Hi! මං {YOUTUBE_CHANNEL_NAME} Channel එකේ Bot! 🔥\n\nඅලුත් Video එකක් ආව ගමන් මං Channel එකට දාන්නම්!\n\n🤖 @{BOT_USERNAME}")
                        print(f"Replied to /start from {chat_id}")
        except Exception as e:
            print(f"Start Handler Error: {e}")
            time.sleep(5)

def check_loop():
    global last_id
    print(f"Bot Started! Channels={CHANNELS} YT={YOUTUBE_CHANNEL_NAME}")
    send_to_all_channels(f"✅ Bot Started! 🔥\n\n📺 Channel: {YOUTUBE_CHANNEL_NAME}\n🤖 Bot: @{BOT_USERNAME}\n\nඅලුත් Video එකක් ආව ගමන් මං මෙතනට දාන්නම්! 💖")
    while True:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
            r = requests.get(url, timeout=20)
            root = ET.fromstring(r.content)
            entry = root.find('entry')
            if entry is None:
                time.sleep(600)
                continue
            vid = entry.find('{http://www.youtube.com/xml/schemas/2015}videoId').text
            title = entry.find('title').text
            link = entry.find('link').attrib['href']
            if last_id is None:
                last_id = vid
                print(f"First video saved: {title}")
            elif vid != last_id:
                last_id = vid
                msg = f"🔥 NEW VIDEO! 🔥\n\n📺 {YOUTUBE_CHANNEL_NAME}\n📌 {title}\n\n▶️ Watch Now:\n{link}\n\n🤖 @{BOT_USERNAME}"
                send_to_all_channels(msg)
                print(f"New video sent: {title}")
            else:
                print("No new video...")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=check_loop, daemon=True).start()
    threading.Thread(target=handle_start, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

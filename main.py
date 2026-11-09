import os, time, requests, threading
import xml.etree.ElementTree as ET
from flask import Flask

# ✅ ඔයාගේ නම් වලටම ගැලපෙන විදියට!
TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_IDS_RAW = os.environ.get("CHANNEL_IDS", "") # -100xxxxxxxxxx, -100yyyyyyyyyy වගේ කීපයක් දාන්නත් පුලුවන්!
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")
YOUTUBE_CHANNEL_NAME = os.environ.get("YOUTUBE_CHANNEL_NAME", "My Channel")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

# CHANNEL_IDS එකේ කොමා වලින් වෙන් කරලා තියෙන Channel ටික ලිස්ට් එකක් කරනවා
CHANNELS = [c.strip() for c in CHANNEL_IDS_RAW.split(",") if c.strip()]

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot is Alive! ✅ | Channels: {CHANNELS} | YT: {YOUTUBE_CHANNEL_NAME} ({YOUTUBE_CHANNEL_ID}) | Bot: @{BOT_USERNAME}"

def send_to_all_channels(text):
    for ch in CHANNELS:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": ch, "text": text},
                timeout=20
            )
            print(f"Sent to {ch} | Status: {r.status_code} | {r.text[:200]}")
        except Exception as e:
            print(f"Send Error to {ch}: {e}")

last_id = None

def check_loop():
    global last_id
    print(f"Bot Started! Channels={CHANNELS} YT={YOUTUBE_CHANNEL_NAME}")

    # ✅ Welcome Message එක!
    send_to_all_channels(
        f"✅ Bot Started! 🔥\n\n"
        f"📺 Channel: {YOUTUBE_CHANNEL_NAME}\n"
        f"🤖 Bot: @{BOT_USERNAME}\n\n"
        f"අලුත් Video එකක් ආව ගමන් මං මෙතනට දාන්නම්! 💖"
    )

    while True:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
            r = requests.get(url, timeout=20)
            root = ET.fromstring(r.content)
            entry = root.find('entry')
            if entry is None:
                print("No video found yet...")
                time.sleep(600)
                continue

            vid = entry.find('{http://www.youtube.com/xml/schemas/2015}videoId').text
            title = entry.find('title').text
            link = entry.find('link').attrib['href']

            if last_id is None:
                last_id = vid
                print(f"First video saved: {title} - will NOT send old video")
            elif vid != last_id:
                last_id = vid
                msg = (
                    f"🔥 NEW VIDEO! 🔥\n\n"
                    f"📺 {YOUTUBE_CHANNEL_NAME}\n"
                    f"📌 {title}\n\n"
                    f"▶️ Watch Now:\n{link}\n\n"
                    f"🤖 @{BOT_USERNAME}"
                )
                send_to_all_channels(msg)
                print(f"New video sent: {title}")
            else:
                print("No new video...")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(600) # විනාඩි 10න් 10ට Check කරනවා

if __name__ == "__main__":
    threading.Thread(target=check_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

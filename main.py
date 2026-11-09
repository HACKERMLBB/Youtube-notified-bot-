import os, time, requests, threading
import xml.etree.ElementTree as ET
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL")
YT_ID = os.environ.get("YOUTUBE_CHANNEL_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Alive! ✅"

last_id = None

def check_loop():
    global last_id
    print("Bot Started, checking YouTube...")
    while True:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_ID}"
            r = requests.get(url, timeout=20)
            root = ET.fromstring(r.content)
            entry = root.find('entry')
            if entry is None:
                print("No video found yet")
                time.sleep(600)
                continue

            vid = entry.find('{http://www.youtube.com/xml/schemas/2015}videoId').text
            title = entry.find('title').text
            link = entry.find('link').attrib['href']

            if last_id is None:
                last_id = vid
                print(f"First video: {title}")
            elif vid != last_id:
                last_id = vid
                msg = f"🔥 NEW VIDEO! 🔥\n\n📌 {title}\n\n▶️ Watch Now:\n{link}"
                res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHANNEL, "text": msg})
                print(f"Sent! Status: {res.status_code} - {title}")
            else:
                print("No new video...")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=check_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

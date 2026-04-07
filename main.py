import time
import os
import json
import threading
import base64
from flask import Flask, render_template_string, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

# --- ফাইল সেটিংস ---
DB_FILE = "wa_database.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f: json.dump({"hello": "Hi! I am Adil's Bot."}, f)

driver = None
qr_code_base64 = ""

def get_driver():
    global driver
    if driver is None:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # WhatsApp Web-এর জন্য এই ইউজার এজেন্ট জরুরি
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- Admin UI ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Bot Link</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; background: #e5ddd5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 15px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .qr-box { background: #eee; padding: 10px; margin: 20px 0; min-height: 250px; }
        img { width: 100%; border: 1px solid #ddd; }
        .btn { background: #25d366; color: white; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold; }
        .input-box { width: 100%; padding: 10px; margin: 5px 0; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #075e54;">🟢 WhatsApp Link Device</h2>
        <div class="qr-box">
            {% if qr %}
                <img src="data:image/png;base64,{{ qr }}">
                <p>ফোনের WhatsApp থেকে QR স্ক্যান করুন</p>
            {% else %}
                <p><br><br>বট চালু করতে 'Get QR Code' দিন</p>
            {% endif %}
        </div>
        <form action="/get_qr" method="POST">
            <button class="btn">Get QR Code / Refresh</button>
        </form>
        <hr>
        <h4>🤖 Train Bot</h4>
        <form action="/train" method="POST">
            <input type="text" name="q" class="input-box" placeholder="User Message" required>
            <input type="text" name="a" class="input-box" placeholder="Bot Reply" required>
            <button type="submit" class="btn" style="background: #34b7f1;">Save Logic</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def admin():
    global qr_code_base64
    return render_template_string(HTML_TEMPLATE, qr=qr_code_base64)

@app.route('/get_qr', methods=['POST'])
def get_qr():
    global qr_code_base64
    d = get_driver()
    if "web.whatsapp.com" not in d.current_url:
        d.get("https://web.whatsapp.com")
    
    time.sleep(10) # QR লোড হওয়ার সময়
    try:
        # QR কোড এরিয়া খুঁজে স্ক্রিনশট নেওয়া
        element = d.find_element(By.XPATH, "//canvas[@aria-label='Scan me!']").find_element(By.XPATH, "./..")
        qr_code_base64 = element.screenshot_as_base64
    except:
        qr_code_base64 = "" # অলরেডি লগইন থাকলে কিউআর আসবে না
    
    return "<script>window.location.href='/';</script>"

@app.route('/train', methods=['POST'])
def train():
    q = request.form.get('q').lower().strip()
    a = request.form.get('a').strip()
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        data[q] = a
        f.seek(0)
        json.dump(data, f, indent=4)
    return "Saved! <a href='/'>Back</a>"

# --- অটো রিপ্লাই লুপ ---
def whatsapp_loop():
    global driver
    while True:
        try:
            if driver:
                # আনরেড মেসেজ চেক করা
                unread_chats = driver.find_elements(By.XPATH, "//span[@aria-label='Unread']")
                for chat in unread_chats:
                    chat.click()
                    time.sleep(2)
                    
                    # শেষ মেসেজ পড়া
                    msgs = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]")
                    if msgs:
                        last_msg = msgs[-1].text.split('\n')[0].lower().strip()
                        
                        # ডাটাবেস থেকে রিপ্লাই খোঁজা
                        with open(DB_FILE, 'r') as f:
                            replies = json.load(f)
                        
                        if last_msg in replies:
                            input_box = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @data-tab='10']")
                            input_box.send_keys(replies[last_msg])
                            input_box.send_keys(Keys.ENTER)
                            print(f"Replied to: {last_msg}")
            time.sleep(10)
        except:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=whatsapp_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

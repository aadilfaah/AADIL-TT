import time
import os
import json
import threading
import base64
from flask import Flask, request, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

# --- গ্লোবাল ভেরিয়েবল ---
DB_FILE = "database.json"
driver = None
current_screenshot = ""

def get_driver():
    global driver
    if driver is None:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- এডমিন প্যানেল UI ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ADIL Remote Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; background: #f0f2f5; padding: 20px; }
        .screen-box { background: #000; padding: 10px; border-radius: 10px; margin: 20px auto; max-width: 400px; }
        img { width: 100%; border-radius: 5px; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .login-btn { background: #ff0050; color: white; }
        .refresh-btn { background: #00f2ea; color: #000; }
        .input-box { width: 80%; padding: 10px; margin: 10px; }
    </style>
</head>
<body>
    <h2>📱 TikTok Remote Control</h2>
    
    <div class="screen-box">
        {% if img %}
            <img src="data:image/png;base64,{{ img }}">
        {% else %}
            <p style="color: white;">Click 'Start Login' to see screen</p>
        {% endif %}
    </div>

    <form action="/action" method="POST">
        <button name="cmd" value="start" class="btn login-btn">Start Login Page</button>
        <button name="cmd" value="refresh" class="btn refresh-btn">Refresh Screen</button>
        <br><br>
        <input type="text" name="text_input" class="input-box" placeholder="Type here (ID/Pass)">
        <br>
        <button name="cmd" value="type" class="btn">Type Text</button>
        <button name="cmd" value="enter" class="btn" style="background:#222; color:white;">Press Enter</button>
    </form>

    <hr>
    <h3>🤖 Bot Training</h3>
    <form action="/add_reply" method="POST">
        <input type="text" name="q" placeholder="User Message" required><br>
        <input type="text" name="a" placeholder="Bot Reply" required><br>
        <button type="submit" class="btn" style="background:#28a745; color:white;">Save Reply</button>
    </form>
</body>
</html>
'''

@app.route('/admin')
def admin():
    global current_screenshot
    return render_template_string(HTML_TEMPLATE, img=current_screenshot)

@app.route('/action', methods=['POST'])
def action():
    global driver, current_screenshot
    cmd = request.form.get('cmd')
    text = request.form.get('text_input')
    d = get_driver()

    if cmd == "start":
        d.get("https://www.tiktok.com/login")
    elif cmd == "refresh":
        pass # শুধু স্ক্রিনশট আপডেট হবে
    elif cmd == "type" and text:
        try:
            d.switch_to.active_element.send_keys(text)
        except: pass
    elif cmd == "enter":
        try:
            d.switch_to.active_element.send_keys(Keys.ENTER)
        except: pass

    time.sleep(2)
    current_screenshot = d.get_screenshot_as_base64()
    return "<script>window.location.href='/admin';</script>"

@app.route('/add_reply', methods=['POST'])
def add_reply():
    q = request.form.get('q').lower().strip()
    a = request.form.get('a').strip()
    db = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: db = json.load(f)
    db[q] = a
    with open(DB_FILE, 'w') as f: json.dump(db, f, indent=4)
    return "Saved! <a href='/admin'>Back</a>"

# বটের রিপ্লাই লজিক (ব্যাকগ্রাউন্ডে চলবে)
def auto_reply_loop():
    global driver
    while True:
        try:
            if driver and "messages" in driver.current_url:
                with open(DB_FILE, 'r') as f: replies = json.load(f)
                chats = driver.find_elements(By.XPATH, "//div[contains(@class, 'DivThreadItem')]")
                for chat in chats[:2]:
                    chat.click()
                    time.sleep(2)
                    msg_elements = driver.find_elements(By.XPATH, "//div[@data-e2e='message-text']")
                    if msg_elements:
                        incoming = msg_elements[-1].text.lower().strip()
                        if incoming in replies:
                            box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                            box.send_keys(replies[incoming])
                            box.send_keys(Keys.ENTER)
            time.sleep(30)
        except:
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=auto_reply_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

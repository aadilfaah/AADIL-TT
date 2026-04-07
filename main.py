import time
import os
import json
import threading
from flask import Flask, request, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

# --- ডাটা ফাইল ম্যানেজমেন্ট ---
CONFIG_FILE = "config.json"
DB_FILE = "database.json"
STATUS = {"user": "Not Logged In", "status": "Idle"}

def load_json(file, default):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- এডমিন প্যানেল UI (আইফোন ও অ্যান্ড্রয়েড ফ্রেন্ডলি) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ADIL Bot Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; padding: 15px; color: #333; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status-box { background: #e3f2fd; border-left: 6px solid #2196f3; padding: 15px; border-radius: 8px; }
        input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
        button { background: #ff0050; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px; }
        h2 { margin-top: 0; font-size: 18px; color: #111; }
        .user-tag { color: #ff0050; font-weight: bold; border: 1px solid #ff0050; padding: 2px 8px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="status-box card">
        <h2>📊 Live Status</h2>
        <p>Current User: <span class="user-tag">{{ status.user }}</span></p>
        <p>Activity: <strong>{{ status.status }}</strong></p>
    </div>

    <div class="card">
        <h2>🔑 Update Session ID</h2>
        <form method="POST" action="/update_session">
            <input type="text" name="session_id" placeholder="Paste Session ID here..." required>
            <button type="submit">Update & Restart Bot</button>
        </form>
    </div>

    <div class="card">
        <h2>🤖 Train Bot</h2>
        <form method="POST" action="/add_reply">
            <input type="text" name="question" placeholder="User says (e.g. hello)" required>
            <textarea name="answer" placeholder="Bot replies (e.g. Hi there!)" rows="2" required></textarea>
            <button type="submit" style="background: #28a745;">Save to Database</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return f"<h1>ADIL Bot is Online!</h1><p>User: {STATUS['user']}</p><a href='/admin'>Go to Admin Panel</a>"

@app.route('/admin')
def admin():
    return render_template_string(HTML_TEMPLATE, status=STATUS)

@app.route('/update_session', methods=['POST'])
def update_session():
    new_id = request.form.get('session_id').strip()
    save_json(CONFIG_FILE, {"session_id": new_id})
    return "✅ Session Updated! Restarting... <a href='/admin'>Go Back</a>"

@app.route('/add_reply', methods=['POST'])
def add_reply():
    q = request.form.get('question').lower().strip()
    a = request.form.get('answer').strip()
    db = load_json(DB_FILE, {})
    db[q] = a
    save_json(DB_FILE, db)
    return "✅ Bot Trained! <a href='/admin'>Go Back</a>"

def run_bot():
    global STATUS
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    while True:
        config = load_json(CONFIG_FILE, {"session_id": ""})
        if not config["session_id"]:
            STATUS["status"] = "Waiting for Session ID..."
            time.sleep(10)
            continue

        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://www.tiktok.com")
            time.sleep(5)
            
            driver.add_cookie({'name': 'sessionid', 'value': config["session_id"], 'domain': '.tiktok.com'})
            driver.refresh()
            time.sleep(10)

            # ইউজারনেম ডিটেকশন
            try:
                driver.get("https://www.tiktok.com/profile")
                time.sleep(5)
                user = driver.find_element(By.XPATH, "//h1[@data-e2e='user-title'] | //h2[@data-e2e='user-title']").text
                STATUS["user"] = user
            except:
                STATUS["user"] = "Logged In (Hidden)"

            while True:
                STATUS["status"] = "Monitoring Messages..."
                driver.get("https://www.tiktok.com/messages")
                time.sleep(15)
                
                replies = load_json(DB_FILE, {})
                chats = driver.find_elements(By.XPATH, "//div[contains(@class, 'DivThreadItem')]")
                
                for chat in chats[:3]:
                    try:
                        chat.click()
                        time.sleep(3)
                        msgs = driver.find_elements(By.XPATH, "//div[@data-e2e='message-text']")
                        if msgs:
                            text = msgs[-1].text.lower().strip()
                            if text in replies:
                                box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                                box.send_keys(replies[text])
                                box.send_keys(Keys.ENTER)
                    except: continue
                time.sleep(40)
        except Exception as e:
            STATUS["status"] = f"Error: {str(e)[:50]}"
            try: driver.quit()
            except: pass
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

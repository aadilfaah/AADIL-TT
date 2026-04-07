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

# --- ফাইল পাথ ---
CONFIG_FILE = "config.json"
DB_FILE = "database.json"
STATUS = {"user": "Not Logged In", "status": "Idle"}

def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- এডমিন প্যানেল UI ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ADIL TikTok Bot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status-box { background: #e7f3ff; padding: 15px; border-left: 5px solid #007bff; margin-bottom: 20px; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold; }
        h2 { color: #333; margin-top: 0; }
        .user-tag { color: #d91e18; font-weight: bold; }
    </style>
</head>
<body>
    <div class="status-box">
        <h2>📊 Bot Status</h2>
        <p>Logged in as: <span class="user-tag">{{ status.user }}</span></p>
        <p>Current Activity: <strong>{{ status.status }}</strong></p>
    </div>

    <div class="card">
        <h2>🔑 Update Session ID</h2>
        <form method="POST" action="/update_session">
            <input type="text" name="session_id" placeholder="Paste New Session ID Here" required>
            <button type="submit">Update & Restart</button>
        </form>
    </div>

    <div class="card">
        <h2>🤖 Train Bot</h2>
        <form method="POST" action="/add_reply">
            <input type="text" name="question" placeholder="User Message (e.g. hi)" required>
            <textarea name="answer" placeholder="Bot Reply" required></textarea>
            <button type="submit" style="background: #28a745;">Add to Database</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return f"<h1>Bot is Online!</h1><p>Logged in as: {STATUS['user']}</p><a href='/admin'>Go to Admin Panel</a>"

@app.route('/admin')
def admin():
    return render_template_string(HTML_TEMPLATE, status=STATUS)

@app.route('/update_session', methods=['POST'])
def update_session():
    new_id = request.form.get('session_id')
    save_data(CONFIG_FILE, {"session_id": new_id})
    return "Session ID Updated! Restarting Bot... <a href='/admin'>Back</a>"

@app.route('/add_reply', methods=['POST'])
def add_reply():
    q = request.form.get('question').lower().strip()
    a = request.form.get('answer').strip()
    db = load_data(DB_FILE, {})
    db[q] = a
    save_data(DB_FILE, db)
    return "Successfully Trained! <a href='/admin'>Back</a>"

def run_tiktok_bot():
    global STATUS
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    while True:
        config = load_data(CONFIG_FILE, {"session_id": ""})
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

            # --- ইউজারনেম খুঁজে বের করার ফিচার ---
            try:
                # প্রোফাইল আইকন বা ইউজারনেম এলিমেন্ট খোঁজা
                driver.get("https://www.tiktok.com/profile")
                time.sleep(5)
                user_element = driver.find_element(By.XPATH, "//h1[@data-e2e='user-title'] | //h2[@data-e2e='user-title']")
                STATUS["user"] = user_element.text
                print(f">>> Logged in as: {STATUS['user']}")
            except:
                STATUS["user"] = "Unknown (Check Session ID)"

            while True:
                STATUS["status"] = "Monitoring Messages..."
                driver.get("https://www.tiktok.com/messages")
                time.sleep(15)
                
                replies = load_data(DB_FILE, {})
                chats = driver.find_elements(By.XPATH, "//div[contains(@class, 'DivThreadItem')]")
                
                for chat in chats[:3]:
                    try:
                        chat.click()
                        time.sleep(3)
                        msg_elements = driver.find_elements(By.XPATH, "//div[@data-e2e='message-text']")
                        if msg_elements:
                            incoming = msg_elements[-1].text.lower().strip()
                            if incoming in replies:
                                box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                                box.send_keys(replies[incoming])
                                box.send_keys(Keys.ENTER)
                                print(f"Replied to {incoming}")
                    except: continue
                time.sleep(45)

        except Exception as e:
            print(f"Error: {e}")
            STATUS["status"] = "Error! Retrying..."
            try: driver.quit()
            except: pass
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_tiktok_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

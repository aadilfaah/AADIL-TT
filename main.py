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

# --- ফাইল পাথ সেটআপ ---
CONFIG_FILE = "config.json"
DB_FILE = "database.json"

def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- এডমিন প্যানেল UI (HTML) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ADIL TikTok Bot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        h2 { color: #333; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔑 Update Session ID</h2>
        <form method="POST" action="/update_session">
            <input type="text" name="session_id" placeholder="Enter New Session ID" required>
            <button type="submit">Update & Restart Bot</button>
        </form>
    </div>

    <div class="card">
        <h2>🤖 Train Bot (Add Reply)</h2>
        <form method="POST" action="/add_reply">
            <input type="text" name="question" placeholder="User Message (e.g. hi)" required>
            <textarea name="answer" placeholder="Bot Reply" required></textarea>
            <button type="submit">Add to Database</button>
        </form>
    </div>
    
    <div class="card">
        <h2>📜 Current Database</h2>
        <ul>
            {% for q, a in db.items() %}
                <li><strong>{{q}}:</strong> {{a}}</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return "<h1>Bot is Running!</h1><p>Go to /admin to manage.</p>"

@app.route('/admin')
def admin():
    db = load_data(DB_FILE, {})
    return render_template_string(HTML_TEMPLATE, db=db)

@app.route('/update_session', methods=['POST'])
def update_session():
    new_id = request.form.get('session_id')
    save_data(CONFIG_FILE, {"session_id": new_id})
    return "Session ID Updated! Please restart Render service."

@app.route('/add_reply', methods=['POST'])
def add_reply():
    q = request.form.get('question').lower().strip()
    a = request.form.get('answer').strip()
    db = load_data(DB_FILE, {})
    db[q] = a
    save_data(DB_FILE, db)
    return "Successfully Trained! <a href='/admin'>Back</a>"

def run_tiktok_bot():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    while True:
        config = load_data(CONFIG_FILE, {"session_id": ""})
        if not config["session_id"]:
            print(">>> Waiting for Session ID...")
            time.sleep(10)
            continue

        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://www.tiktok.com")
            time.sleep(5)
            
            driver.add_cookie({
                'name': 'sessionid',
                'value': config["session_id"],
                'domain': '.tiktok.com'
            })
            driver.refresh()
            time.sleep(10)

            while True:
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
                                print(f"Replied: {replies[incoming]}")
                    except: continue
                
                time.sleep(45)
        except Exception as e:
            print(f"Error: {e}")
            try: driver.quit()
            except: pass
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_tiktok_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

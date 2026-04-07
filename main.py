import os
import json
import threading
import time
from flask import Flask, request, redirect, render_template_string, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = Flask(__name__)
DB_FILE = 'database.json'
QR_FILE = 'qr.png'

# বটের গ্লোবাল স্টেট
bot_status = "Stopped" # Stopped, Loading, Running
driver = None

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({"replies": {}}, f)
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            return data if "replies" in data else {"replies": {}}
    except:
        return {"replies": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# আপডেট করা ডিজাইন (স্ট্যাটাস ইন্ডিকেটর সহ)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aadil's Bot Control</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; display: flex; justify-content: center; padding: 20px; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 30px; width: 100%; max-width: 450px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; }
        .status { font-size: 14px; margin-bottom: 20px; padding: 5px 10px; border-radius: 20px; display: inline-block; }
        .status-Stopped { background: #ef4444; }
        .status-Loading { background: #f59e0b; }
        .status-Running { background: #10b981; }
        .qr-box { background: white; padding: 10px; border-radius: 15px; margin: 20px auto; min-height: 200px; display: flex; align-items: center; justify-content: center; }
        img { max-width: 200px; }
        .btn-start { background: #38bdf8; color: #000; padding: 12px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; margin-bottom: 20px; }
        input { width: 100%; padding: 10px; margin: 5px 0; border-radius: 10px; border: none; background: #1e293b; color: white; box-sizing: border-box; }
        .save-btn { background: #1d4ed8; color: white; border: none; padding: 10px; border-radius: 10px; width: 100%; cursor: pointer; margin-top: 10px; }
        .list { text-align: left; margin-top: 20px; max-height: 150px; overflow-y: auto; font-size: 13px; }
    </style>
</head>
<body>
    <div class="glass">
        <h2>❄️ Aadil's Bot Control</h2>
        <div class="status status-{{ status }}">Status: {{ status }}</div>

        {% if status == "Stopped" %}
            <form action="/start" method="post"><button class="btn-start">Start WhatsApp Scanner</button></form>
        {% else %}
            <div class="qr-box">
                {% if qr_exists %}
                    <img src="/get_qr?t={{ time }}" alt="QR Code">
                {% else %}
                    <p style="color: #000;">QR কোড লোড হচ্ছে... (অপেক্ষা করুন)</p>
                {% endif %}
            </div>
        {% endif %}

        <hr style="opacity: 0.1; margin: 20px 0;">
        
        <form action="/train" method="post">
            <input type="text" name="msg" placeholder="ইউজার মেসেজ" required>
            <input type="text" name="reply" placeholder="বট রিপ্লাই" required>
            <button class="save-btn" type="submit">ডাটাবেসে সেভ করুন</button>
        </form>

        <div class="list">
            {% for msg, reply in replies.items() %}
            <div style="margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.05);"><b>U:</b> {{ msg }} | <b>B:</b> {{ reply }}</div>
            {% endfor %}
        </div>
    </div>
    <script>if("{{ status }}" != "Stopped") { setTimeout(() => { location.reload(); }, 15000); }</script>
</body>
</html>
"""

def start_whatsapp_thread():
    global bot_status, driver
    bot_status = "Loading"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com/")
        
        # কিউআর কোড খোঁজার চেষ্টা
        retries = 0
        while retries < 12: # ২ মিনিট পর্যন্ত চেষ্টা করবে
            try:
                qr_element = driver.find_element(By.CSS_SELECTOR, "canvas")
                if qr_element:
                    qr_element.screenshot(QR_FILE)
                    bot_status = "Running"
                    break
            except:
                time.sleep(10)
                retries += 1
        
        # অটো রিপ্লাই লুপ (লগইন হওয়ার পর)
        while bot_status == "Running":
            # এখানে database.json থেকে রিপ্লাই দেওয়ার লজিক কাজ করবে
            time.sleep(5)
            
    except Exception as e:
        print(f"Error: {e}")
        bot_status = "Stopped"

@app.route('/')
def index():
    data = load_db()
    qr_exists = os.path.exists(QR_FILE)
    return render_template_string(HTML_TEMPLATE, replies=data['replies'], status=bot_status, qr_exists=qr_exists, time=time.time())

@app.route('/start', methods=['POST'])
def start_bot():
    global bot_status
    if bot_status == "Stopped":
        threading.Thread(target=start_whatsapp_thread, daemon=True).start()
    return redirect('/')

@app.route('/get_qr')
def get_qr():
    if os.path.exists(QR_FILE):
        return send_file(QR_FILE, mimetype='image/png')
    return "No QR", 404

@app.route('/train', methods=['POST'])
def train():
    msg, reply = request.form.get('msg', '').lower().strip(), request.form.get('reply', '').strip()
    if msg and reply:
        data = load_db()
        data['replies'][msg] = reply
        save_db(data)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

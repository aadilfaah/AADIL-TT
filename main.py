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

# ডাটাবেস হ্যান্ডেলিং (KeyError ফিক্সড)
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"replies": {}}, f)
        return {"replies": {}}
    
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            if "replies" not in data:
                return {"replies": {}}
            return data
    except:
        return {"replies": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# প্রিমিয়াম আইসি ব্লু গ্লাসমরফিজম ডিজাইন
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aadil's Bot Trainer</title>
    <style>
        body {
            background: radial-gradient(circle at top right, #1e293b, #0f172a);
            color: white; font-family: 'Segoe UI', sans-serif;
            display: flex; justify-content: center; min-height: 100vh; margin: 0; padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px; padding: 30px; width: 100%; max-width: 450px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); text-align: center;
        }
        h2 { color: #7dd3fc; text-shadow: 0 0 10px rgba(125, 211, 252, 0.5); }
        .qr-section { background: white; padding: 10px; border-radius: 15px; margin: 20px auto; display: inline-block; }
        img { max-width: 200px; display: block; }
        input {
            width: 100%; padding: 12px; margin: 8px 0; border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(15, 23, 42, 0.6);
            color: white; box-sizing: border-box;
        }
        button {
            width: 100%; padding: 14px; background: linear-gradient(135deg, #38bdf8, #1d4ed8);
            border: none; border-radius: 12px; color: white; font-weight: bold;
            cursor: pointer; transition: 0.3s; margin-top: 10px;
        }
        button:hover { transform: translateY(-20px); box-shadow: 0 5px 15px rgba(56, 189, 248, 0.4); }
        .list-container { margin-top: 25px; text-align: left; max-height: 200px; overflow-y: auto; }
        .item { background: rgba(255, 255, 255, 0.03); padding: 10px; margin-bottom: 8px; border-radius: 10px; border-left: 3px solid #38bdf8; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>❄️ Aadil's WhatsApp Bot</h2>
        
        <div class="qr-section">
            {% if qr_exists %}
                <img src="/get_qr?t={{ time }}" alt="Scan QR">
            {% else %}
                <p style="color: #000; padding: 20px;">QR কোড তৈরি হচ্ছে...</p>
            {% endif %}
        </div>
        
        <form action="/train" method="post">
            <input type="text" name="msg" placeholder="যদি এই মেসেজ দেয়..." required>
            <input type="text" name="reply" placeholder="বট এই উত্তর দিবে..." required>
            <button type="submit">ডাটাবেসে সেভ করুন</button>
        </form>

        <div class="list-container">
            <p style="color: #94a3b8; font-size: 14px;">ট্রেইন্ড ডাটাবেস:</p>
            {% for msg, reply in replies.items() %}
            <div class="item">
                <b style="color: #7dd3fc;">U:</b> {{ msg }} <br>
                <b style="color: #38bdf8;">B:</b> {{ reply }}
            </div>
            {% endfor %}
        </div>
    </div>
    <script>setTimeout(() => { location.reload(); }, 20000);</script>
</body>
</html>
"""

@app.route('/')
def index():
    data = load_db()
    qr_exists = os.path.exists(QR_FILE)
    return render_template_string(HTML_TEMPLATE, replies=data['replies'], qr_exists=qr_exists, time=time.time())

@app.route('/get_qr')
def get_qr():
    if os.path.exists(QR_FILE):
        return send_file(QR_FILE, mimetype='image/png')
    return "No QR", 404

@app.route('/train', methods=['POST'])
def train():
    msg = request.form.get('msg', '').lower().strip()
    reply = request.form.get('reply', '').strip()
    if msg and reply:
        data = load_db()
        data['replies'][msg] = reply
        save_db(data)
    return redirect('/')

def start_whatsapp():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com/")
        
        while True:
            try:
                qr_element = driver.find_element(By.CSS_SELECTOR, "canvas")
                if qr_element:
                    qr_element.screenshot(QR_FILE)
            except:
                pass
            time.sleep(10)
    except Exception as e:
        print(f"Driver Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=start_whatsapp, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

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
QR_FILE = 'qr.png' # পাথ সহজ করা হয়েছে

# ডাটাবেস হ্যান্ডেলিং
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({"replies": {}}, f)
    with open(DB_FILE, 'r') as f:
        try: return json.load(f)
        except: return {"replies": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# HTML ইন্টারফেস (একদম ক্লিন)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Aadil Bot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; text-align: center; padding: 10px; }
        .card { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; max-width: 400px; margin: auto; border: 1px solid rgba(255,255,255,0.1); }
        img { background: white; padding: 5px; border-radius: 5px; margin: 15px 0; max-width: 100%; }
        input { width: 100%; padding: 10px; margin: 5px 0; border-radius: 8px; border: none; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #38bdf8; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .item { background: rgba(255,255,255,0.05); padding: 8px; margin-top: 5px; border-radius: 5px; font-size: 13px; text-align: left; }
    </style>
</head>
<body>
    <div class="card">
        <h3>❄️ Aadil's WhatsApp Bot</h3>
        <p style="font-size: 12px;">QR কোড লোড না হলে পেজ রিফ্রেশ দিন</p>
        
        {% if qr_exists %}
            <img src="/get_qr?t={{ time }}" alt="Scan Me">
        {% else %}
            <div style="padding: 40px;">QR কোড তৈরি হচ্ছে...</div>
        {% endif %}
        
        <form action="/train" method="post">
            <input type="text" name="msg" placeholder="ইউজার মেসেজ (উদা: হাই)" required>
            <input type="text" name="reply" placeholder="বট রিপ্লাই (উদা: হ্যালো)" required>
            <button type="submit">ডাটাবেসে সেভ করুন</button>
        </form>

        <div style="margin-top: 20px;">
            <p>ট্রেইন্ড লিস্ট:</p>
            {% for msg, reply in replies.items() %}
            <div class="item"><b>U:</b> {{ msg }} <br> <b>B:</b> {{ reply }}</div>
            {% endfor %}
        </div>
    </div>
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
    return "No QR yet", 404

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
        print("Driver Started Successfully")
        
        while True:
            try:
                # QR কোড খোঁজা
                qr_element = driver.find_element(By.CSS_SELECTOR, "canvas")
                if qr_element:
                    qr_element.screenshot(QR_FILE)
            except:
                pass
            time.sleep(10) # প্রতি ১০ সেকেন্ডে কিউআর আপডেট হবে
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=start_whatsapp, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)

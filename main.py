import os
import json
import threading
import time
import base64
from flask import Flask, request, redirect, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
DB_FILE = 'database.json'
QR_FILE = 'static/qr.png'

# স্ট্যাটিক ফোল্ডার তৈরি (QR সেভ করার জন্য)
if not os.path.exists('static'):
    os.makedirs('static')

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({"replies": {}}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# প্রিমিয়াম ড্যাশবোর্ড উইথ QR সেকশন
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Aadil's Bot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; text-align: center; padding: 20px; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 30px; max-width: 500px; margin: auto; border: 1px solid rgba(255,255,255,0.1); }
        .qr-box { background: white; padding: 10px; border-radius: 10px; margin: 20px 0; display: inline-block; }
        input { width: 90%; padding: 12px; margin: 10px 0; border-radius: 10px; border: none; background: #1e293b; color: white; }
        button { width: 95%; padding: 12px; background: #38bdf8; border: none; border-radius: 10px; color: #000; font-weight: bold; cursor: pointer; }
        .list-item { background: rgba(255,255,255,0.03); padding: 10px; margin-top: 10px; border-radius: 10px; text-align: left; }
    </style>
</head>
<body>
    <div class="glass">
        <h2>📱 WhatsApp Login</h2>
        <p style="font-size: 12px; color: #94a3b8;">নিচের QR কোডটি আপনার WhatsApp App দিয়ে স্ক্যান করুন</p>
        
        <div class="qr-box">
            <img src="/static/qr.png?t={{ time }}" alt="QR Code Loading..." width="250">
        </div>
        
        <form action="/train" method="post">
            <input type="text" name="msg" placeholder="ইউজার মেসেজ" required>
            <input type="text" name="reply" placeholder="বট রিপ্লাই" required>
            <button type="submit">ট্রেইন করান</button>
        </form>

        <div style="margin-top: 20px;">
            <h4>ট্রেইন্ড লিস্ট:</h4>
            {% for msg, reply in replies.items() %}
            <div class="list-item"><b>U:</b> {{ msg }} | <b>B:</b> {{ reply }}</div>
            {% endfor %}
        </div>
    </div>
    <script>setTimeout(() => { location.reload(); }, 15000); // ১৫ সেকেন্ড পর অটো রিফ্রেশ হবে QR এর জন্য</script>
</body>
</html>
"""

driver = None

def start_whatsapp():
    global driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://web.whatsapp.com/")
    
    print("WhatsApp Web Loading...")
    
    while True:
        try:
            # QR কোড এলিমেন্ট খুঁজে বের করা
            qr_element = driver.find_element(By.CSS_SELECTOR, "canvas")
            if qr_element:
                qr_element.screenshot(QR_FILE)
                print("QR Code Updated")
            
            # অটো রিপ্লাই চেক (লগইন হওয়ার পর)
            # এখানে database.json থেকে চেক করে রিপ্লাই দেওয়ার লজিক কাজ করবে
        except:
            pass
        time.sleep(5)

@app.route('/')
def index():
    data = load_db()
    return render_template_string(HTML_TEMPLATE, replies=data['replies'], time=time.time())

@app.route('/train', methods=['POST'])
def train():
    msg, reply = request.form.get('msg').lower().strip(), request.form.get('reply').strip()
    if msg and reply:
        data = load_db()
        data['replies'][msg] = reply
        save_db(data)
    return redirect('/')

if __name__ == '__main__':
    threading.Thread(target=start_whatsapp, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

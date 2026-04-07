import os, json, threading, time, logging
from flask import Flask, request, redirect, render_template_string, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# লগিং কনফিগারেশন যাতে রেন্ডার ড্যাশবোর্ডে সব দেখা যায়
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DB_FILE = 'database.json'
QR_FILE = 'qr.png'

bot_status = "Stopped"
driver = None

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({"replies": {}}, f)
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            return data if "replies" in data else {"replies": {}}
    except: return {"replies": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# প্রিমিয়াম আইসি ব্লু গ্লাসমরফিজম ডিজাইন এবং বড় কিউআর কোড বক্স
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aadil's WhatsApp Bot Control</title>
    <style>
        body { background: #0f172a; color: white; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; padding: 20px; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border-radius: 20px; padding: 30px; width: 100%; max-width: 500px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); }
        .status { padding: 8px 20px; border-radius: 20px; display: inline-block; margin-bottom: 20px; font-weight: bold; font-size: 14px; }
        .Stopped { background: #ef4444; } .Loading { background: #f59e0b; } .Running { background: #10b981; }
        .qr-box { background: white; padding: 15px; border-radius: 15px; margin: 20px auto; min-height: 250px; display: flex; align-items: center; justify-content: center; color: #000; overflow: hidden; }
        .qr-img { max-width: 100%; height: auto; border-radius: 10px; }
        .btn { background: linear-gradient(135deg, #38bdf8, #1d4ed8); color: white; padding: 14px; border: none; border-radius: 12px; font-weight: bold; width: 100%; cursor: pointer; transition: 0.3s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(56, 189, 248, 0.4); }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); background: rgba(15, 23, 42, 0.6); color: white; box-sizing: border-box; }
        .list { text-align: left; margin-top: 25px; max-height: 150px; overflow-y: auto; font-size: 13px; }
        .item { background: rgba(255,255,255,0.03); padding: 8px; margin-bottom: 5px; border-radius: 8px; border-left: 3px solid #38bdf8; }
    </style>
</head>
<body>
    <div class="glass">
        <h2 style="color: #7dd3fc;">❄️ Aadil's WhatsApp Bot</h2>
        <div class="status {{ status }}">Status: {{ status }}</div>

        {% if status == "Stopped" %}
            <form action="/start" method="post"><button class="btn">Start WhatsApp Scanner</button></form>
        {% else %}
            <div class="qr-box">
                {% if qr_exists %}<img src="/get_qr?t={{ time }}" class="qr-img">{% else %}কিউআর কোড তৈরি হচ্ছে... (লগ চেক করুন){% endif %}
            </div>
        {% endif %}
        
        <form action="/train" method="post" style="margin-top: 25px;">
            <input type="text" name="msg" placeholder="যদি কেউ এই মেসেজ দেয়..." required>
            <input type="text" name="reply" placeholder="বট এই উত্তর দিবে..." required>
            <button class="btn" style="background:#1e40af;">ডাটাবেসে সেভ করুন</button>
        </form>

        <div class="list">
            <p style="color: #94a3b8;">ট্রেইন্ড ডাটাবেস:</p>
            {% for msg, reply in replies.items() %}
            <div class="item"><b>U:</b> {{ msg }} | <b>B:</b> {{ reply }}</div>
            {% endfor %}
        </div>
    </div>
    <script>if("{{ status }}" != "Stopped") { setTimeout(()=>location.reload(), 15000); }</script>
</body>
</html>
"""

def start_whatsapp_thread():
    global bot_status, driver
    logger.info(">>> STEP 1: Background Thread Started")
    bot_status = "Loading"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # কিউআর কোড পুরোপুরি দেখানোর জন্য উইন্ডো বড় করা
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--force-device-scale-factor=1") # জুম লেভেল ঠিক রাখা
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        logger.info(">>> STEP 2: Launching Chrome Browser...")
        driver = webdriver.Chrome(options=chrome_options)
        logger.info(">>> STEP 3: Navigating to WhatsApp Web...")
        driver.get("https://web.whatsapp.com/")
        
        # পেজ লোড হওয়ার জন্য অন্তত ৩০ সেকেন্ড অপেক্ষা করুন
        time.sleep(30)
        
        # কিউআর কোড খোঁজার জন্য ১৫ বার চেষ্টা (প্রতি ১০ সেকেন্ডে)
        for i in range(15):
            logger.info(f">>> STEP 4: Searching for QR Code Canvas... (Attempt {i+1})")
            try:
                # পুরো ক্যানভাস বা কিউআর এলিমেন্টটি খুঁজে বের করা
                qr_element = driver.find_element(By.CSS_SELECTOR, "canvas")
                if qr_element:
                    # নির্দিষ্ট কিউআর কোডটির স্ক্রিনশট নেওয়া
                    qr_element.screenshot(QR_FILE)
                    logger.info(">>> STEP 5: Full QR Code Screenshot Saved Successfully!")
                    bot_status = "Running"
                    break
            except:
                time.sleep(10)
        
        if bot_status != "Running":
            logger.error(">>> FAILED: QR Code not found within 2.5 minutes.")
            bot_status = "Stopped"

    except Exception as e:
        logger.error(f">>> CRITICAL ERROR: {str(e)}")
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
        logger.info(">>> User Action: Start Button Clicked")
        threading.Thread(target=start_whatsapp_thread, daemon=True).start()
    return redirect('/')

@app.route('/get_qr')
def get_qr():
    return send_file(QR_FILE, mimetype='image/png') if os.path.exists(QR_FILE) else ("No QR File Found", 404)

@app.route('/train', methods=['POST'])
def train():
    msg, reply = request.form.get('msg','').lower().strip(), request.form.get('reply','').strip()
    if msg and reply:
        data = load_db(); data['replies'][msg] = reply; save_db(data)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

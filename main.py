import os, json, threading, time, logging, sys
from flask import Flask, request, redirect, render_template_string, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# লগিং সেটআপ যাতে রেন্ডারে সব দেখা যায়
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DB_FILE = 'database.json'
QR_FILE = 'qr.png'

# গ্লোবাল ডাটা স্টোর
bot_info = {
    "status": "Stopped",
    "number": "Not Logged In",
    "logs": [] # {'t': 'time', 's': 'sender', 'm': 'msg', 'r': 'reply'}
}
driver = None

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({"replies": {}}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# প্রিমিয়াম আইসি ব্লু প্যানেল ডিজাইন
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aadil Bot Pro</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 25px; width: 100%; max-width: 500px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; text-align: center; }
        .status { padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin-bottom: 15px; }
        .Stopped { background: #ef4444; } .Loading { background: #f59e0b; } .Running { background: #10b981; }
        .info-card { background: rgba(56, 189, 248, 0.1); border: 1px solid #38bdf8; padding: 10px; border-radius: 10px; margin: 10px 0; font-size: 14px; }
        .qr-box { background: white; padding: 10px; border-radius: 10px; margin: 15px auto; width: fit-content; }
        .btn { background: #38bdf8; color: #000; padding: 12px; border: none; border-radius: 10px; font-weight: bold; width: 100%; cursor: pointer; }
        input { width: 100%; padding: 10px; margin: 5px 0; border-radius: 8px; border: none; background: #1e293b; color: white; box-sizing: border-box; }
        .log-box { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 10px; text-align: left; max-height: 250px; overflow-y: auto; font-size: 12px; }
        .log-item { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 5px 0; }
    </style>
</head>
<body>
    <div class="glass">
        <h2 style="color:#7dd3fc; margin:0;">🤖 Aadil Bot Dashboard</h2>
        <div class="status {{ info['status'] }}">Status: {{ info['status'] }}</div>
        
        <div class="info-card">👤 Connected Number: <b>{{ info['number'] }}</b></div>

        {% if info['status'] == "Stopped" %}
            <form action="/start" method="post"><button class="btn">Start WhatsApp Scanner</button></form>
        {% elif info['status'] == "Loading" %}
            <div class="qr-box">
                {% if qr_exists %}<img src="/get_qr?t={{ time }}" width="200">{% else %}<p style="color:black">QR তৈরি হচ্ছে...</p>{% endif %}
            </div>
        {% endif %}

        <form action="/train" method="post" style="margin-top:20px;">
            <input type="text" name="msg" placeholder="মেসেজ..." required>
            <input type="text" name="reply" placeholder="উত্তর..." required>
            <button class="btn" style="background:#1d4ed8; color:white;">ট্রেনিং ডাটা সেভ</button>
        </form>
    </div>

    <div class="glass">
        <h3 style="margin:0; color:#10b981;">📜 Live Logs</h3>
        <div class="log-box">
            {% for log in info['logs'][::-1] %}
            <div class="log-item">
                <small style="color:#94a3b8;">[{{ log.t }}]</small> <b>{{ log.s }}</b>: {{ log.m }} <br>
                <span style="color:#34d399;">↳ Bot: {{ log.r }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>if("{{ info['status'] }}" != "Stopped") { setTimeout(()=>location.reload(), 10000); }</script>
</body>
</html>
"""

def bot_worker():
    global bot_info, driver
    bot_info["status"] = "Loading"
    logger.info(">>> STEP 1: Starting Browser")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://web.whatsapp.com/")
        
        # কিউআর এবং লগইন চেক লুপ
        logged_in = False
        for i in range(20):
            try:
                # কিউআর সেভ করা
                if not logged_in:
                    qr_canvas = driver.find_element(By.CSS_SELECTOR, "canvas")
                    qr_canvas.screenshot(QR_FILE)
                    logger.info(f">>> QR Updated (Attempt {i+1})")
                
                # লগইন হয়েছে কিনা চেক (সার্চ বার বা চ্যাট লিস্ট আসলে)
                if driver.find_elements(By.CSS_SELECTOR, "div[data-tab='3']"):
                    logger.info(">>> STEP 2: Login Successful!")
                    bot_info["status"] = "Running"
                    logged_in = True
                    
                    # নম্বর বের করার চেষ্টা
                    driver.get("https://web.whatsapp.com/settings/profile")
                    time.sleep(3)
                    try:
                        num_el = driver.find_element(By.XPATH, "//div[contains(text(), '+')]")
                        bot_info["number"] = num_el.text
                    except: bot_info["number"] = "Connected (Unknown Number)"
                    
                    driver.get("https://web.whatsapp.com/") # মেইন পেজে ফিরে আসা
                    break
            except: pass
            time.sleep(10)

        # অটো রিপ্লাই লজিক
        while bot_info["status"] == "Running":
            try:
                unread = driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='unread messages']")
                for chat in unread:
                    chat.click()
                    time.sleep(1)
                    
                    sender = driver.find_element(By.CSS_SELECTOR, "header span[title]").get_attribute("title")
                    msgs = driver.find_elements(By.CSS_SELECTOR, "div.message-in span.selectable-text")
                    
                    if msgs:
                        m_text = msgs[-1].text
                        m_clean = m_text.lower().strip()
                        
                        db = load_db()
                        if m_clean in db['replies']:
                            r_text = db['replies'][m_clean]
                            
                            # রিপ্লাই পাঠানো
                            box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']")
                            box.send_keys(r_text)
                            driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']").click()
                            
                            # লগে যোগ
                            bot_info["logs"].append({
                                "t": time.strftime("%H:%M"), "s": sender, "m": m_text, "r": r_text
                            })
                            if len(bot_info["logs"]) > 15: bot_info["logs"].pop(0)
            except: pass
            time.sleep(5)

    except Exception as e:
        logger.error(f">>> ERROR: {e}")
        bot_info["status"] = "Stopped"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, info=bot_info, qr_exists=os.path.exists(QR_FILE), time=time.time())

@app.route('/start', methods=['POST'])
def start():
    if bot_info["status"] == "Stopped":
        threading.Thread(target=bot_worker, daemon=True).start()
    return redirect('/')

@app.route('/get_qr')
def get_qr(): return send_file(QR_FILE) if os.path.exists(QR_FILE) else ("404", 404)

@app.route('/train', methods=['POST'])
def train():
    m, r = request.form.get('msg','').lower().strip(), request.form.get('reply','').strip()
    if m and r:
        db = load_db(); db['replies'][m] = r; save_db(db)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

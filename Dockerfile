import os, json, threading, time, logging, sys
from flask import Flask, request, redirect, render_template_string, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

app = Flask(__name__)
DB_FILE = 'database.json'
QR_FILE = 'qr.png'

# গ্লোবাল স্ট্যাটাস
bot_info = {
    "status": "Stopped",
    "device_state": "Offline", # Offline, Connecting, Syncing, Active
    "number": "Not Logged In",
    "logs": []
}
driver = None

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({"replies": {}}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

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
        .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 12px; margin-bottom: 10px; display: inline-block; }
        .Active { background: #10b981; } .Syncing { background: #f59e0b; } .Offline { background: #ef4444; }
        .info-card { background: rgba(56, 189, 248, 0.1); border: 1px solid #38bdf8; padding: 10px; border-radius: 10px; margin: 10px 0; font-size: 14px; text-align: left; }
        .qr-box { background: white; padding: 10px; border-radius: 10px; margin: 15px auto; width: fit-content; }
        .btn { background: #38bdf8; color: #000; padding: 12px; border: none; border-radius: 10px; font-weight: bold; width: 100%; cursor: pointer; }
        .log-box { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 10px; text-align: left; max-height: 200px; overflow-y: auto; font-size: 12px; border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body>
    <div class="glass">
        <h2 style="color:#7dd3fc; margin:0;">🤖 Aadil Bot Control</h2>
        <div style="margin: 10px 0;">
            <span class="status-badge {{ info['device_state'] }}">Device: {{ info['device_state'] }}</span>
        </div>
        
        <div class="info-card">
            👤 <b>Number:</b> {{ info['number'] }}<br>
            📡 <b>Status:</b> {{ info['status'] }}
        </div>

        {% if info['status'] == "Stopped" %}
            <form action="/start" method="post"><button class="btn">Start Bot</button></form>
        {% elif info['device_state'] != "Active" %}
            <div class="qr-box">
                {% if qr_exists %}<img src="/get_qr?t={{ time }}" width="200">{% else %}<p style="color:black">QR Loading...</p>{% endif %}
            </div>
            <p style="font-size: 12px; color: #94a3b8;">স্ক্যান করার পর ১-২ মিনিট অপেক্ষা করুন।</p>
        {% endif %}
    </div>

    <div class="glass">
        <h3 style="margin:0 0 10px 0; color:#34d399;">📜 Live Chat Logs</h3>
        <div class="log-box">
            {% for log in info['logs'][::-1] %}
            <div style="margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05);">
                <small style="color:#94a3b8;">[{{ log.t }}]</small> <b>{{ log.s }}</b>: {{ log.m }}<br>
                <span style="color:#34d399;">↳ {{ log.r }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>setTimeout(()=>location.reload(), 15000);</script>
</body>
</html>
"""

def bot_worker():
    global bot_info, driver
    bot_info["status"] = "Starting"
    bot_info["device_state"] = "Connecting"
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://web.whatsapp.com/")
        
        # কিউআর এবং সিঙ্ক চেক
        for i in range(30):
            try:
                # যদি সার্চ বক্স খুঁজে পায়, তারমানে লগইন সফল
                if driver.find_elements(By.CSS_SELECTOR, "div[data-tab='3']"):
                    bot_info["device_state"] = "Active"
                    bot_info["status"] = "Running"
                    
                    # নম্বর বের করার চেষ্টা
                    driver.get("https://web.whatsapp.com/settings/profile")
                    time.sleep(3)
                    try:
                        bot_info["number"] = driver.find_element(By.XPATH, "//div[contains(text(), '+')]").text
                    except: pass
                    driver.get("https://web.whatsapp.com/")
                    break
                
                # যদি কিউআর থাকে
                elif driver.find_elements(By.CSS_SELECTOR, "canvas"):
                    driver.find_element(By.CSS_SELECTOR, "canvas").screenshot(QR_FILE)
                    bot_info["device_state"] = "Waiting for Scan"
                
                # যদি সিঙ্ক হতে থাকে (আপনার স্ক্রিনশটের অবস্থা)
                elif driver.find_elements(By.CSS_SELECTOR, "div[role='progressbar']"):
                    bot_info["device_state"] = "Syncing Data..."
                
            except: pass
            time.sleep(10)

        # মেসেজ লিসেনার
        while bot_info["device_state"] == "Active":
            try:
                unread = driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='unread messages']")
                for chat in unread:
                    chat.click()
                    time.sleep(1)
                    sender = driver.find_element(By.CSS_SELECTOR, "header span[title]").get_attribute("title")
                    msgs = driver.find_elements(By.CSS_SELECTOR, "div.message-in span.selectable-text")
                    if msgs:
                        m_text = msgs[-1].text
                        db = load_db()
                        if m_text.lower().strip() in db['replies']:
                            reply = db['replies'][m_text.lower().strip()]
                            box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']")
                            box.send_keys(reply)
                            driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']").click()
                            bot_info["logs"].append({"t": time.strftime("%H:%M"), "s": sender, "m": m_text, "r": reply})
                            if len(bot_info["logs"]) > 20: bot_info["logs"].pop(0)
            except: pass
            time.sleep(5)

    except Exception as e:
        logger.error(f"Error: {e}")
        bot_info["device_state"] = "Offline"
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

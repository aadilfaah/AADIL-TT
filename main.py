import os, json, threading, time, logging
from flask import Flask, request, redirect, render_template_string, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DB_FILE = 'database.json'
QR_FILE = 'qr.png'

# গ্লোবাল ভেরিয়েবল
bot_status = "Stopped"
login_number = "Not Logged In"
chat_logs = [] # [ {'time': '...', 'sender': '...', 'msg': '...', 'reply': '...'}, ... ]
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aadil's WhatsApp Bot Pro</title>
    <style>
        body { background: #0f172a; color: white; font-family: 'Segoe UI', sans-serif; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border-radius: 20px; padding: 25px; width: 100%; max-width: 600px; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); margin-bottom: 20px; }
        .status { padding: 8px 15px; border-radius: 20px; display: inline-block; font-weight: bold; font-size: 13px; margin-bottom: 10px; }
        .Stopped { background: #ef4444; } .Loading { background: #f59e0b; } .Running { background: #10b981; }
        .info-card { background: rgba(56, 189, 248, 0.1); border-radius: 10px; padding: 10px; margin: 10px 0; border: 1px solid #38bdf8; font-size: 14px; }
        .qr-box { background: white; padding: 15px; border-radius: 15px; margin: 15px auto; width: fit-content; }
        .btn { background: linear-gradient(135deg, #38bdf8, #1d4ed8); color: white; padding: 12px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; transition: 0.3s; }
        input { width: 100%; padding: 10px; margin: 8px 0; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); background: #1e293b; color: white; box-sizing: border-box; }
        .log-container { text-align: left; max-height: 300px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 10px; padding: 10px; margin-top: 15px; font-size: 12px; }
        .log-item { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 5px 0; margin-bottom: 5px; }
        .log-time { color: #94a3b8; font-size: 10px; }
        .log-msg { color: #7dd3fc; }
        .log-reply { color: #34d399; font-weight: bold; }
    </style>
</head>
<body>
    <div class="glass">
        <h2 style="color: #7dd3fc; margin:0;">🤖 Bot Dashboard</h2>
        <div style="margin-top:10px;">
            <div class="status {{ status }}">Status: {{ status }}</div>
        </div>

        <div class="info-card">
            👤 <b>Logged In As:</b> {{ login_number }}
        </div>

        {% if status == "Stopped" %}
            <form action="/start" method="post"><button class="btn">Start WhatsApp Scanner</button></form>
        {% elif status == "Loading" and not qr_exists %}
            <p>ব্রাউজার চালু হচ্ছে... লগে নজর রাখুন।</p>
        {% elif not logged_in %}
            <div class="qr-box">
                {% if qr_exists %}<img src="/get_qr?t={{ time }}" width="220">{% else %}কিউআর লোড হচ্ছে...{% endif %}
            </div>
        {% endif %}

        <form action="/train" method="post" style="margin-top: 20px;">
            <input type="text" name="msg" placeholder="ইউজার যা লিখবে..." required>
            <input type="text" name="reply" placeholder="বট যা উত্তর দিবে..." required>
            <button class="btn" style="background:#1e40af;">ট্রেনিং ডাটা সেভ করুন</button>
        </form>
    </div>

    <div class="glass">
        <h3 style="margin:0; color: #34d399;">📜 Live Chat Logs</h3>
        <div class="log-container">
            {% if not chat_logs %}
                <p style="color:#64748b; text-align:center;">এখনো কোনো মেসেজ আসেনি...</p>
            {% else %}
                {% for log in chat_logs[::-1] %}
                <div class="log-item">
                    <span class="log-time">[{{ log.time }}]</span><br>
                    <b>Sender:</b> {{ log.sender }} <br>
                    <span class="log-msg">💬: {{ log.msg }}</span> <br>
                    <span class="log-reply">🤖: {{ log.reply }}</span>
                </div>
                {% endfor %}
            {% endif %}
        </div>
    </div>

    <script>if("{{ status }}" != "Stopped") { setTimeout(()=>location.reload(), 10000); }</script>
</body>
</html>
"""

def start_whatsapp_thread():
    global bot_status, driver, login_number, chat_logs
    bot_status = "Loading"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com/")
        
        # QR Code Step
        for i in range(20):
            try:
                if i > 5: # কয়েক সেকেন্ড পর কিউআর চেক
                    qr_canvas = driver.find_element(By.CSS_SELECTOR, "canvas")
                    qr_canvas.screenshot(QR_FILE)
                    logger.info("QR Saved")
                
                # লগইন হয়েছে কিনা চেক (সার্চ বার আসলে বুঝবো লগইন হয়েছে)
                if driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']"):
                    bot_status = "Running"
                    logger.info("Login Success!")
                    
                    # নম্বর বের করার চেষ্টা
                    try:
                        driver.get("https://web.whatsapp.com/settings/profile")
                        time.sleep(2)
                        num_element = driver.find_element(By.XPATH, "//div[contains(text(), '+')]")
                        login_number = num_element.text
                        driver.get("https://web.whatsapp.com/") # আবার মেইন পেজে ফেরা
                    except: login_number = "Unknown (Check Mobile)"
                    break
            except: pass
            time.sleep(10)

        # Message Listener Loop
        while bot_status == "Running":
            try:
                unread_chats = driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='unread messages']")
                for chat in unread_chats:
                    chat.click()
                    time.sleep(1)
                    
                    # প্রেরকের নাম/নম্বর এবং মেসেজ পড়া
                    sender_name = driver.find_element(By.CSS_SELECTOR, "header span[title]").get_attribute("title")
                    messages = driver.find_elements(By.CSS_SELECTOR, "div.message-in span.selectable-text")
                    
                    if messages:
                        raw_msg = messages[-1].text
                        clean_msg = raw_msg.lower().strip()
                        
                        data = load_db()
                        if clean_msg in data['replies']:
                            reply_val = data['replies'][clean_msg]
                            
                            # রিপ্লাই পাঠানো
                            input_box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']")
                            input_box.send_keys(reply_val)
                            driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']").click()
                            
                            # লগে যোগ করা
                            chat_logs.append({
                                "time": time.strftime("%H:%M:%S"),
                                "sender": sender_name,
                                "msg": raw_msg,
                                "reply": reply_val
                            })
                            # মেমোরি বাঁচাতে শুধু শেষ ২০টি লগ রাখা
                            if len(chat_logs) > 20: chat_logs.pop(0)
            except: pass
            time.sleep(5)

    except Exception as e:
        logger.error(f"Error: {e}")
        bot_status = "Stopped"

@app.route('/')
def index():
    data = load_db()
    qr_exists = os.path.exists(QR_FILE)
    logged_in = (bot_status == "Running" and login_number != "Not Logged In")
    return render_template_string(HTML_TEMPLATE, 
                                 replies=data['replies'], 
                                 status=bot_status, 
                                 qr_exists=qr_exists, 
                                 login_number=login_number,
                                 chat_logs=chat_logs,
                                 logged_in=logged_in,
                                 time=time.time())

@app.route('/start', methods=['POST'])
def start_bot():
    global bot_status
    if bot_status == "Stopped":
        threading.Thread(target=start_whatsapp_thread, daemon=True).start()
    return redirect('/')

@app.route('/get_qr')
def get_qr():
    return send_file(QR_FILE, mimetype='image/png') if os.path.exists(QR_FILE) else ("404", 404)

@app.route('/train', methods=['POST'])
def train():
    msg, reply = request.form.get('msg','').lower().strip(), request.form.get('reply','').strip()
    if msg and reply:
        data = load_db(); data['replies'][msg] = reply; save_db(data)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

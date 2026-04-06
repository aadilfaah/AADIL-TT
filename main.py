import time
import os
import threading
import firebase_admin
from firebase_admin import credentials, db
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from flask import Flask, render_template_string, request, jsonify

# --- ১. ফ্লাস্ক অ্যাডমিন প্যানেল UI (HTML) ---
# এটি সরাসরি পাইথনের ভেতরেই থাকবে, আলাদা index.html লাগবে না।
HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>ADIL-TT All-in-One Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; text-align: center; padding: 20px; }
        .card { background: #1e293b; padding: 25px; border-radius: 15px; max-width: 400px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
        input, textarea { width: 90%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 14px; }
        textarea { height: 80px; resize: none; }
        button { width: 95%; padding: 12px; background: #38bdf8; color: #0f172a; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s; }
        button:hover { background: #0ea5e9; transform: translateY(-2px); }
        #status { margin-top: 20px; color: #fbbf24; font-weight: bold; padding: 10px; background: #334155; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #38bdf8;">TikTok Bot Admin</h2>
        <input type="text" id="user" placeholder="TikTok Username">
        <input type="password" id="pass" placeholder="TikTok Password">
        <textarea id="msg" placeholder="Auto Reply Message..."></textarea>
        <button onclick="sendCommand()">START BOT & REPLY</button>
        <div id="status">System Status: Waiting...</div>
    </div>

    <script>
        async def sendCommand() {
            const u = document.getElementById('user').value;
            const p = document.getElementById('pass').value;
            const m = document.getElementById('msg').value;
            
            if(!u || !p || !m) return alert("All fields are required!");
            document.getElementById('status').innerText = "Sending Command to Firebase...";

            // আমরা সরাসরি পাইথনের একটি রুটে ডাটা পাঠাবো
            const res = await fetch('/api/set_command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user: u, pass: p, message: m})
            });
            const data = await res.json();
            if(data.success) document.getElementById('status').innerText = "Command Sent Successfully!";
        }

        // প্রতি ৩ সেকেন্ড পর পর স্ট্যাটাস চেক করবে
        setInterval(async () => {
            const res = await fetch('/api/get_status');
            const data = await res.json();
            document.getElementById('status').innerText = "Bot Status: " + data.status;
        }, 3000);
    </script>
</body>
</html>
"""

# --- ২. ফায়ারবেস ও ফ্লাস্ক সেটআপ ---
app = Flask(__name__)

cert_dict = {
  "type": "service_account",
  "project_id": "py-tt-75784",
  "private_key_id": "68f288c7ae4777ebbae58d6ba051feb3a486370b",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDBfXgOxAdQKoQV\nB5h3yjVmkZG8pmaF19aqIsJxJ2HhaIMZrEelcMfr6tKxOC2Yb1+E/Z+KYSuMGEpD\nuULg/VBHrZfj5zT8vicXoX8sq8fYzvUPIjLuuew4M86QT4y3kZWOkv1rVorDw72n\n0ptE4kRWAHB/+/SGY4rfT4XSWjcGnTzr4EeCLPM7RwvQduLpMni8kkjB1OIWhRK5\n4W/xIxbNOcOTx3zIcab0z+QiO8YZ1HL/I8yKvghqvQyQm3Q4UZDxa0VEKwOnJEdC\nD3IoG4VpdVBnqNePruEqGZRfz3WQS+OIQ5NGibTdxe4H2o1epXs1eGjsu1rHOHw9\nE1QhDCNTAgMBAAECggEAAVusGA5wLrPdsXgYLd8ReOLUrwpL9eyJ6S/NRZYNLdPZ\n97gp2JNuE83WJMBMMaG2fex5zjLYZ2dUPh1yxrmAcsBZLJRW3t9GzvenON0Lzg3F\n0pFe4iYT7mEOthyY1EEFV7bYaIR2/ODG2AK2bElaSXA/Weae1MKmGuMoAU34zOcS\nfl6YtIIHnB4+0bNxlG5g5IU9bnuq6cahjOWfDae1d5bR53ZPUbOwV6x85mxcpeXF\nj1HATQv9eUERSlsENt+zxGR1WKalUoI70OWFnkXVKEEW96VdP7KvxNF6ckD8u5mK\n1Kn59tdb4FWmB07mP9TmgPjDb5Ogpuxb5KVLVR4U4QKBgQD2jz5pHDg/uZm0cRXD\nERf/ein8Uejpo9y8UclcC2SNu+zgqoyGt1yIaFRgL/onolvsC+UKiHkUvf8jPtbH\n+xcS59U3bLy3e5FPWaTE4/0jWFhkJjY6FpriFCf7mX+xjvLw8s+KKMk5A/cmNgTu\nO3gcB+3LDxC2pK8VWMwnhcjtnwKBgQDI5gsCg5lduEv8IgQHbUZCOFDzjD/I5Y3/\n2hXhGaIVs6UZSw8eITeZVpgimrySFC0kZSi1Uj8Y02WtiT/nSqGmDemtgJ4sXMuN\ii0sRGydAoGHrB2GnvUgwKiLkTNj9PNrym4e7AqoiwvLvUiC54vLNtqHam5o1kmB\nC6/P/qZFzQKBgDz7/UHeWwNYEu6QsgNHrRnhy5S/Zc60WxqxWA7OOpbcDqEbThrc\nK6UJuST5ePRosjfWUVajnt9Eh2DeYB2iu3hPo2tMF/mCNNTdpWWVxr0BUwuib/M6\nOCEHP0R6GR1/8BMs26yenfbeRjlLTzjluLWmOGjrVwT2AuBS0FxOOP6dAoGATdTB\nwzGUwzhZR88t3Gq7Y4BJ7HETbRNyFgM5osG5h8rXVZs8uiGIVsGzowRrtfRXINiI\nEudQRp/vrnGT7ll9ksWlGHDR1sIEoks8AQBpS9Lit9s4fSUsNootQhT44erOO55r\nV1N/NZjY8w/b/csS36Hau8fCCp+qTnJmpKA1bqkCgYEAqpU36CpvvMhx9CEJ76MX\n2q+hpwcWd75+BM37DolPqLm3Lj2GwkR7Z5ZG300eWAel2n4b+tpQfR+JTRyYvtTH\ntpWlhwh4f/Ua8fcogVKh4d+u51DdXpaumkRFCc1JeTHcb3S7EZou9vfnCavkQKNm\nGHcf+EDRprnny0h+s5o0csw=\n-----END PRIVATE KEY-----\n".replace('\\n', '\n'),
  "client_email": "firebase-adminsdk-fbsvc@py-tt-75784.iam.gserviceaccount.com"
}

if not firebase_admin._apps:
    cred = credentials.Certificate(cert_dict)
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://py-tt-75784-default-rtdb.firebaseio.com/'})

# --- ৩. ফ্ল্যাস্ক রাউটস ---
@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/api/set_command', methods=['POST'])
def set_command():
    data = request.json
    db.reference('bot_control').update({
        'user': data['user'],
        'pass': data['pass'],
        'message': data['message'],
        'command': 'start',
        'login_status': 'Waiting for bot...'
    })
    return jsonify(success=True)

@app.route('/api/get_status')
def get_status():
    status = db.reference('bot_control/login_status').get()
    return jsonify(status=status or "Idle")

# --- ৪. টিকটক বট লজিক ---
def run_bot(u, p, msg):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(5)
        
        # Login
        driver.find_element(By.NAME, "username").send_keys(u)
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(p)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(15)

        # Message Reply
        driver.get("https://www.tiktok.com/messages")
        time.sleep(10)
        
        # প্রথম চ্যাটে রিপ্লাই
        chat = driver.find_element(By.XPATH, "//div[@data-e2e='message-item']")
        chat.click()
        time.sleep(3)
        
        input_box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
        input_box.send_keys(msg)
        input_box.send_keys(Keys.ENTER)
        time.sleep(2)
        
        return "Reply Sent Successfully!"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        try: driver.quit()
        except: pass

# ৫. ব্যাকগ্রাউন্ড মনিটর থ্রেড
def bot_monitor():
    print(">>> Bot Monitor Started")
    while True:
        try:
            ref = db.reference('bot_control')
            data = ref.get()
            if data and data.get('command') == 'start':
                print(f">>> Running bot for {data['user']}...")
                res = run_bot(data['user'], data['pass'], data['message'])
                ref.update({'login_status': res, 'command': 'idle'})
        except Exception as e:
            print(f"Monitor Error: {e}")
        time.sleep(5)

# --- ৬. মেইন রানার ---
if __name__ == "__main__":
    # বটকে আলাদা থ্রেডে চালানো
    threading.Thread(target=bot_monitor, daemon=True).start()
    
    # ফ্ল্যাস্ক সার্ভার চালানো (অ্যাডমিন প্যানেলের জন্য)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

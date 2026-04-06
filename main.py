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

# ১. ফ্লাস্ক অ্যাডমিন প্যানেল UI
HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Bot Admin Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; text-align: center; padding: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 15px; max-width: 380px; margin: auto; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
        input, textarea { width: 90%; padding: 10px; margin: 8px 0; border-radius: 5px; border: 1px solid #334155; background: #0f172a; color: white; }
        button { width: 95%; padding: 12px; background: #38bdf8; color: #0f172a; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        #status { margin-top: 15px; color: #fbbf24; font-size: 14px; background: #334155; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="color: #38bdf8;">TikTok Bot Control</h2>
        <input type="text" id="user" placeholder="Your Username">
        <input type="password" id="pass" placeholder="Your Password">
        <textarea id="msg" placeholder="Write Auto Reply Message..."></textarea>
        <button onclick="startBot()">START BOT</button>
        <div id="status">System Status: Waiting...</div>
    </div>

    <script>
        async function startBot() {
            const u = document.getElementById('user').value;
            const p = document.getElementById('pass').value;
            const m = document.getElementById('msg').value;
            if(!u || !p || !m) return alert("Fill all fields!");
            
            document.getElementById('status').innerText = "Sending command...";
            const res = await fetch('/api/set_command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user: u, pass: p, message: m})
            });
            const data = await res.json();
            if(data.success) document.getElementById('status').innerText = "Command Sent!";
        }

        setInterval(async () => {
            const res = await fetch('/api/get_status');
            const data = await res.json();
            document.getElementById('status').innerText = "Bot Status: " + data.status;
        }, 3000);
    </script>
</body>
</html>
"""

# ২. ফায়ারবেস সেটআপ (এরর ফিক্সড)
app = Flask(__name__)

cert_dict = {
  "type": "service_account",
  "project_id": "py-tt-75784",
  "private_key_id": "68f288c7ae4777ebbae58d6ba051feb3a486370b",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDBfXgOxAdQKoQV\nB5h3yjVmkZG8pmaF19aqIsJxJ2HhaIMZrEelcMfr6tKxOC2Yb1+E/Z+KYSuMGEpD\nuULg/VBHrZfj5zT8vicXoX8sq8fYzvUPIjLuuew4M86QT4y3kZWOkv1rVorDw72n\n0ptE4kRWAHB/+/SGY4rfT4XSWjcGnTzr4EeCLPM7RwvQduLpMni8kkjB1OIWhRK5\n4W/xIxbNOcOTx3zIcab0z+QiO8YZ1HL/I8yKvghqvQyQm3Q4UZDxa0VEKwOnJEdC\nD3IoG4VpdVBnqNePruEqGZRfz3WQS+OIQ5NGibTdxe4H2o1epXs1eGjsu1rHOHw9\nE1QhDCNTAgMBAAECggEAAVusGA5wLrPdsXgYLd8ReOLUrwpL9eyJ6S/NRZYNLdPZ\n97gp2JNuE83WJMBMMaG2fex5zjLYZ2dUPh1yxrmAcsBZLJRW3t9GzvenON0Lzg3F\n0pFe4iYT7mEOthyY1EEFV7bYaIR2/ODG2AK2bElaSXA/Weae1MKmGuMoAU34zOcS\nfl6YtIIHnB4+0bNxlG5g5IU9bnuq6cahjOWfDae1d5bR53ZPUbOwV6x85mxcpeXF\nj1HATQv9eUERSlsENt+zxGR1WKalUoI70OWFnkXVKEEW96VdP7KvxNF6ckD8u5mK\n1Kn59tdb4FWmB07mP9TmgPjDb5Ogpuxb5KVLVR4U4QKBgQD2jz5pHDg/uZm0cRXD\nERf/ein8Uejpo9y8UclcC2SNu+zgqoyGt1yIaFRgL/onolvsC+UKiHkUvf8jPtbH\n+xcS59U3bLy3e5FPWaTE4/0jWFhkJjY6FpriFCf7mX+xjvLw8s+KKMk5A/cmNgTu\nO3gcB+3LDxC2pK8VWMwnhcjtnwKBgQDI5gsCg5lduEv8IgQHbUZCOFDzjD/I5Y3/\n2hXhGaIVs6UZSw8eITeZVpgimrySFC0kZSi1Uj8Y02WtiT/nSqGmDemtgJ4sXMuN\ii0sRGydAoGHrB2GnvUgwKiLkTNj9PNrym4e7AqoiwvLvUiC54vLNtqHam5o1kmB\nC6/P/qZFzQKBgDz7/UHeWwNYEu6QsgNHrRnhy5S/Zc60WxqxWA7OOpbcDqEbThrc\nK6UJuST5ePRosjfWUVajnt9Eh2DeYB2iu3hPo2tMF/mCNNTdpWWVxr0BUwuib/M6\nOCEHP0R6GR1/8BMs26yenfbeRjlLTzjluLWmOGjrVwT2AuBS0FxOOP6dAoGATdTB\nwzGUwzhZR88t3Gq7Y4BJ7HETbRNyFgM5osG5h8rXVZs8uiGIVsGzowRrtfRXINiI\nEudQRp/vrnGT7ll9ksWlGHDR1sIEoks8AQBpS9Lit9s4fSUsNootQhT44erOO55r\nV1N/NZjY8w/b/csS36Hau8fCCp+qTnJmpKA1bqkCgYEAqpU36CpvvMhx9CEJ76MX\n2q+hpwcWd75+BM37DolPqLm3Lj2GwkR7Z5ZG300eWAel2n4b+tpQfR+JTRyYvtTH\ntpWlhwh4f/Ua8fcogVKh4d+u51DdXpaumkRFCc1JeTHcb3S7EZou9vfnCavkQKNm\nGHcf+EDRprnny0h+s5o0csw=\n-----END PRIVATE KEY-----\n".replace('\\n', '\n'),
  "client_email": "firebase-adminsdk-fbsvc@py-tt-75784.iam.gserviceaccount.com",
  "client_id": "115744384158435013507",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/metadata/x509/firebase-adminsdk-fbsvc%40py-tt-75784.iam.gserviceaccount.com",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40py-tt-75784.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

if not firebase_admin._apps:
    cred = credentials.Certificate(cert_dict)
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://py-tt-75784-default-rtdb.firebaseio.com/'})

# ৩. ফ্ল্যাস্ক রাউটস
@app.route('/')
def index(): return render_template_string(HTML_UI)

@app.route('/api/set_command', methods=['POST'])
def set_command():
    data = request.json
    db.reference('bot_control').update({
        'user': data['user'], 'pass': data['pass'], 'message': data['message'],
        'command': 'start', 'login_status': 'Bot received command'
    })
    return jsonify(success=True)

@app.route('/api/get_status')
def get_status():
    s = db.reference('bot_control/login_status').get()
    return jsonify(status=s or "Ready")

# ৪. টিকটক অটোমেশন
def run_bot(u, p, msg):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(5)
        driver.find_element(By.NAME, "username").send_keys(u)
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(p)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(15)
        driver.get("https://www.tiktok.com/messages")
        time.sleep(10)
        # অটো রিপ্লাই লজিক
        chat = driver.find_element(By.XPATH, "//div[@data-e2e='message-item']")
        chat.click()
        time.sleep(2)
        box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
        box.send_keys(msg)
        box.send_keys(Keys.ENTER)
        return "Success: Logged in & Reply Sent"
    except Exception as e: return f"Error: {str(e)}"
    finally:
        try: driver.quit()
        except: pass

# ৫. ব্যাকগ্রাউন্ড মনিটর
def bot_monitor():
    while True:
        try:
            ref = db.reference('bot_control')
            data = ref.get()
            if data and data.get('command') == 'start':
                res = run_bot(data['user'], data['pass'], data['message'])
                ref.update({'login_status': res, 'command': 'idle'})
        except: pass
        time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=bot_monitor, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

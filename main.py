import time
import os
import threading
import firebase_admin
from firebase_admin import credentials, db
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask

# ১. ফ্লাস্ক সার্ভার (Render-এ অ্যাপটি সজাগ রাখার জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "TikTok Bot is Running!"

def run_flask():
    # Render সাধারণত ১০০০০ পোর্ট ব্যবহার করে
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ২. ফায়ারবেস ডিকশনারি সেটআপ (আপনার দেওয়া তথ্য অনুযায়ী)
cert_dict = {
  "type": "service_account",
  "project_id": "py-tt-75784",
  "private_key_id": "68f288c7ae4777ebbae58d6ba051feb3a486370b",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDBfXgOxAdQKoQV\nB5h3yjVmkZG8pmaF19aqIsJxJ2HhaIMZrEelcMfr6tKxOC2Yb1+E/Z+KYSuMGEpD\nuULg/VBHrZfj5zT8vicXoX8sq8fYzvUPIjLuuew4M86QT4y3kZWOkv1rVorDw72n\n0ptE4kRWAHB/+/SGY4rfT4XSWjcGnTzr4EeCLPM7RwvQduLpMni8kkjB1OIWhRK5\n4W/xIxbNOcOTx3zIcab0z+QiO8YZ1HL/I8yKvghqvQyQm3Q4UZDxa0VEKwOnJEdC\nD3IoG4VpdVBnqNePruEqGZRfz3WQS+OIQ5NGibTdxe4H2o1epXs1eGjsu1rHOHw9\nE1QhDCNTAgMBAAECggEAAVusGA5wLrPdsXgYLd8ReOLUrwpL9eyJ6S/NRZYNLdPZ\n97gp2JNuE83WJMBMMaG2fex5zjLYZ2dUPh1yxrmAcsBZLJRW3t9GzvenON0Lzg3F\n0pFe4iYT7mEOthyY1EEFV7bYaIR2/ODG2AK2bElaSXA/Weae1MKmGuMoAU34zOcS\nfl6YtIIHnB4+0bNxlG5g5IU9bnuq6cahjOWfDae1d5bR53ZPUbOwV6x85mxcpeXF\nj1HATQv9eUERSlsENt+zxGR1WKalUoI70OWFnkXVKEEW96VdP7KvxNF6ckD8u5mK\n1Kn59tdb4FWmB07mP9TmgPjDb5Ogpuxb5KVLVR4U4QKBgQD2jz5pHDg/uZm0cRXD\nERf/ein8Uejpo9y8UclcC2SNu+zgqoyGt1yIaFRgL/onolvsC+UKiHkUvf8jPtbH\n+xcS59U3bLy3e5FPWaTE4/0jWFhkJjY6FpriFCf7mX+xjvLw8s+KKMk5A/cmNgTu\nO3gcB+3LDxC2pK8VWMwnhcjtnwKBgQDI5gsCg5lduEv8IgQHbUZCOFDzjD/I5Y3/\n2hXhGaIVs6UZSw8eITeZVpgimrySFC0kZSi1Uj8Y02WtiT/nSqGmDemtgJ4sXMuN\nii0sRGydAoGHrB2GnvUgwKiLkTNj9PNrym4e7AqoiwvLvUiC54vLNtqHam5o1kmB\nC6/P/qZFzQKBgDz7/UHeWwNYEu6QsgNHrRnhy5S/Zc60WxqxWA7OOpbcDqEbThrc\nK6UJuST5ePRosjfWUVajnt9Eh2DeYB2iu3hPo2tMF/mCNNTdpWWVxr0BUwuib/M6\nOCEHP0R6GR1/8BMs26yenfbeRjlLTzjluLWmOGjrVwT2AuBS0FxOOP6dAoGATdTB\nwzGUwzhZR88t3Gq7Y4BJ7HETbRNyFgM5osG5h8rXVZs8uiGIVsGzowRrtfRXINiI\nEudQRp/vrnGT7ll9ksWlGHDR1sIEoks8AQBpS9Lit9s4fSUsNootQhT44erOO55r\nV1N/NZjY8w/b/csS36Hau8fCCp+qTnJmpKA1bqkCgYEAqpU36CpvvMhx9CEJ76MX\n2q+hpwcWd75+BM37DolPqLm3Lj2GwkR7Z5ZG300eWAel2n4b+tpQfR+JTRyYvtTH\ntpWlhwh4f/Ua8fcogVKh4d+u51DdXpaumkRFCc1JeTHcb3S7EZou9vfnCavkQKNm\nGHcf+EDRprnny0h+s5o0csw=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@py-tt-75784.iam.gserviceaccount.com",
  "client_id": "115744384158435013507",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/栄.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40py-tt-75784.iam.gserviceaccount.com",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40py-tt-75784.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# ফায়ারবেস ইনিশিয়ালাইজেশন
if not firebase_admin._apps:
    cred = credentials.Certificate(cert_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://py-tt-75784-default-rtdb.firebaseio.com/'
    })

# ৩. টিকটক অটোমেশন ফাংশন
def run_tiktok_bot(username, password):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless') # Render/Replit এর জন্য মাস্ট
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(5)
        
        # লগইন ইনপুট
        driver.find_element("name", "username").send_keys(username)
        driver.find_element("xpath", "//input[@type='password']").send_keys(password)
        driver.find_element("xpath", "//button[@type='submit']").click()
        
        # লগইন হওয়ার জন্য অপেক্ষা
        time.sleep(20) 
        
        if "messages" in driver.current_url or "foryou" in driver.current_url:
            return "Success"
        else:
            return "Failed: Captcha or Wrong Credentials"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        driver.quit()

# ৪. মেইন লুপ (অ্যাডমিন প্যানেল মনিটর করার জন্য)
def monitor_commands():
    print("Bot is listening for commands from py-tt-75784...")
    while True:
        try:
            ref = db.reference('bot_control')
            data = ref.get()

            if data and data.get('command') == 'start':
                u = data.get('user')
                p = data.get('pass')
                
                print(f"Command received for: {u}")
                ref.update({'login_status': 'Processing...'})
                
                result = run_tiktok_bot(u, p)
                
                # রেজাল্ট আপডেট
                ref.update({
                    'login_status': result,
                    'command': 'idle'
                })
        except Exception as e:
            print(f"DB Error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    # ফ্লাস্ক থ্রেড চালু করা (Render-এর জন্য)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # বটের কাজ শুরু করা
    monitor_commands()

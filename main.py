import time
import os
import json
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

# --- কনফিগারেশন সেকশন ---
# লাইন ১২: আপনার টিকটক ইউজারনেম এখানে দিন
TIKTOK_USER = "@s574028" 

# লাইন ১৫: আপনার টিকটক পাসওয়ার্ড এখানে দিন
TIKTOK_PASS = "Tamim@4372" 

# লাইন ১৮: আপনার ট্রেইনিং ফাইলের নাম (যদি পরিবর্তন করেন)
DB_FILE = "database.json"
# -----------------------

def load_train_data():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {DB_FILE}: {e}")
        return {}

@app.route('/')
def home():
    return "<h1>TikTok Bot is Running!</h1><p>Status: Monitoring Messages...</p>"

def run_tiktok_bot():
    print(">>> Bot started...")
    options = Options()
    options.add_argument('--headless') # সার্ভারে চালানোর জন্য এটি জরুরি
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # লগইন পেজে যাওয়া
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(5)
        
        # লগইন ইনপুট
        print(">>> Logging in...")
        driver.find_element(By.NAME, "username").send_keys(TIKTOK_USER)
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(TIKTOK_PASS)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # লগইন হওয়ার জন্য পর্যাপ্ত সময় (ক্যাপচা আসলে এখানে ম্যানুয়ালি হ্যান্ডেল করতে হয়)
        time.sleep(20) 

        while True:
            print(">>> Checking for new messages...")
            driver.get("https://www.tiktok.com/messages")
            time.sleep(10)
            
            # ট্রেইনড ডাটা লোড করা
            replies = load_train_data()
            
            # মেসেজ লিস্ট থেকে চ্যাটগুলো খুঁজে বের করা
            chats = driver.find_elements(By.XPATH, "//div[@data-e2e='message-item']")
            
            for chat in chats[:3]: # শুধু প্রথম ৩টি চ্যাট চেক করবে প্রতিবার
                try:
                    chat.click()
                    time.sleep(3)
                    
                    # শেষ মেসেজটি পড়া
                    msg_elements = driver.find_elements(By.XPATH, "//div[@data-e2e='message-text']")
                    if msg_elements:
                        incoming_msg = msg_elements[-1].text.lower().strip()
                        print(f"User said: {incoming_msg}")

                        # ডাটাবেসে উত্তর আছে কি না চেক করা
                        if incoming_msg in replies:
                            reply_text = replies[incoming_msg]
                            
                            # রিপ্লাই টাইপ করে পাঠানো
                            input_box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                            input_box.send_keys(reply_text)
                            input_box.send_keys(Keys.ENTER)
                            print(f"Replied: {reply_text}")
                            time.sleep(2)
                except Exception as e:
                    continue
            
            # প্রতি ৩০ সেকেন্ড পর পর চেক করবে
            time.sleep(30)

    except Exception as e:
        print(f"Bot Stopped. Error: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    # বটকে আলাদা থ্রেডে চালানো যেন Flask সার্ভার ব্লক না হয়
    threading.Thread(target=run_tiktok_bot, daemon=True).start()
    
    # Render এর জন্য Flask রান করা
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

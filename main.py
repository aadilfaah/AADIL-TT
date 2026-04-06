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

# --- আপনার ল্যাপটপ থেকে পাওয়া Session ID ---
MY_SESSION_ID = "E1334f1033768fe012b39c19888b29ff"
# ------------------------------------------

@app.route('/')
def home():
    return "<h1>ADIL-TT Bot is Online!</h1><p>Status: Logged in with Session ID</p>"

def run_tiktok_bot():
    print(">>> Bot is starting...")
    options = Options()
    options.add_argument('--headless') # Render-এ চালানোর জন্য জরুরি
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # ১. প্রথমে টিকটক সাইটে যেতে হবে যেন কুকি অ্যাড করা যায়
        driver.get("https://www.tiktok.com")
        time.sleep(5)

        # ২. সেশন আইডি কুকি ইনজেক্ট করা
        driver.add_cookie({
            'name': 'sessionid',
            'value': MY_SESSION_ID,
            'domain': '.tiktok.com',
            'path': '/',
            'secure': True,
            'httpOnly': True
        })
        
        print(">>> Session Injected! Refreshing page...")
        driver.refresh()
        time.sleep(10)

        # ৩. মেসেজ চেক করার লুপ
        while True:
            print(">>> Checking for new messages...")
            driver.get("https://www.tiktok.com/messages")
            time.sleep(15)
            
            # database.json থেকে রিপ্লাই ডাটা লোড করা
            try:
                if os.path.exists('database.json'):
                    with open('database.json', 'r', encoding='utf-8') as f:
                        replies = json.load(f)
                else:
                    replies = {}
            except Exception as e:
                print(f"JSON Load Error: {e}")
                replies = {}

            # চ্যাট আইটেমগুলো খুঁজে বের করা
            chats = driver.find_elements(By.XPATH, "//div[contains(@class, 'DivThreadItem')]")
            
            for chat in chats[:3]: # শুধু প্রথম ৩টি চ্যাট চেক করবে
                try:
                    chat.click()
                    time.sleep(3)
                    
                    # শেষ মেসেজটি পড়া
                    msg_elements = driver.find_elements(By.XPATH, "//div[@data-e2e='message-text']")
                    if msg_elements:
                        incoming_msg = msg_elements[-1].text.lower().strip()
                        print(f"Received: {incoming_msg}")

                        # ডাটাবেসে উত্তর আছে কি না চেক করা
                        if incoming_msg in replies:
                            reply_text = replies[incoming_msg]
                            
                            # রিপ্লাই টাইপ করে পাঠানো
                            input_box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                            input_box.send_keys(reply_text)
                            time.sleep(1)
                            input_box.send_keys(Keys.ENTER)
                            print(f"Replied: {reply_text}")
                except Exception as e:
                    print(f"Chat processing error: {e}")
                    continue
            
            # প্রতি ৪৫ সেকেন্ড পর পর ইনবক্স রিফ্রেশ করবে
            time.sleep(45)

    except Exception as e:
        print(f"Major Error: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    # বটকে ব্যাকগ্রাউন্ড থ্রেডে চালানো
    threading.Thread(target=run_tiktok_bot, daemon=True).start()
    
    # Render-এর জন্য Flask সার্ভার চালু করা
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

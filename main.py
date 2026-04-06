import time
import os
import json
import threading
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

# ১. ফাইল থেকে ট্রেইনড ডাটা লোড করা
def load_replies():
    try:
        with open('replies.json', 'r') as f:
            return json.load(f)
    except:
        return {"default": "Hello! I am busy right now."}

# ২. ফ্ল্যাস্ক ওয়েবসাইট (রেন্ডার সজাগ রাখার জন্য)
@app.route('/')
def home():
    return "<h1>TikTok Auto-Reply Bot is Live!</h1><p>Running from replies.json</p>"

# ৩. টিকটক অটোমেশন লজিক
def run_tiktok_bot():
    print(">>> Bot started checking messages...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # আপনার ইউজারনেম ও পাসওয়ার্ড এখানে দিয়ে দিন অথবা Environment Variable ব্যবহার করুন
    u = "YOUR_USERNAME" 
    p = "YOUR_PASSWORD"
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(5)
        
        # লগইন
        driver.find_element(By.NAME, "username").send_keys(u)
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(p)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(20) # লগইন ও ক্যাপচার জন্য সময়

        while True:
            driver.get("https://www.tiktok.com/messages")
            time.sleep(10)
            
            # মেসেজ লিস্ট থেকে নতুন মেসেজ চেক করা
            chats = driver.find_elements(By.XPATH, "//div[@data-e2e='message-item']")
            replies_data = load_replies()

            for chat in chats[:5]: # প্রথম ৫টি চ্যাট চেক করবে
                chat.click()
                time.sleep(3)
                
                # শেষ আসা মেসেজটি পড়ার চেষ্টা
                try:
                    last_msg_elements = driver.find_elements(By.XPATH, "//div[@data-e2e='message-text']")
                    if last_msg_elements:
                        received_text = last_msg_elements[-1].text.lower().strip()
                        print(f"Received: {received_text}")

                        # replies.json এ উত্তর আছে কি না চেক করা
                        reply_to_send = replies_data.get(received_text, "Default Reply: Thank you for messaging!")

                        # উত্তর টাইপ করা ও পাঠানো
                        input_box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                        input_box.send_keys(reply_to_send)
                        input_box.send_keys(Keys.ENTER)
                        print(f"Replied with: {reply_to_send}")
                except Exception as e:
                    print(f"Chat error: {e}")
            
            time.sleep(30) # প্রতি ৩০ সেকেন্ড পর পর নতুন মেসেজ চেক করবে

    except Exception as e:
        print(f"Major Error: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে বট চালানো
    threading.Thread(target=run_tiktok_bot, daemon=True).start()
    
    # ফ্ল্যাস্ক সার্ভার
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

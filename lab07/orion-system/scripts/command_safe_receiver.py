#!/usr/bin/env python3
import socketserver, os, re, hmac, hashlib, random
from datetime import datetime

PORT     = 6005
REPORTS  = os.path.join(os.path.dirname(__file__), '..', 'reports')
LOG      = os.path.join(REPORTS, 'command_safety_gate.log')
STATE    = os.path.join(REPORTS, 'processed_commands.db')
PENDING  = os.path.join(REPORTS, 'pending_commands.db')
DB       = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'user_db.txt')
ALLOWED  = {'operator': {'SET_MODE_NOMINAL', 'SET_MODE_SAFE'},
            'admin':    {'SET_MODE_NOMINAL', 'SET_MODE_SAFE', 'RESET', 'SHUTDOWN'}}
CRITICAL = {'RESET', 'SHUTDOWN'}

def load_users():
    u = {}
    for line in open(DB):
        p = line.strip().split(':')
        if len(p) == 3: u[p[0]] = {'role': p[1], 'token': p[2]}
    return u

def load_pending():
    p = {}
    if not os.path.exists(PENDING): return p
    for line in open(PENDING):
        parts = line.strip().split(':', 3)
        if len(parts) == 4: p[parts[0]] = {'user': parts[1], 'role': parts[2], 'cmd': parts[3]}
    return p

def save_pending(p):
    with open(PENDING, 'w') as f:
        for rid, e in p.items(): f.write(f"{rid}:{e['user']}:{e['role']}:{e['cmd']}\n")

def field(line, key):
    m = re.search(rf'{key}=([^;]+)', line)
    return m.group(1) if m else ''

def log(msg):
    open(LOG, 'a').write(msg + '\n')

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        db = load_users()
        for raw in self.rfile:
            line = raw.decode().strip()
            if not line: continue
            now    = datetime.now().astimezone().isoformat(timespec='seconds')
            user   = field(line, 'USER'); role = field(line, 'ROLE'); cmd = field(line, 'CMD')
            cid    = field(line, 'COMMAND_ID'); ts = field(line, 'TIMESTAMP'); auth = field(line, 'AUTH')
            req_id = field(line, 'REQUEST_ID')
            print(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd}')
            log(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            if user not in db:
                print(f'[REJECTED] UNKNOWN USER: {user}'); log(f'[REJECTED] UNKNOWN USER: {user} RAW={line}'); continue
            u = db[user]
            if role != u['role']:
                print(f'[REJECTED] ROLE MISMATCH: {user}'); log(f'[REJECTED] ROLE MISMATCH: {user} RAW={line}'); continue
            data = (f'USER={user};ROLE={role};CMD={cmd};REQUEST_ID={req_id};COMMAND_ID={cid};TIMESTAMP={ts}'
                    if req_id else f'USER={user};ROLE={role};CMD={cmd};COMMAND_ID={cid};TIMESTAMP={ts}')
            exp = hmac.new(u['token'].encode(), data.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(auth, exp):
                print(f'[REJECTED] INVALID AUTH: {user}'); log(f'[REJECTED] INVALID AUTH: {user} RAW={line}'); continue
            seen = set(open(STATE).read().splitlines()) if os.path.exists(STATE) else set()
            if cid in seen:
                print(f'[REJECTED] REPLAY: {cid}'); log(f'[REJECTED] REPLAY: {cid} RAW={line}'); continue
            open(STATE, 'a').write(cid + '\n')
            if cmd == 'CONFIRM':
                if role != 'admin':
                    print(f'[REJECTED] INSUFFICIENT ROLE FOR CONFIRM: {user}'); log(f'[REJECTED] CONFIRM ROLE: {user} RAW={line}'); continue
                pending = load_pending()
                if req_id not in pending:
                    print(f'[REJECTED] UNKNOWN REQUEST_ID={req_id}'); log(f'[REJECTED] UNKNOWN REQUEST_ID={req_id}'); continue
                stored = pending.pop(req_id)['cmd']
                save_pending(pending)
                print(f'[CONFIRMED] EXECUTING REQUEST_ID={req_id} CMD={stored}')
                log(f'[CONFIRMED {now}] REQUEST_ID={req_id} CMD={stored}')
                print(); continue
            if cmd not in ALLOWED.get(role, set()):
                print(f'[REJECTED] UNAUTHORIZED: {user} CMD={cmd}'); log(f'[REJECTED] UNAUTHORIZED: {user} CMD={cmd} RAW={line}'); continue
            if cmd in CRITICAL:
                rid = f'REQ-{datetime.now().strftime("%Y%m%d%H%M%S")}-{random.randint(1000,9999)}'
                pending = load_pending(); pending[rid] = {'user': user, 'role': role, 'cmd': cmd}; save_pending(pending)
                print(f'[PENDING] CRITICAL CMD REQUIRES CONFIRMATION REQUEST_ID={rid}')
                log(f'[PENDING {now}] USER={user} CMD={cmd} REQUEST_ID={rid}')
                print(); continue
            print(f'[AUTHORIZED] USER={user} ROLE={role} CMD={cmd}')
            log(f'[AUTHORIZED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            print()

class Server(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    for p in (LOG, STATE, PENDING): open(p, 'w').close()
    print(f'Listening on 127.0.0.1:{PORT}')
    with Server(('127.0.0.1', PORT), Handler) as s: s.serve_forever()

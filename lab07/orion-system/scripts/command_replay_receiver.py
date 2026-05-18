#!/usr/bin/env python3
import socketserver, os, re, hmac, hashlib
from datetime import datetime

PORT    = 6004
REPORTS = os.path.join(os.path.dirname(__file__), '..', 'reports')
LOG     = os.path.join(REPORTS, 'command_replay_protection.log')
STATE   = os.path.join(REPORTS, 'processed_commands.db')
DB      = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'user_db.txt')
ALLOWED = {'operator': {'SET_MODE_NOMINAL', 'SET_MODE_SAFE'},
           'admin':    {'SET_MODE_NOMINAL', 'SET_MODE_SAFE', 'RESET', 'SHUTDOWN'}}

def load_users():
    u = {}
    for line in open(DB):
        p = line.strip().split(':')
        if len(p) == 3: u[p[0]] = {'role': p[1], 'token': p[2]}
    return u

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
            now  = datetime.now().astimezone().isoformat(timespec='seconds')
            user = field(line, 'USER'); role = field(line, 'ROLE'); cmd = field(line, 'CMD')
            cid  = field(line, 'COMMAND_ID'); ts = field(line, 'TIMESTAMP'); auth = field(line, 'AUTH')
            print(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd}')
            log(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            if user not in db:
                print(f'[REJECTED] UNKNOWN USER: {user}'); log(f'[REJECTED] UNKNOWN USER: {user} RAW={line}'); continue
            u = db[user]
            if role != u['role']:
                print(f'[REJECTED] ROLE MISMATCH: {user}'); log(f'[REJECTED] ROLE MISMATCH: {user} RAW={line}'); continue
            data = f'USER={user};ROLE={role};CMD={cmd};COMMAND_ID={cid};TIMESTAMP={ts}'
            exp  = hmac.new(u['token'].encode(), data.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(auth, exp):
                print(f'[REJECTED] INVALID AUTH: {user}'); log(f'[REJECTED] INVALID AUTH: {user} RAW={line}'); continue
            seen = set(open(STATE).read().splitlines()) if os.path.exists(STATE) else set()
            if cid in seen:
                print(f'[REJECTED] REPLAY: {cid}'); log(f'[REJECTED] REPLAY: {cid} RAW={line}'); continue
            open(STATE, 'a').write(cid + '\n')
            if cmd not in ALLOWED.get(role, set()):
                print(f'[REJECTED] UNAUTHORIZED: {user} CMD={cmd}'); log(f'[REJECTED] UNAUTHORIZED: {user} CMD={cmd} RAW={line}'); continue
            print(f'[AUTHORIZED] USER={user} ROLE={role} CMD={cmd}')
            log(f'[AUTHORIZED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            print()

class Server(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    open(LOG, 'w').close(); open(STATE, 'w').close()
    print(f'Listening on 127.0.0.1:{PORT}')
    with Server(('127.0.0.1', PORT), Handler) as s: s.serve_forever()

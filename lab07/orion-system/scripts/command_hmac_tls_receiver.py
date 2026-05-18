#!/usr/bin/env python3
import socketserver, ssl, os, re, hmac, hashlib
from datetime import datetime

PORT    = 7005
REPORTS = os.path.join(os.path.dirname(__file__), '..', 'reports')
LOG     = os.path.join(REPORTS, 'command_hmac_authentication.log')
DB      = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'user_db.txt')
CERT    = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'tls', 'orion.pem')
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
            ts   = field(line, 'TIMESTAMP'); auth = field(line, 'AUTH')
            print(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd}')
            log(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            if user not in db:
                print(f'[REJECTED] UNKNOWN USER: {user}'); log(f'[REJECTED] UNKNOWN USER: {user} RAW={line}'); continue
            u = db[user]
            if role != u['role']:
                print(f'[REJECTED] ROLE MISMATCH: {user}'); log(f'[REJECTED] ROLE MISMATCH: {user} RAW={line}'); continue
            data = f'USER={user};ROLE={role};CMD={cmd};TIMESTAMP={ts}'
            exp  = hmac.new(u['token'].encode(), data.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(auth, exp):
                print(f'[REJECTED] INVALID AUTH: {user}'); log(f'[REJECTED] INVALID AUTH: {user} RAW={line}'); continue
            if cmd not in ALLOWED.get(role, set()):
                print(f'[REJECTED] UNAUTHORIZED: {user} CMD={cmd}'); log(f'[REJECTED] UNAUTHORIZED: {user} CMD={cmd} RAW={line}'); continue
            print(f'[AUTHORIZED] USER={user} ROLE={role} CMD={cmd}')
            log(f'[AUTHORIZED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            print()

class TLSServer(socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, addr, handler):
        super().__init__(addr, handler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(CERT)
        self._ctx = ctx
    def get_request(self):
        conn, addr = self.socket.accept()
        return self._ctx.wrap_socket(conn, server_side=True), addr
    def handle_error(self, req, addr):
        import sys as _sys
        if not isinstance(_sys.exc_info()[1], (BrokenPipeError, ssl.SSLError, ConnectionResetError)):
            super().handle_error(req, addr)

if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    open(LOG, 'w').close()
    print(f'Listening on 127.0.0.1:{PORT} (TLS)')
    with TLSServer(('127.0.0.1', PORT), Handler) as s: s.serve_forever()

#!/usr/bin/env python3
import socketserver
import os
import re
import hmac
import hashlib
from datetime import datetime

PORT = 6003
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
LOG_FILE = os.path.join(REPORT_DIR, 'command_hmac_authentication.log')
USER_DB = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'user_db.txt')

ALLOWED_CMDS = {
    'operator': {'SET_MODE_NOMINAL', 'SET_MODE_SAFE'},
    'admin':    {'SET_MODE_NOMINAL', 'SET_MODE_SAFE', 'RESET', 'SHUTDOWN'},
}


def load_user_db():
    users = {}
    try:
        with open(USER_DB) as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(':')
                    if len(parts) == 3:
                        users[parts[0]] = {'role': parts[1], 'token': parts[2]}
    except FileNotFoundError:
        pass
    return users


def parse_field(line, field):
    m = re.search(rf'{field}=([^;]+)', line)
    return m.group(1) if m else ''


def compute_hmac(data, token):
    return hmac.new(token.encode(), data.encode(), hashlib.sha256).hexdigest()


def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')


def execute_cmd(cmd, ts):
    actions = {
        'SET_MODE_NOMINAL': 'Switching satellite mode to NOMINAL',
        'SET_MODE_SAFE':    'Switching satellite mode to SAFE',
        'RESET':            'Simulated satellite reset',
        'SHUTDOWN':         'Simulated satellite shutdown',
    }
    msg = f'[ACTION] {actions.get(cmd, f"Unknown: {cmd}")}'
    print(msg)
    log(f'[ACTION {ts}] {cmd}')


class HMACCommandHandler(socketserver.StreamRequestHandler):
    def handle(self):
        users = load_user_db()
        for raw in self.rfile:
            line = raw.decode().strip()
            if not line:
                continue
            ts        = datetime.now().astimezone().isoformat(timespec='seconds')
            user      = parse_field(line, 'USER')
            role      = parse_field(line, 'ROLE')
            cmd       = parse_field(line, 'CMD')
            timestamp = parse_field(line, 'TIMESTAMP')
            recv_auth = parse_field(line, 'AUTH')
            print(f'[RECEIVED {ts}] USER={user} ROLE={role} CMD={cmd}')
            log(f'[RECEIVED {ts}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            if user not in users:
                msg = f'[REJECTED] UNKNOWN USER: {user}'
                print(msg); log(f'{msg} RAW={line}'); print(); continue
            db = users[user]
            if role != db['role']:
                msg = f'[REJECTED] ROLE MISMATCH: USER={user} DECLARED_ROLE={role} EXPECTED_ROLE={db["role"]}'
                print(msg); log(f'[REJECTED] ROLE MISMATCH: USER={user} RAW={line}'); print(); continue
            data = f'USER={user};ROLE={role};CMD={cmd};TIMESTAMP={timestamp}'
            if not hmac.compare_digest(recv_auth, compute_hmac(data, db['token'])):
                msg = f'[REJECTED] INVALID AUTH: {user}'
                print(msg); log(f'{msg} RAW={line}'); print(); continue
            allowed = ALLOWED_CMDS.get(role, set())
            if cmd not in allowed:
                msg = f'[REJECTED] UNAUTHORIZED USER={user} ROLE={role} CMD={cmd}'
                print(msg); log(f'{msg} RAW={line}'); print(); continue
            print(f'[AUTHORIZED] USER={user} ROLE={role} CMD={cmd}')
            log(f'[AUTHORIZED {ts}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            execute_cmd(cmd, ts)
            print()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == '__main__':
    os.makedirs(REPORT_DIR, exist_ok=True)
    open(LOG_FILE, 'a').close()
    print(f'=== HMAC COMMAND RECEIVER STARTED ===\nListening on 127.0.0.1:{PORT}\n')
    with ReusableTCPServer(('127.0.0.1', PORT), HMACCommandHandler) as server:
        server.serve_forever()

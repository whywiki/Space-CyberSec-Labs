#!/usr/bin/env python3
import socketserver, os, re
from datetime import datetime

PORT    = 6001
REPORTS = os.path.join(os.path.dirname(__file__), '..', 'reports')
LOG     = os.path.join(REPORTS, 'command_authorization.log')
ALLOWED = {'operator': {'SET_MODE_NOMINAL', 'SET_MODE_SAFE'},
           'admin':    {'SET_MODE_NOMINAL', 'SET_MODE_SAFE', 'RESET', 'SHUTDOWN'}}
ACTIONS = {'SET_MODE_NOMINAL': 'Switching satellite mode to NOMINAL',
           'SET_MODE_SAFE':    'Switching satellite mode to SAFE',
           'RESET':            'Simulated satellite reset',
           'SHUTDOWN':         'Simulated satellite shutdown'}

def field(line, key):
    m = re.search(rf'{key}=([^;]+)', line)
    return m.group(1) if m else ''

def log(msg):
    open(LOG, 'a').write(msg + '\n')

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        for raw in self.rfile:
            line = raw.decode().strip()
            if not line: continue
            now  = datetime.now().astimezone().isoformat(timespec='seconds')
            user = field(line, 'USER'); role = field(line, 'ROLE'); cmd = field(line, 'CMD')
            ts   = field(line, 'TIMESTAMP')
            print(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd}')
            log(f'[RECEIVED {now}] USER={user} ROLE={role} CMD={cmd} MSG_TS={ts} RAW={line}')
            if cmd not in ALLOWED.get(role, set()):
                print(f'[REJECTED {now}] UNAUTHORIZED USER={user} ROLE={role} CMD={cmd}')
                log(f'[REJECTED {now}] UNAUTHORIZED USER={user} ROLE={role} CMD={cmd} RAW={line}')
                print(); continue
            print(f'[AUTHORIZED {now}] USER={user} ROLE={role} CMD={cmd}')
            log(f'[AUTHORIZED {now}] USER={user} ROLE={role} CMD={cmd} RAW={line}')
            print(f'[ACTION] {ACTIONS[cmd]}')
            log(f'[ACTION {now}] {cmd}')
            print()

class Server(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    open(LOG, 'w').close()
    print(f'=== AUTHORIZED COMMAND RECEIVER STARTED ===\nListening on 127.0.0.1:{PORT}\n')
    with Server(('127.0.0.1', PORT), Handler) as s: s.serve_forever()

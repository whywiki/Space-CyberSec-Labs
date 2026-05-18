#!/usr/bin/env python3
import socketserver, os, re
from datetime import datetime

PORT    = 6000
REPORTS = os.path.join(os.path.dirname(__file__), '..', 'reports')
LOG     = os.path.join(REPORTS, 'command_channel.log')
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
            if cmd in ACTIONS:
                print(f'[ACTION] {ACTIONS[cmd]}')
                log(f'[ACTION {now}] {cmd}')
            else:
                print(f'[UNKNOWN COMMAND] {cmd}')
                log(f'[UNKNOWN {now}] RAW={line}')
            print()

class Server(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    open(LOG, 'w').close()
    print(f'=== INSECURE COMMAND RECEIVER STARTED ===\nListening on 127.0.0.1:{PORT}\n')
    with Server(('127.0.0.1', PORT), Handler) as s: s.serve_forever()

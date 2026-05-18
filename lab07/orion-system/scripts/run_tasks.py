#!/usr/bin/env python3
import subprocess, threading, time, os, sys, hmac, hashlib, random, socket, ssl, signal
from datetime import datetime

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SCRIPTS)
REPORTS = os.path.join(ROOT, 'reports')

def ts():
    return datetime.now().astimezone().isoformat(timespec='seconds')

def start(cmd):
    env = {**os.environ, 'PYTHONUNBUFFERED': '1'}
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, env=env, start_new_session=True)
    threading.Thread(target=lambda: [sys.stdout.write(l) or sys.stdout.flush() for l in p.stdout], daemon=True).start()
    return p

def kill(p):
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    except Exception:
        p.terminate()
    try: p.wait(3)
    except: p.kill()
    time.sleep(0.3)

def free(port):
    subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True)
    time.sleep(0.5)

def wait_port(port, tls=False, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), 0.5) as s:
                if tls:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                    ctx.wrap_socket(s)
            return
        except: time.sleep(0.2)

def nc(msg, port):
    with socket.create_connection(('127.0.0.1', port)) as s:
        s.sendall((msg + '\n').encode())
    time.sleep(0.5)

def send_tls(msg, port):
    print(f'[SENDING TLS] {msg}')
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection(('127.0.0.1', port)) as raw:
        with ctx.wrap_socket(raw) as tls:
            tls.sendall((msg + '\n').encode())
    time.sleep(0.5)

def send(msg, port):
    print(f'[SENDING] {msg}')
    nc(msg, port)

def build_plain_hmac_msg(user, role, cmd):
    tokens = {'alice': 'token-alice-123', 'bob': 'token-bob-999'}
    token = tokens[user]
    data = f'USER={user};ROLE={role};CMD={cmd};TIMESTAMP={ts()}'
    auth = hmac.new(token.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f'{data};AUTH={auth}'

def build_hmac_msg(user, role, cmd, req_id=None):
    tokens = {'alice': 'token-alice-123', 'bob': 'token-bob-999'}
    token = tokens[user]
    cid = f"CMD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}"
    parts = [f'USER={user}', f'ROLE={role}', f'CMD={cmd}']
    if req_id: parts.append(f'REQUEST_ID={req_id}')
    parts += [f'COMMAND_ID={cid}', f'TIMESTAMP={ts()}']
    data = ';'.join(parts)
    auth = hmac.new(token.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f'{data};AUTH={auth}'

def wait_pending(timeout=3):
    pending = os.path.join(REPORTS, 'pending_commands.db')
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(pending):
            line = open(pending).readline().strip()
            if line: return line.split(':')[0]
        time.sleep(0.1)
    return None

def show_log(filename):
    time.sleep(0.4)
    print(f'\n$ cat ../reports/{filename}')
    path = os.path.join(REPORTS, filename)
    if os.path.exists(path): print(open(path).read())


TOKENS = {'alice': 'token-alice-123', 'bob': 'token-bob-999'}

def plain_msg(user, role, cmd):
    return f'USER={user};ROLE={role};CMD={cmd};TIMESTAMP={ts()}'

def token_msg(user, role, cmd):
    token = TOKENS.get(user, 'unknown')
    return f'USER={user};ROLE={role};CMD={cmd};TOKEN={token};TIMESTAMP={ts()}'


def task1():
    free(6000)
    open(os.path.join(REPORTS, 'command_channel.log'), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_insecure_receiver.py')])
    wait_port(6000); time.sleep(0.5)
    for user, role, cmd in [('alice','operator','SET_MODE_SAFE'), ('bob','operator','SET_MODE_NOMINAL'),
                             ('admin','admin','RESET'), ('admin','admin','SHUTDOWN'), ('eve','operator','DEPLOY_SOLAR_ARRAY')]:
        send(plain_msg(user, role, cmd), 6000)
    send(plain_msg('intruder', 'admin', 'SHUTDOWN'), 6000)
    kill(srv)
    show_log('command_channel.log')


def task2():
    free(6001)
    open(os.path.join(REPORTS, 'command_authorization.log'), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_authorized_receiver.py')])
    wait_port(6001); time.sleep(0.5)
    for user, role, cmd in [('alice','operator','SET_MODE_SAFE'), ('alice','operator','SET_MODE_NOMINAL'),
                             ('alice','operator','RESET'), ('alice','operator','SHUTDOWN'),
                             ('bob','admin','RESET'), ('bob','admin','SHUTDOWN')]:
        send(plain_msg(user, role, cmd), 6001)
    send(plain_msg('intruder', 'admin', 'SHUTDOWN'), 6001)
    kill(srv)
    show_log('command_authorization.log')


def task3():
    free(6002)
    open(os.path.join(REPORTS, 'command_token_authentication.log'), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_token_receiver.py')])
    wait_port(6002); time.sleep(0.5)
    for user, role, cmd in [('alice','operator','SET_MODE_SAFE'), ('bob','admin','SHUTDOWN'),
                             ('alice','operator','SHUTDOWN'), ('eve','admin','SHUTDOWN')]:
        send(token_msg(user, role, cmd), 6002)
    send(f"USER=alice;ROLE=admin;CMD=SHUTDOWN;TOKEN=token-alice-123;TIMESTAMP={ts()}", 6002)
    kill(srv)
    show_log('command_token_authentication.log')


def task4():
    free(6003)
    open(os.path.join(REPORTS, 'command_hmac_authentication.log'), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_hmac_receiver.py')])
    wait_port(6003); time.sleep(0.5)
    for user, role, cmd in [('alice','operator','SET_MODE_SAFE'), ('bob','admin','SHUTDOWN')]:
        send(build_plain_hmac_msg(user, role, cmd), 6003)
    send(f"USER=intruder;ROLE=admin;CMD=SHUTDOWN;TIMESTAMP={ts()};AUTH=fake", 6003)
    valid_ts = ts()
    data = f'USER=alice;ROLE=operator;CMD=SET_MODE_SAFE;TIMESTAMP={valid_ts}'
    auth = hmac.new(TOKENS['alice'].encode(), data.encode(), hashlib.sha256).hexdigest()
    send(f'USER=alice;ROLE=operator;CMD=SHUTDOWN;TIMESTAMP={valid_ts};AUTH={auth}', 6003)
    kill(srv)
    show_log('command_hmac_authentication.log')


def task5():
    free(6004)
    for f in ('command_replay_protection.log', 'processed_commands.db'):
        open(os.path.join(REPORTS, f), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_replay_receiver.py')])
    wait_port(6004); time.sleep(0.5)
    msg = build_hmac_msg('alice', 'operator', 'SET_MODE_SAFE')
    send(msg, 6004)
    print(f'[REPLAYING] {msg}'); nc(msg, 6004)
    send(build_hmac_msg('bob', 'admin', 'RESET'), 6004)
    kill(srv)
    show_log('command_replay_protection.log')


def task6():
    free(6005)
    for f in ('command_safety_gate.log', 'processed_commands.db', 'pending_commands.db'):
        open(os.path.join(REPORTS, f), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_safe_receiver.py')])
    wait_port(6005); time.sleep(0.5)
    send(build_hmac_msg('alice', 'operator', 'SET_MODE_SAFE'), 6005)
    send(build_hmac_msg('bob', 'admin', 'SHUTDOWN'), 6005)
    req_id = wait_pending()
    if req_id:
        send(build_hmac_msg('bob', 'admin', 'CONFIRM', req_id), 6005)
    send(build_hmac_msg('bob', 'admin', 'CONFIRM', 'REQ-DOES-NOT-EXIST'), 6005)
    send(build_hmac_msg('alice', 'operator', 'CONFIRM', 'REQ-OPERATOR-ATTEMPT'), 6005)
    kill(srv)
    show_log('command_safety_gate.log')


def task7():
    free(7005)
    for f in ('command_safety_gate.log', 'processed_commands.db', 'pending_commands.db'):
        open(os.path.join(REPORTS, f), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_safe_tls_receiver.py')])
    wait_port(7005, tls=True); time.sleep(0.5)
    send_tls(build_hmac_msg('alice', 'operator', 'SET_MODE_SAFE'), 7005)
    send_tls(f"USER=intruder;ROLE=admin;CMD=SHUTDOWN;COMMAND_ID=BAD-001;TIMESTAMP={ts()};AUTH=fake", 7005)
    send_tls(build_hmac_msg('bob', 'admin', 'SHUTDOWN'), 7005)
    req_id = wait_pending()
    if req_id:
        send_tls(build_hmac_msg('bob', 'admin', 'CONFIRM', req_id), 7005)
    kill(srv)
    show_log('command_safety_gate.log')
    print('\n$ ss -ltnp | grep 7005')
    subprocess.run('ss -ltnp 2>/dev/null | grep 7005 || echo "(receiver already stopped - was bound to 127.0.0.1:7005)"', shell=True)


def task8():
    free(7005)
    open(os.path.join(REPORTS, 'command_hmac_authentication.log'), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_hmac_tls_receiver.py')])
    wait_port(7005, tls=True); time.sleep(0.5)
    cert = os.path.join(ROOT, 'credentials', 'tls', 'orion.pem')
    print(f'\nsocat equivalent: socat OPENSSL-LISTEN:7005,cert={cert},verify=0,fork TCP:127.0.0.1:6003')
    for user, role, cmd in [('alice','operator','SET_MODE_SAFE'), ('bob','admin','RESET')]:
        send_tls(build_plain_hmac_msg(user, role, cmd), 7005)
    kill(srv)
    show_log('command_hmac_authentication.log')


def task9():
    free(7005)
    for f in ('command_safety_gate.log', 'processed_commands.db', 'pending_commands.db'):
        open(os.path.join(REPORTS, f), 'w').close()
    srv = start([sys.executable, os.path.join(SCRIPTS, 'command_safe_tls_receiver.py')])
    wait_port(7005, tls=True); time.sleep(0.5)
    print('\n$ ss -ltnp | grep 7005')
    result = subprocess.run('ss -ltnp', shell=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if '7005' in line: print(' ', line)
    send_tls(build_hmac_msg('alice', 'operator', 'SET_MODE_SAFE'), 7005)
    kill(srv)
    show_log('command_safety_gate.log')
    print('- TLS receiver bound to 127.0.0.1 (loopback only)')
    print('- no external interface exposed')
    print('- attack surface limited to local processes')


if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    tasks = [task1, task2, task3, task4, task5, task6, task7, task8, task9]
    selected = [tasks[int(a) - 1] for a in sys.argv[1:]] if len(sys.argv) > 1 else tasks
    for t in selected:
        t()

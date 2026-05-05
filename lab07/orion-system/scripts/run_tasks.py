#!/usr/bin/env python3
import subprocess
import socket
import time
import os
import sys
import hmac
import hashlib
from datetime import datetime

SCRIPTS = os.path.dirname(__file__)
ROOT = os.path.dirname(SCRIPTS)
REPORTS = os.path.join(ROOT, 'reports')


def ts():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def wait_port(port, timeout=8, host='127.0.0.1'):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def send(message, port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall((message + '\n').encode())
        s.shutdown(socket.SHUT_WR)
    time.sleep(0.4)


def make_msg(user, role, cmd):
    return f"USER={user};ROLE={role};CMD={cmd};TIMESTAMP={ts()}"


def make_token_msg(user, role, cmd):
    tokens = {'alice': 'token-alice-123', 'bob': 'token-bob-999'}
    token = tokens.get(user, 'unknown')
    return f"USER={user};ROLE={role};CMD={cmd};TOKEN={token};TIMESTAMP={ts()}"


def make_hmac_msg(user, role, cmd):
    tokens = {'alice': 'token-alice-123', 'bob': 'token-bob-999'}
    token = tokens.get(user, 'unknown')
    data = f"USER={user};ROLE={role};CMD={cmd};TIMESTAMP={ts()}"
    auth = hmac.new(token.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data};AUTH={auth}"


def start_proc(cmd, **kwargs):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, **kwargs)


def drain(proc, timeout=1.5):
    import select
    lines = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([proc.stdout], [], [], 0.1)
        if r:
            line = proc.stdout.readline()
            if line:
                lines.append(line.rstrip())
    return lines


def kill(proc):
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def show(lines):
    for l in lines:
        print(l)


def task1():
    log = os.path.join(REPORTS, 'command_channel.log')
    open(log, 'w').close()
    proc = start_proc(['bash', os.path.join(SCRIPTS, 'command_receiver.sh')], cwd=SCRIPTS)
    if not wait_port(6000):
        print('ERROR: receiver did not start'); kill(proc); return
    show(drain(proc, 0.6))
    for msg in [
        make_msg('alice', 'operator', 'SET_MODE_SAFE'),
        make_msg('bob', 'operator', 'SET_MODE_NOMINAL'),
        make_msg('admin', 'admin', 'RESET'),
        make_msg('admin', 'admin', 'SHUTDOWN'),
        make_msg('eve', 'operator', 'DEPLOY_SOLAR_ARRAY'),
    ]:
        print(f'[SENDING] {msg}')
        send(msg, 6000)
        show(drain(proc, 0.7))
    injected = f"USER=intruder;ROLE=admin;CMD=SHUTDOWN;TIMESTAMP={ts()}"
    print(f'[INJECTING] {injected}')
    send(injected, 6000)
    show(drain(proc, 0.7))
    kill(proc)
    with open(log) as f:
        print(f.read())


def task2():
    log = os.path.join(REPORTS, 'command_authorization.log')
    open(log, 'w').close()
    proc = start_proc(['bash', os.path.join(SCRIPTS, 'command_authorized_receiver.sh')], cwd=SCRIPTS)
    if not wait_port(6001):
        print('ERROR: receiver did not start'); kill(proc); return
    show(drain(proc, 0.6))
    for user, role, cmd in [
        ('alice', 'operator', 'SET_MODE_SAFE'),
        ('alice', 'operator', 'SET_MODE_NOMINAL'),
        ('alice', 'operator', 'RESET'),
        ('alice', 'operator', 'SHUTDOWN'),
        ('bob',   'admin',    'RESET'),
        ('bob',   'admin',    'SHUTDOWN'),
    ]:
        msg = make_msg(user, role, cmd)
        print(f'[SENDING] {msg}')
        send(msg, 6001)
        show(drain(proc, 0.7))
    forged = f"USER=intruder;ROLE=admin;CMD=SHUTDOWN;TIMESTAMP={ts()}"
    print(f'[SENDING] {forged}')
    send(forged, 6001)
    show(drain(proc, 0.7))
    kill(proc)
    with open(log) as f:
        print(f.read())


def task3():
    log = os.path.join(REPORTS, 'command_token_authentication.log')
    open(log, 'w').close()
    proc = start_proc([sys.executable, os.path.join(SCRIPTS, 'command_token_receiver.py')], cwd=SCRIPTS)
    if not wait_port(6002):
        print('ERROR: receiver did not start'); kill(proc); return
    show(drain(proc, 0.6))
    for user, role, cmd in [
        ('alice', 'operator', 'SET_MODE_SAFE'),
        ('bob',   'admin',    'SHUTDOWN'),
        ('alice', 'operator', 'SHUTDOWN'),
        ('eve',   'admin',    'SHUTDOWN'),
    ]:
        msg = make_token_msg(user, role, cmd)
        print(f'[SENDING] {msg}')
        send(msg, 6002)
        show(drain(proc, 0.7))
    impersonation = f"USER=alice;ROLE=admin;CMD=SHUTDOWN;TOKEN=token-alice-123;TIMESTAMP={ts()}"
    print(f'[SENDING] {impersonation}')
    send(impersonation, 6002)
    show(drain(proc, 0.7))
    sample = make_token_msg('alice', 'operator', 'SET_MODE_SAFE')
    print(f'token visible in message: {sample}')
    kill(proc)
    with open(log) as f:
        print(f.read())


def task4():
    log = os.path.join(REPORTS, 'command_hmac_authentication.log')
    open(log, 'w').close()
    proc = start_proc([sys.executable, os.path.join(SCRIPTS, 'command_hmac_receiver.py')], cwd=SCRIPTS)
    if not wait_port(6003):
        print('ERROR: receiver did not start'); kill(proc); return
    show(drain(proc, 0.6))
    for user, role, cmd in [
        ('alice', 'operator', 'SET_MODE_SAFE'),
        ('bob',   'admin',    'SHUTDOWN'),
    ]:
        msg = make_hmac_msg(user, role, cmd)
        print(f'[SENDING] {msg}')
        send(msg, 6003)
        show(drain(proc, 0.7))
    forged = f"USER=intruder;ROLE=admin;CMD=SHUTDOWN;TIMESTAMP={ts()};AUTH=fake"
    print(f'[SENDING] {forged}')
    send(forged, 6003)
    show(drain(proc, 0.7))
    valid_ts = ts()
    token = 'token-alice-123'
    data = f"USER=alice;ROLE=operator;CMD=SET_MODE_SAFE;TIMESTAMP={valid_ts}"
    auth = hmac.new(token.encode(), data.encode(), hashlib.sha256).hexdigest()
    tampered = f"USER=alice;ROLE=operator;CMD=SHUTDOWN;TIMESTAMP={valid_ts};AUTH={auth}"
    print(f'[SENDING] {tampered}')
    send(tampered, 6003)
    show(drain(proc, 0.7))
    sample = make_hmac_msg('alice', 'operator', 'SET_MODE_SAFE')
    print(f'token not in message: {sample}')
    kill(proc)
    with open(log) as f:
        print(f.read())


if __name__ == '__main__':
    os.makedirs(REPORTS, exist_ok=True)
    task1()
    task2()
    task3()
    task4()

#!/usr/bin/env python3
import os
import fcntl
import time
import sys

SHARED = "/tmp/pp_shared.txt"
LOCK = "/tmp/pp_shared.lock"
CLIENT_LOCK = "/tmp/pp_client.lock"
SERVER_LOCK = "/tmp/pp_server.lock"
TIMEOUT = 5
BUFFER = 16
client_lk = None
def read_response():
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_SH)
        fd = os.open(SHARED, os.O_RDONLY)
        data = os.read(fd, BUFFER ).decode('utf-8', errors='ignore').strip('\x00')
        if data.startswith("S:"):
            return data[2:]
        return ""
    except Exception:
        return ""
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def write_request(text):
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        os.write(fd, f"C:{text}".encode())
        return True
    except Exception:
        return False
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def clear_file():
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        return True
    except Exception:
        return False
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def wait_server():
    start = time.time()
    while time.time() - start < TIMEOUT:
        if not os.path.exists(SERVER_LOCK):
            time.sleep(0.3)
            continue
        try:
            lk = os.open(SERVER_LOCK, os.O_RDWR)
            try:
                fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.close(lk)
                time.sleep(0.3)
                continue
            except (IOError, OSError):
                os.close(lk)
                return True
        except Exception:
            time.sleep(0.3)
            continue
    return False

def acquire_client_lock():
    global client_lk
    try:
        client_lk = os.open(CLIENT_LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(client_lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False

def release_client_lock():
    global client_lk
    if client_lk is not None:
        fcntl.flock(client_lk, fcntl.LOCK_UN)
        os.close(client_lk)
        client_lk = None

if not acquire_client_lock():
    print("[client] another client running", file=sys.stderr)
    sys.exit(1)

print("[client] started") 

if not wait_server():
    print("[client] server not found")
    release_client_lock()
    sys.exit(1)

print("[client] connected")

state = 1
msg = ""
wait_start = 0
try:
    while True:
        if state == 1:
            try:
                msg = input("> ").strip()
                if len(msg) > BUFFER :
                        print("[client] error: message too long")
                        state = 1
                        continue
            except EOFError:
                break
            if msg == "exit":
                break
            if not msg:
                continue
            state = 2
        elif state == 2:
            if write_request(msg):
                print(f"[client] sent: {msg}")
                wait_start = time.time()
                state = 3
            else:
                print("[client] send failed")
                state = 1
        elif state == 3:
            resp = read_response()
            if resp:
                print(f"[client] get: {resp}")
                clear_file()
                state = 1
            elif time.time() - wait_start > TIMEOUT:
                print("[client] timeout")
                clear_file()
                state = 1
            else:
                time.sleep(0.2)
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

release_client_lock()
print("[client] stopped")

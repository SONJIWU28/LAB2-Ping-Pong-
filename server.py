#!/usr/bin/env python3
import os
import fcntl
import time
import sys

SHARED = "/tmp/pp_shared.txt"
LOCK = "/tmp/pp_shared.lock"
SERVER_LOCK = "/tmp/pp_server.lock"
BUFFER = 16
server_lk = None
def read_request():
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_RDWR)
        data = os.read(fd, BUFFER).decode('utf-8', errors='ignore').strip('\x00')
        if data.startswith("C:"):
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
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

def write_response(text):
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        os.write(fd, f"S:{text}".encode())
        return True
    except Exception:
        return False
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def cleanup():
    for f in (SHARED, LOCK):
        try:
            os.remove(f)
        except Exception:
            pass

def acquire_server_lock():
    global server_lk
    try:
        server_lk = os.open(SERVER_LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(server_lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False

def release_server_lock():
    global server_lk
    if server_lk is not None:
        fcntl.flock(server_lk, fcntl.LOCK_UN)
        os.close(server_lk)
        server_lk = None

if not acquire_server_lock():
    print("[server] already running", file=sys.stderr)
    sys.exit(1)

cleanup()
print("[server] started")

state = 1
msg = ""
try:
    while True:
        if state == 1:
            req = read_request()
            if req:
                msg = req
                print(f"[server] get: {msg}")
                state = 2
        elif state == 2:
            if msg == "ping" or msg == "Ping" or msg == "PING"  :
                state = 3
            else:
                print(f"[server] unknown: {msg}")
                state = 4
        elif state == 3:
            if write_response("pong"):
                print("[server] sent: pong")
                state = 1
            else:
                state = 4
        elif state == 4:
            write_response("error")
            print("[server] sent: error")
            state = 1
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
cleanup()
release_server_lock()
try:
    os.remove(SERVER_LOCK)
except Exception:
    pass
print("[server] stopped")

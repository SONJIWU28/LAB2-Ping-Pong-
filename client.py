import os
import fcntl
import time
import sys

SHARED = "/tmp/pp_shared.txt"
LOCK = "/tmp/pp_shared.lock"
CLIENT_LOCK = "/tmp/pp_client.lock"
SERVER_LOCK = "/tmp/pp_server.lock"
client_lk = None

def read_file():
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_SH)
        fd = os.open(SHARED, os.O_RDONLY)
        return os.read(fd, 16).decode('utf-8', errors='ignore').strip('\x00')
    except Exception:return ""
    finally:
        if fd is not None:os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def write_file(text):
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        encoded = text.encode('utf-8')
        os.write(fd, encoded)
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
    while time.time() - start < 5:
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
    except (IOError, OSError):return False

def release_client_lock():
    global client_lk
    if client_lk is not None:
        fcntl.flock(client_lk, fcntl.LOCK_UN)
        os.close(client_lk)
        client_lk = None

if not acquire_client_lock():
    print("another client already running", file=sys.stderr)
    sys.exit(1)
print("started")
if not wait_server():
    print("timeout")
    release_client_lock()
    sys.exit(1)
print("connected")
state = 1
msg = ""
wait_start = 0
try:
    while True:
        if state == 1:
            try:msg = input("> ").strip()
            except EOFError:break
            if msg == "exit":break
            if not msg:continue
            state = 2
        elif state == 2:
            if write_file(msg):
                print(f"sent: {msg}")
                wait_start = time.time()
                state = 3
            else:
                print("send failed")
                state = 1
        elif state == 3:
            resp = read_file()
            if resp == "error":
                print("error from server")
                state = 1
            elif resp:
                print(f"get: {resp}")
                state = 1
            elif time.time() - wait_start > 5:
                print("The server is not running")
                write_file("")
                state = 1
except KeyboardInterrupt: pass
release_client_lock()
print("stopped")
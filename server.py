import os
import fcntl
import sys

SHARED = "/tmp/pp_shared.txt"
LOCK = "/tmp/pp_shared.lock"
SERVER_LOCK = "/tmp/pp_server.lock"
last_sent = ""
server_lk = None

def read_and_clear():
    global last_sent
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_RDWR)
        data = os.read(fd, 16).decode('utf-8', errors='ignore').strip('\x00')
        if data and data!=last_sent:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            last_sent = ""
            return data
        return ""
    except Exception: return ""
    finally:
        if fd is not None: os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def write_file(text):
    global last_sent
    lk = fd = None
    try:
        lk = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(SHARED, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        encoded = text.encode('utf-8')
        os.write(fd, encoded)
        last_sent=text
        return True
    except Exception: return False
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)

def cleanup():
    for f in (SHARED, LOCK):
        try: os.remove(f)
        except Exception: pass

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
    print("already running", file=sys.stderr)
    sys.exit(1)
cleanup()
print("started")
state = 1
try:
    while True:
        if state == 1:
            msg = read_and_clear()
            if msg:
                print(f"get: {msg}")
                if msg == "ping":state = 2
                else:
                    print(f"unknown command: {msg}")
                    if write_file("error"):print("sent: error")
        elif state == 2:
            if write_file("pong"):
                print("sent: pong")
                state = 1
except KeyboardInterrupt: pass
cleanup()
release_server_lock()
try: os.remove(SERVER_LOCK)
except Exception: pass
print("stopped")
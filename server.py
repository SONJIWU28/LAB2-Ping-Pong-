#!/usr/bin/env python3
import os
import fcntl
import time

shared_file = "/tmp/pp_shared.txt"
lock_file = "/tmp/pp_shared.lock"
server_lock = "/tmp/pp_server.lock"
buf_size = 16

client_msg = "_C:"
server_msg = "_S:"
error_msg = "_ERR"


def read_from_file():
    lk = None
    fd = None
    try:
        lk = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_SH)
        fd = os.open(shared_file, os.O_RDONLY)
        data = os.read(fd, buf_size)
        return data.decode().strip('\x00')
    except:
        return ""
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)


def write_to_file(text):
    lk = None
    fd = None
    try:
        lk = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd = os.open(shared_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        os.write(fd, text.encode()[:buf_size])
        return True
    except:
        return False
    finally:
        if fd is not None:
            os.close(fd)
        if lk is not None:
            fcntl.flock(lk, fcntl.LOCK_UN)
            os.close(lk)


def cleanup():
    for f in (shared_file, lock_file):
        try:
            os.remove(f)
        except:
            pass
    print("Server: shared files cleared")


def try_lock_server():
    try:
        fd = os.open(server_lock, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except:
        return None


srv_fd = try_lock_server()
if srv_fd is None:
    print("Server: another instance already running")
    exit(1)

cleanup()
print("=== Server started ===")

state = 1
received = ""

try:
    while True:
        if state == 1:
            req = read_from_file()
            if req and req.startswith(client_msg):
                received = req[len(client_msg):]
                print("Server: message received from client: \"" + received + "\"")
                state = 2
        elif state == 2:
            print("Server: message processing")
            if received == "ping":
                state = 3
            else:
                print("Server: message is not ping")
                state = 4
        elif state == 3:
            print("Server: sending response to client")
            if write_to_file(server_msg + "pong"):
                print("Server: response have sent: \"pong\"")
                print()
                state = 1
            else:
                state = 4
        elif state == 4:
            print("Server: unexpected error")
            write_to_file(error_msg)
            print()
            time.sleep(0.5)
            state = 1
        time.sleep(0.2)
except KeyboardInterrupt:
    pass

fcntl.flock(srv_fd, fcntl.LOCK_UN)
os.close(srv_fd)
try:
    os.remove(server_lock)
except:
    pass
cleanup()
print("=== Server stopped ===")

#!/usr/bin/env python3
import os
import fcntl
import time

shared_file = "/tmp/pp_shared.txt"
lock_file = "/tmp/pp_shared.lock"
buf_size = 16

client_msg = "_C:"
server_msg = "_S:"
error_msg = "_ERR"

connect_timeout = 5
response_timeout = 8


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


def wait_server():
    start = time.time()
    while not os.path.exists(lock_file):
        if time.time() - start > connect_timeout:
            return False
        time.sleep(0.3)
    return True


print("=== Client started ===")

if not wait_server():
    print("Client: server is not running")
    exit(1)

print("Client: connected to server")

state = 1
user_msg = ""
wait_start = 0

try:
    while True:
        if state == 1:
            try:
                user_msg = input("> ").strip()
            except:
                break
            if user_msg == "exit":
                break
            if not user_msg:
                continue
            if len(client_msg) + len(user_msg) > buf_size:
                print("Client: message too long (max " + str(buf_size - len(client_msg)) + " bytes)")
                continue
            state = 2
        elif state == 2:
            print("Client: message sending: \"" + user_msg + "\"")
            if write_to_file(client_msg + user_msg):
                print("Client: message have sent")
                wait_start = time.time()
                state = 3
            else:
                print("Client: error sending message")
                state = 5
        elif state == 3:
            print("Client: waiting for response")
            state = 4
        elif state == 4:
            resp = read_from_file()
            if resp == error_msg:
                print("Client: Error")
                print()
                write_to_file("")
                state = 1
            elif resp.startswith(server_msg):
                print("Client: got message from server: \"" + resp[len(server_msg):] + "\"")
                print()
                write_to_file("")
                state = 1
            elif time.time() - wait_start > response_timeout:
                print("Client: Error")
                state = 5
            else:
                time.sleep(0.3)
                continue
        elif state == 5:
            print("Client: Error")
            time.sleep(1)
            state = 1
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

print("=== Client stopped ===")

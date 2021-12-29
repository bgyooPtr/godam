#!/usr/bin/env python3

__author__ = "Byeonggil Yoo"
__copyright__ = "Copyright 2020, The GoDam Project"
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Byeonggil Yoo"
__email__ = "byeonggil.u@gmail.com"

import sys
import argparse

import socket
import threading
import subprocess

ENCODING = 'utf-8'
lock = threading.Lock()

def send_msg_to_notification(msg):
    subprocess.Popen(['notify-send', msg])
    return

# Client
def recv_msg(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            msg = data.decode(ENCODING)
            if msg == '/godam':
                send_msg_to_notification("Go dam!!")
            else:
                print(msg)
        except:
            pass

def run_client(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        t = threading.Thread(target=recv_msg, args=(sock,))
        t.daemon = True
        t.start()
        
        while True:
            msg = input()
            if msg == '/quit':
                sock.send(msg.encode(ENCODING))
                break

            sock.send(msg.encode(ENCODING))

# Main
if __name__ == "__main__":
    if len(sys.argv) > 4:
        print('-h or --help')
        sys.exit(1)

    PORT = 1126

    parser = argparse.ArgumentParser(description='**** GODAM Client ****')
    parser.add_argument('-i', '--ip', type=str, help='-i <ip-address>')
    args = parser.parse_args()

    print('Client is connecting to the server', args.ip, PORT)
    run_client(args.ip, PORT)
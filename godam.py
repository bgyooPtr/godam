#!/usr/bin/env python3

__author__ = "Byeonggil Yoo"
__copyright__ = "Copyright 2020, The GoDam Project"
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Byeonggil Yoo"
__email__ = "byeonggil.u@gmail.com"

import sys
import argparse

import socketserver
import socket
import threading
import subprocess

ENCODING = 'utf-8'
lock = threading.Lock()

def send_msg_to_notification(msg):
    subprocess.Popen(['notify-send', msg])
    return

class UserManager:
    def __init__(self):
        self.users = {}

    def add_user(self, username, conn, addr):
        if username in self.users:
            conn.send('Already registered user'.encode(ENCODING))
            return None
        
        lock.acquire()
        self.users[username] = (conn, addr)
        lock.release()

        self.broadcast('[%s] is connected!!' % username)

        return username
    
    def remove_user(self, username):
        if username not in self.users:
            return
        
        lock.acquire()
        del self.users[username]
        lock.release()

        self.broadcast('[%s] is disconnected!!' % username)

    def message_handler(self, username, msg):
        if msg[0] != '/':
            self.broadcast('[%s] %s' % (username, msg), username)
            return
        if msg.strip() == '/godam':
            self.broadcast(msg)
        if msg.strip() == '/quit':
            self.remove_user(username)
            return -1

    def broadcast(self, msg, username=None):
        # for conn, addr in self.users.values():
            # conn.send(msg.encode(ENCODING))
        for key in self.users.keys():
            if username is None:
                self.users[key][0].send(msg.encode(ENCODING))
            else:
                if key is not username:
                    self.users[key][0].send(msg.encode(ENCODING))

class TCPHandler(socketserver.BaseRequestHandler):
    userman = UserManager()

    def handle(self):
        print('[%s] is connected.' % self.client_address[0])

        try:
            username = self.register_username()
            print('[%s] is registered.' % username)
            msg = self.request.recv(1024)

            while msg:
                print('%s> %s' % (username, msg.decode(ENCODING)))
                if self.userman.message_handler(username, msg.decode()) == -1:
                    self.request.close()
                    break
                msg = self.request.recv(1024)
        except Exception as e:
            print(e)
        
        print('[%s] exit' %self.client_address[0])
        self.userman.remove_user(username)

    def register_username(self):
        while True:
            self.request.send('Your ID:'.encode(ENCODING))
            username = self.request.recv(1024)
            username = username.decode(ENCODING).strip()
            if self.userman.add_user(username, self.request, self.client_address):
                return username

class GodamServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def run_server(port):
    print('-- Godam Server --')
    try:
        server = GodamServer(('', port), TCPHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('bye~')
        server.shutdown()
        server.server_close()

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
    if len(sys.argv) < 1:
        print('-h or --help')
        sys.exit(1)

    parser = argparse.ArgumentParser(description='for my friends')
    parser.add_argument('-s', '--server', type=str, nargs=1, help='-s <port>')
    parser.add_argument('-c', '--client', type=str, nargs=2, help='-c <ip-addr> <port>')
    args = parser.parse_args()

    if(args.server is not None):
        print('Server will be started:', args.server[0])
        run_server(int(args.server[0]))

    if(args.client is not None):
        print('Client is connecting to the server', args.client[0], args.client[1])
        run_client(args.client[0], int(args.client[1]))
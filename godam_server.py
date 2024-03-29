#!/usr/bin/env python3

__author__ = "Byeonggil Yoo"
__copyright__ = "Copyright 2020, The GoDam Project"
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Byeonggil Yoo"
__email__ = "byeonggil.u@gmail.com"

import socketserver
import socket

ENCODING = 'utf-8'

class UserManager:
    def __init__(self):
        self.users = {}

    def add_user(self, username, conn, addr):
        if username in self.users:
            conn.send('Already registered user'.encode(ENCODING))
            return None
        
        self.users[username] = (conn, addr)
        self.broadcast('[%s] is connected!!' % username)

        return username
    
    def remove_user(self, username):
        if username not in self.users:
            return
        
        del self.users[username]
        self.broadcast('[%s] is disconnected!!' % username)

    def list_user(self):
        msg = ''
        cnt = 0
        for key, _ in self.users.items():
            msg += "{}: {}\n".format(cnt, key)
            cnt += 1
        return msg

    def message_handler(self, username, msg):
        if msg[0] != '/':
            self.broadcast('[%s] %s' % (username, msg), username)
            return
        if msg.strip() == '/godam':
            self.broadcast(msg)
        elif msg.strip() == '/list':
            self.send_to_user(self.list_user(), username)
        elif msg.strip() == '/quit':
            self.remove_user(username)
            return -1
            
    def send_to_user(self, msg, username):
        self.users[username][0].send(msg.encode(ENCODING))

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
                print('TCPHandler::handle()')
                print('%s> %s' % (username, msg.decode(ENCODING)))
                if self.userman.message_handler(username, msg.decode(ENCODING)) == -1:
                    self.request.close()
                    break
                msg = self.request.recv(1024)

            print('[%s] exit' %self.client_address[0])
            self.userman.remove_user(username)

        except Exception as e:
            print(e)
        

    def register_username(self):
        while True:
            print('TCPHandler::register_username()')
            username = self.request.recv(1024)
            username = username.decode(ENCODING).replace('/user_id/', '')
            if self.userman.add_user(username, self.request, self.client_address):
                self.userman.send_to_user('/user_id/_registered', username)
                return username

class GodamServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

def run_server(port):
    print('-- Godam Server --')
    try:
        server = GodamServer(('', port), TCPHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()

# Main
if __name__ == "__main__":
    PORT = 1126
    run_server(PORT)

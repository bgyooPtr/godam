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

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QGridLayout
from PyQt5.QtCore import QCoreApplication

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
                print('%s> %s' % (username, msg.decode(ENCODING)))
                if self.userman.message_handler(username, msg.decode()) == -1:
                    self.request.close()
                    break
                msg = self.request.recv(1024)

            print('[%s] exit' %self.client_address[0])
            self.userman.remove_user(username)

        except Exception as e:
            print(e)
        

    def register_username(self):
        while True:
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
        print('bye~')
        server.shutdown()
        server.server_close()

# Client

class GodamClient():
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))


    def recv_msg_loop(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                msg = data.decode(ENCODING)
                if msg == '/godam':
                    send_msg_to_notification("Go dam!!")
                else:
                    print(msg+'\n')
            except:
                pass

    def set_user_id(self, id):
        while True:
            self.sock.send(('/user_id/' + id).encode(ENCODING))
            data = self.sock.recv(1024)
            msg = data.decode(ENCODING)
            if msg.replace('/user_id/', '') == '_registered':
                print('[%s] is registered.' % id)
                break

    def send_msg_loop(self):
        while True:
            msg = input()
            self.sock.send(msg.encode(ENCODING))

            if msg == '/quit':
                break

    def run(self):
        recv_thread = threading.Thread(target=self.recv_msg_loop)
        recv_thread.daemon = True
        recv_thread.start()

        send_thread = threading.Thread(target=self.send_msg_loop)
        send_thread.daemon = True
        send_thread.start()

        recv_thread.join()
        send_thread.join()

# UI
class ClientUI(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.initUI()
    
    def initUI(self):
        main_layout = QGridLayout()

        self.txtUser = QLineEdit(self)
        main_layout.addWidget(self.txtUser, 1, 0)

        self.btnRegister = QPushButton('Register', self)
        self.btnRegister.setCheckable(True)
        self.btnRegister.toggle()
        self.btnRegister.clicked.connect(self.btnRegister_clicked)
        main_layout.addWidget(self.btnRegister, 1, 1)

        btnQuit = QPushButton('Quit', self)
        btnQuit.clicked.connect(QCoreApplication.instance().quit)
        main_layout.addWidget(btnQuit, 2, 1)

        self.setWindowTitle('GoDam')
        self.setGeometry(300, 300, 300, 200)
        self.setLayout(main_layout)
        self.show()
    
    def btnRegister_clicked(self):
        if not self.btnRegister.isChecked():
            self.userID = self.txtUser.text()
            self.client.set_user_id(self.userID)

            client_thread = threading.Thread(target=self.client.run())
            client_thread.daemon = True
            client_thread.start()

            self.txtUser.setDisabled(True)
            self.btnRegister.setText('Cancel')
        else:
            self.txtUser.setDisabled(False)
            self.btnRegister.setText('Register')

def run_client(host, port):
    client = GodamClient(host, port)
    # client_t = threading.Thread(target=client.run())
    # client_t.daemon = True
    # client_t.start()

    app = QApplication([]) # or sys.argv
    ex = ClientUI(client)

    # client_t.join()
    sys.exit(app.exec_())

# Main
if __name__ == "__main__":
    if len(sys.argv) < 1:
        print('-h or --help')
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', type=str, nargs=1, help='-s <port>')
    parser.add_argument('-c', '--client', type=str, nargs=2, help='-c <ip-addr> <port>')
    args = parser.parse_args()

    if(args.server is not None):
        print('Server will be started:', args.server[0])
        run_server(int(args.server[0]))

    if(args.client is not None):
        print('Client is connecting to the server', args.client[0], args.client[1])
        # client_thread = threading.Thread(target=run_client, args=(args.client[0], int(args.client[1])))
        # client_thread.daemon = True
        # client_thread.start()
        run_client(args.client[0], int(args.client[1]))

#!/usr/bin/env python3

__author__ = "Byeonggil Yoo"
__copyright__ = "Copyright 2020, The GoDam Project"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Byeonggil Yoo"
__email__ = "byeonggil.u@gmail.com"

import sys
import subprocess
from socket import socket, SO_REUSEADDR, SOL_SOCKET, SOCK_STREAM, AF_INET, gethostbyname, gethostname
from asyncio import Task, coroutine, get_event_loop

import argparse
import threading
import getpass

def send_msg_to_notification(msg):
    subprocess.Popen(['notify-send', msg])
    return

ENCODING = 'utf-8'
BUFFER_SIZE = 1024

class Peer(object):
    def __init__(self, server, sock, name):
        self.loop = server.loop
        self.name = name
        self._sock = sock
        self._server = server
        Task(self._peer_handler())

    def send(self, data):
        return self.loop.sock_sendall(self._sock, data.encode(ENCODING))

    @coroutine
    def _peer_handler(self):
        try:
            yield from self._peer_loop()
        except IOError:
            pass
        finally:
            self._server.remove(self)
    
    @coroutine
    def _peer_loop(self):
        while True:
            buf = yield from self.loop.sock_recv(self._sock, BUFFER_SIZE)
            if buf == b'':
                break

            message = '%s: %s' % (self.name, buf.decode(ENCODING))

            print(message)
            self._server.broadcast(message)

class Server(object):
    def __init__(self, loop, port):
        self.loop = loop
        self._serv_sock = socket()
        self._serv_sock.setblocking(0)
        self._serv_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._serv_sock.bind(('', port))
        self._serv_sock.listen(5)
        self._peers = []
        Task(self._server())

    def remove(self, peer):
        self._peers.remove(peer)
        self.broadcast('Peer %s quit!\n' % (peer.name))

    def broadcast(self, message):
        for peer in self._peers:
            peer.send(message)

    @coroutine
    def _server(self):
        while True:
            peer_sock, peer_name = yield from self.loop.sock_accept(self._serv_sock)
            peer_sock.setblocking(0)
            peer = Peer(self, peer_sock, peer_name)
            self._peers.append(peer)

            message = 'Peer %s connected!\n' % (peer.name,)
            print(message)
            self.broadcast(message)

def run_server(port):
    loop = get_event_loop()
    Server(loop, port)
    loop.run_forever()

## client
def listener(sock):
    try:
        while True:
            data = sock.recv(BUFFER_SIZE).decode(ENCODING)
            print('>', data)
            send_msg_to_notification(data)
    except ConnectionAbortedError:
        pass

def run_client(host, port):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host, port))

    listener_thread = threading.Thread(target=listener, args=(sock,))
    listener_thread.start()

    try:
        while True:
            message = input('>')
            sock.send(message.encode(ENCODING))
    except EOFError:
        pass
    finally:
        sock.close()

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


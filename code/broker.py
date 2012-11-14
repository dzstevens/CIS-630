'''
Created on Nov 13, 2012

@author: David Stevens
'''

import socket
from select import *
from sys import stdin, exit, argv
from connections import TestConn

HOST = ""
READ_ONLY = POLLIN | POLLPRI | POLLHUP | POLLERR
READ_WRITE = READ_ONLY | POLLOUT

def main(*args):
    PORT = int(args[1]) if len(args) > 1 else 55555    
    client_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_listener.bind((HOST, PORT))
    client_listener.listen(5)

    f_to_sock = {client_listener.fileno() : client_listener, stdin.fileno(): stdin}
    p = poll()
    p.register(client_listener, READ_ONLY)
    p.register(stdin.fileno(), READ_ONLY)
    try:
        print("Type 'exit' to quit\n\n")
        while True:
            actions = p.poll()
            for f, flag in actions:
                current_sock = f_to_sock[f]
                if flag & (POLLIN | POLLPRI):
                    if current_sock is client_listener:
                        client_sock, addr = client_listener.accept()
                        new_client = TestConn(client_sock)
                        new_client.start()
                        f_to_sock[client_sock.fileno()] = client_sock
                    elif current_sock is stdin:
                        choice = input().strip().lower()
                        if choice == 'exit':
                            for s in f_to_sock:
                                f_to_sock[s].close()
                            exit(0)
                elif flag & POLLERR:
                    print("Error: () Closing socket: {}".format(flag, f))
                    p.unregister(f)
                    current_sock.close()
                    del f_to_sock[f]
    except Exception as e:
        print('ERROR:', e)
        if len(f_to_sock) > 0:
            for sock in f_to_sock.values():
                sock.close()

if __name__ == '__main__':
    main(*argv)
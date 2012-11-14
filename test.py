'''
Created on Nov 29, 2011

@author: david
'''
from socket import *
import sys
from sendfile import sendfile
import os
CHUNK = 1024
DELIM = b'\n'

def send_meta(sock, msg): 
    sock.sendall(msg)
        
def send_header(sock, name, size):
    sock.sendall(name.encode()+DELIM)
    sock.sendall(str(size).encode()+DELIM)
        
def send_file(sock, file):
    size = os.path.getsize(file)
    send_header(sock, file, size)
    with open(file, 'rb') as f:
        offset = 0
        while True:
            sent = sendfile(sock.fileno(), f.fileno(), offset, CHUNK)
            if sent == 0:
                break  # EOF
            offset += sent

def main(*args):
    HOST = ""
    PORT = int(args[1]) if len(args) > 1 else 55555
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((HOST, PORT))
    while(True):
        file = input('file: ')
        if(send_file(sock, file) == 0):
            sock.close()
            break
    
if __name__ == '__main__':
    main(*sys.argv)

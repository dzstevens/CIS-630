from threading import Thread
import socket
from sendfile import sendfile
from collections import namedtuple
import os

CHUNK = 1024
DELIM = b'\n'
class Conn(Thread):

    def __init__(self, sock):
        Thread.__init__(self)
        self.sock = sock
        self.buff = bytes()

    def send_meta(self, msg): 
        self.sock.sendall(msg+DELIM)
        
    def send_header(self, name, size):
        self.sock.sendall(name.encode())
        self.sock.sendall(str(size).encode())
        
    def send_file(self, name):
        size = os.path.getsize(file)
        self.send_header(name, size)
        with open(name, 'rb') as f:
            offset = 0
            while True:
                sent = sendfile(sock.fileno(), f.fileno(), offset, CHUNK)
                if sent == 0:
                    break  # EOF
                offset += sent
        
    def recv_meta(self):
        end = self.buff.find(DELIM)
        while (end == -1):
            msg = self.sock.recv(CHUNK)
            if len(msg) == 0:
                self.sock.close()
                raise socket.error()
            self.buff+=msg
            end = self.buff.find(DELIM)
        meta = self.buff[:end].decode()
        self.buff = self.buff[end+1:]
        return meta
        
    def recv_header(self):
        header = namedtuple('Header', ['size', 'name'])
        header.name = self.recv_meta()
        header.size = int(self.recv_meta())
        return header
    
    def recv_file(self):
        header = self.recv_header()
        while len(self.buff) < header.size:
            msg = self.sock.recv(CHUNK)
            if len(msg) == 0:
                self.sock.close()
                raise socket.error()
            self.buff += msg
        with open(header.name, 'wb') as f:
            f.write(self.buff[:header.size])
            self.buff = self.buff[header.size:]
        return header
            
class TestConn(Conn):
    def run(self):
        try:
            while(True):
                h = self.recv_file()
                print('Wrote {} ({} bytes)'.format(h.name, h.size))

        except socket.error:
            print("Socket Error.")
        finally:
            self.sock.close()

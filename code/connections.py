import socket, os, errno
from multiprocessing import Process
from sendfile import sendfile
from collections import namedtuple

CHUNK = 1024
DELIM = b'\n'

class Conn(Process):

    def __init__(self, sock):
        Process.__init__(self)
        self.sock = sock
        self.buff = bytes()

    def send_meta(self, msg):
        try:
            self.sock.sendall(msg.encode()+DELIM)
        except:
            self.sock.close()
            raise
        
    def send_header(self, header):
        self.send_meta(header.name)
        self.send_meta(header.op)
        if header.size != -1:
            self.send_meta(str(header.size))
        
    def send_change(self, name, delete=False):
        header = namedtuple('Header', ['name', 'op', 'size'])
        header.name = name
        header.op = 'ADD' if not delete else 'DEL'
        header.size = os.path.getsize(name) if not delete else -1
        self.send_header(header)
        if not delete:
            self.send_file(name)

    def send_file(self, name):
        size = os.path.getsize(name)
#         percentage = 0
#         print('Sending \'{}\'...'.format(name))
        with open(name, 'rb') as f:
            offset = 0
            while True:
                sent = sendfile(self.sock.fileno(), f.fileno(), offset, CHUNK)
                if sent == 0:
                    break  # EOF
                offset += sent
#                 new = int(100*(offset / float(size)))
#                 if new - percentage >= 10:
#                     percentage = new
#                     print('\t{}%'.format(percentage))
        
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
        header = namedtuple('Header', ['name', 'op'])
        header.name = self.recv_meta()
        header.op = self.recv_meta()
        if header.op != 'DEL':
            header.size = int(self.recv_meta())
        return header
    
    def recv_file(self, header):
#         print('Recieving \'{}\'...'.format(header.name))
#         percentage = 0
        while len(self.buff) < header.size:
            msg = self.sock.recv(CHUNK)
            if len(msg) == 0:
                self.sock.close()
                raise socket.error()
            self.buff += msg
#             new = int(100*(len(self.buff) / float(header.size)))
#             if new - percentage >= 10:
#                 percentage = new
#                 print('\t{}%'.format(percentage))
        with open(header.name, 'wb') as f:
            f.write(self.buff[:header.size])
            self.buff = self.buff[header.size:]

class ClientConn(Conn):
    def __init__(self, sock, cache):
        Conn.__init__(self, sock)
        self.cache = cache
        
    def run(self):
        try:
            while(True):
                h = self.recv_header()
                h.name = self.cache + h.name
                if h.op == 'ADD':
                    self.recv_file(h)
                    print('Wrote {} ({} bytes)'.format(h.name, h.size))
                else:
                    try:
                        os.remove(h.name)
                        print('Deleted {}'.format(h.name))
                    except OSError as exception:
                        if exception.errno != errno.ENOENT:
                            raise

        except socket.error:
            print("Socket Error")
        finally:
            self.sock.close()

class TestConn(Conn):
    def run(self):
        while(True):
            file = raw_input('file: ')
            if file.lower()[0] == 'q':
                break
            op = False if raw_input('Update (u) or Delete (d): ')[0].lower() == 'u' else True
            try:
                self.send_change(file, op)
            except:
                self.sock.close()
                raise

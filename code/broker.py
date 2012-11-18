'''
Created on Nov 13, 2012

@author: David Stevens
'''

import socket, os, errno, asyncore, asynchat, sys

HOST = ""
PORT = 55555
CACHE = './cache/'
CHUNK = 1024
TERM = '\n'

def make_dir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            
class BrokerServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        make_dir(CACHE)
        
    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            handler = ClientChannel(sock, CACHE)
            
class ClientChannel(asynchat.async_chat):          
    def __init__(self, sock, cache):
        asynchat.async_chat.__init__(self, sock)
        self.buff = []
        self.process_data = self._process_header
        self.set_terminator(TERM)
        self.cache = cache
        self.file_name = ''
    
    def push(self, msg):
        asynchat.async_chat.push(self, msg+TERM)

    def collect_incoming_data(self, data):
        '''Read an incoming message from the client and put it into buffer.'''
        self.buff.append(data)

    def found_terminator(self):
        '''The end of a header or message has been seen.'''
        self.process_data()
    
    def _process_header(self):        
        '''We have the full header'''
        header = ''.join(self.buff).strip().split('\t')
        self.file_name, op = header[:2]
        self.file_name = self.cache+self.file_name
        if op != 'DEL':
            size = int(header[2])
            self.set_terminator(size)
            self.process_data = self._write_file
        else:
            self._delete_file()
        self.buff = []
    
    def _write_file(self):
        if self.file_name:
            size = 0
            with open(self.file_name, 'w') as f:
                for s in self.buff:
                    size += len(s)
                    f.write(s)
            self.buff = []
            print('Wrote {} ({} bytes)'.format(self.file_name, size))
        self.file_name = ''
        self.push('File recieved!')
        self.set_terminator(TERM)
        self.process_data = self._process_header
    
    def _delete_file(self):
        print('Attempting to delete: {}'.format(self.file_name))
        try:
            os.remove(self.file_name)
            print('Deleted {}'.format(self.file_name))
            self.file_name = ''
            self.push('File deleted!')
        except OSError as exception:
            if exception.errno != errno.ENOENT:
                raise
            else:
                self.push('File not present!')

class CmdlineClient(asyncore.file_dispatcher):
    def __init__(self):
        print('Type \'q\' to quit\n')
        asyncore.file_dispatcher.__init__(self, sys.stdin)

    def handle_read(self):
        if self.recv(1).lower() == 'q':
            sys.exit(0)

def main():
    try:
        b = BrokerServer(HOST, PORT)
        c = CmdlineClient()
        asyncore.loop()
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':
    main()

# def main(*args):
#     make_dir(CACHE)
#     PORT = int(args[1]) if len(args) > 1 else 55555    
#     client_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     client_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     client_listener.bind((HOST, PORT))
#     client_listener.listen(5)
# 
#     f_to_sock = {client_listener.fileno() : client_listener, stdin.fileno(): stdin}
#     p = poll()
#     p.register(client_listener, READ_ONLY)
#     p.register(stdin.fileno(), READ_ONLY)
#     try:
#         print("Type 'q' to quit\n\n")
#         while True:
#             actions = p.poll()
#             for f, flag in actions:
#                 current_sock = f_to_sock[f]
#                 if flag & (POLLIN | POLLPRI):
#                     if current_sock is client_listener:
#                         client_sock, addr = client_listener.accept()
#                         new_client = ClientConn(client_sock, CACHE)
#                         new_client.start()
#                         f_to_sock[client_sock.fileno()] = client_sock
#                     elif current_sock is stdin:
#                         choice = raw_input().strip().lower()[0]
#                         if choice == 'q':
#                             for s in f_to_sock:
#                                 f_to_sock[s].close()
#                             exit(0)
#                 elif flag & POLLERR:
#                     print("Error: {} Closing socket: {}".format(flag, f))
#                     p.unregister(f)
#                     current_sock.close()
#                     del f_to_sock[f]
#     except Exception as e:
#         print('ERROR: {}'.format(e))
#         if len(f_to_sock) > 0:
#             for sock in f_to_sock.values():
#                 sock.close()
# 
# if __name__ == '__main__':
#     main(*argv)
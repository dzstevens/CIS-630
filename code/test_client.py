import socket
import sys

import asynchat
import asyncore

import constants


class MockBrokerReceive(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            p("Connected!\n")
            self.channel = MockChannel(sock)


class MockBrokerSend(asyncore.file_dispatcher):
    def __init__(self, b):
        asyncore.file_dispatcher.__init__(self, sys.stdin)
        self.buffer = ''
        self.b = b

    def handle_read(self):
        self.buffer = self.buffer + self.recv(1024)
        if self.buffer.find(constants.DELIMITER):
            data, self.buffer = self.buffer.split(constants.DELIMITER, 1)
            self.b.channel.push(constants.DELIMITER.join(data.split('\\n')) + constants.TERMINATOR)


class MockChannel(asynchat.async_chat):
    def __init__(self, sock):
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator('')

    def collect_incoming_data(self, data):
        p(constants.TERMINATOR.join('\\n'.join(data.split(constants.DELIMITER)).split('\r\\n')))

    def found_terminator(self):
        pass


def p(msg):
    sys.stdout.write(msg)


def main():
    try:
        b = MockBrokerReceive(constants.HOST, constants.PORT)
        c = MockBrokerSend(b)
        asyncore.loop()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()

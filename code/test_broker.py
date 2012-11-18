'''
Created on Nov 17, 2012

@author: David Stevens
'''

import logging
import socket
import sys
import asynchat
import asyncore
import constants

logging.basicConfig(format=constants.LOG_FORMAT, level=logging.INFO)


class MockBrokerReceive(asyncore.dispatcher):
    '''This is half of a Mock Broker, spawning asynchats on connections.'''

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.channels = []
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            logging.warning("An accept returned nothing")
        else:
            sock, addr = pair
            self.channels.append(MockChannel(sock, addr))
            logging.info("Connected to " + repr(addr))


class MockBrokerSend(asyncore.file_dispatcher):
    '''This is half of a Mock Broker, sending what's in the console.'''

    def __init__(self, b):
        asyncore.file_dispatcher.__init__(self, sys.stdin)
        self.buffer = ''
        self.b = b

    def handle_read(self):
        self.buffer += self.recv(1024)
        if self.buffer.find(constants.DELIMITER):
            data, self.buffer = self.buffer.split(constants.DELIMITER, 1)
            data = (constants.DELIMITER.join(data.split('\\n')) +
                    constants.TERMINATOR)
            for channel in self.b.channels:
                logging.info("Pushing to " + repr(channel.addr))
                logging.debug("Data : " + repr(data))
                channel.push(data)


class MockChannel(asynchat.async_chat):
    '''This is a Mock Channel, printing what it receives to the console.'''

    def __init__(self, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.addr = addr
        self.buffer = ''
        self.set_terminator(1)

    def collect_incoming_data(self, data):
        self.buffer += data.replace('\n', '\\n')
        if not self.buffer.endswith('\r'):
            self.buffer = self.buffer.replace('\r\\n', '\r\n')
            sys.stdout.write(self.buffer)
            self.buffer = ''

    def found_terminator(self):
        pass

    def handle_close(self):
        logging.warning("Disconnected from " + repr(self.addr))
        self.close()


if __name__ == '__main__':
    import getopt
    import sys
    host = constants.HOST
    port = constants.PORT
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h:p:', ['host=', 'port='])
    except getopt.GetoptError:
        logging.warning("The system arguments are incorrect")
        logging.debug("Arguments : " + repr(opts))
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--host'):
            host = arg
        elif opt in ('-p', '--port'):
            port = int(arg)

    try:
        b = MockBrokerReceive(host, port)
        c = MockBrokerSend(b)
        asyncore.loop()
    except KeyboardInterrupt:
        sys.exit(0)

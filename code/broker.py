'''
Created on Nov 17, 2012

@author: David Stevens
'''

import logging
import sys
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import constants


class Connection(LineReceiver):
    def __init__(self, users):
        self.users = users

    def connectionMade(self):
        self.users.add(self)
        logging.info("Added self to users")
        logging.debug("Users : " + repr(self.users))
        self.addr = self.transport.getHost().host
        self.peer = self.transport.getPeer().host
        logging.info("Connected to " + repr(self.peer))

    def connectionLost(self, reason):
        logging.warning("Disconnected from " + repr(self.peer))
        if self in self.users:
            self.users.remove(self)
            logging.info("Removed self from users")
            logging.debug("Users : " + repr(self.users))

    def lineReceived(self, line):
        logging.info("Received Line from " + repr(self.peer))
        msg = line.strip().split(constants.DELIMITER)
        msg[1] = int(msg[1])
        self.name, self.flag = msg[:2]
        logging.info("Recieved Message with flag " +
                     constants.DIRECTORY_FLAG_TO_NAME[self.flag])
        logging.debug("Data : " + repr(msg))
        if self.flag == constants.REQUEST:
            self.sendLine(line)
        else:
            for user in self.users - set([self]):
                user.sendLine(line)
            if self.flag == constants.ADD_FILE:
                self.setRawMode()
                logging.info("Switching to raw mode")
                self.to_receive = int(msg[2])
                logging.info("Expecting {} bytes".format(self.to_receive))
                self.buffer = []
                self.buff_size = 0
                self.packet_size = min(constants.CHUNK_SIZE, self.to_receive)
                logging.debug('Next chunk size : {}'.format(self.packet_size))

    def rawDataReceived(self, data):
        self.buffer.append(data)
        self.buff_size += len(data)
        logging.debug("Buffer size : {}".format(self.buff_size))
        while self.buff_size >= self.packet_size:
            buff = ''.join(self.buffer)
            packet = buff[:self.packet_size] 
            for user in self.users - set([self]):
                logging.info("Sending chunk of size {} "
                             "to {}".format(len(packet),
                                            repr(user.peer)))
                user.transport.write(packet)
            self.to_receive -= self.packet_size
            logging.debug("{} bytes left to receive".format(self.to_receive))
            if self.to_receive == 0:
                logging.info("Switching to line mode")
                self.setLineMode(extra=buff[self.packet_size:])
                return
            else:
                self.buffer = [buff[self.packet_size:]]
                self.buff_size = len(self.buffer[0])
                logging.debug("New buffer size : {}".format(self.buff_size))
                self.packet_size = min(constants.CHUNK_SIZE,
                                       self.to_receive)
                logging.debug('Next chunk size : {}'.format(self.packet_size))

    def sendLine(self, line):
        logging.info("Sending Line to " + repr(self.peer))
        logging.debug("Line : " + repr(line))
        LineReceiver.sendLine(self, line)

#     def _handle_GET_FILENAME(self, name):
#         self.state = 'GET_FILENAME':
#         self.name = name
#         self.to_send = [name]
#         self.state = 'GET_FLAG'
#
#     def _hande_GET_FLAG(self, flag):
#         self.to_send.append(flag)
#         if flag in [constants.MOVE_FILE, constants.MOVE_FOLDER]:
#             self.state = 'GET_DEST'
#         elif flag == constants.ADD_FILE:
#             self.state = 'GET_SIZE'
#         else:
#             self.send_message()
#
#     def _handle_GET_DEST(self, arg):
#         self.to_send.append(arg)
#         self.send_message()
#
#     def _handle_GET_SIZE(self, arg):
#         self.to_send.append(arg)
#         self.send_message()
#         self.size = int(arg)
#         self.so_far = 0
#         self.setRawMode()


class BrokerFactory(Factory):
    def __init__(self):
        self.users = set()

    def buildProtocol(self, addr):
        return Connection(self.users)


if __name__ == "__main__":
    import getopt
    import sys
    port = constants.PORT
    loglevel = logging.INFO
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:l:v:',
                                   ['port=', 'logging=', 'verbose='])
    except getopt.GetoptError:
        logging.warning("The system arguments are incorrect")
        logging.debug("Arguments : " + repr(opts))
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-p', '--port'):
            port = int(arg)
        elif opt in ('-v', '-l', '--logging'):
            loglevel = 10 * (6 - int(arg))

    logging.basicConfig(format=constants.LOG_FORMAT, level=loglevel)

    reactor.listenTCP(port, BrokerFactory())
    reactor.run()

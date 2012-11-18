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

logging.basicConfig(format=constants.LOG_FORMAT, level=logging.INFO)


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
        logging.debug("Data : " + repr(line))
        msg = line.strip().split(constants.DELIMITER)
        msg[1] = int(msg[1])
        self.name, self.flag = msg[:2]
        logging.info("Recieved Message with flag " +
                     constants.DIRECTORY_FLAG_TO_NAME[self.flag])
        logging.debug("Data : " + repr(msg))
        if self.flag == constants.ADD_FILE:
            logging.info("Switching to raw mode")
            self.to_receive = int(msg[2])
            self.sent = 0
            self.setRawMode()
        # figure some stuff out here
        if self.flag == constants.REQUEST:
            self.sendLine(line)
        else:
            for user in self.users - set([self]):
                user.sendLine(line)

    def rawDataReceived(self, data):
        for user in self.users - set([self]):
            logging.info("Sending chunk of size " +
                         min(len(data), self.to_receive) + " to " +
                         repr(user.peer))
            logging.debug("Chunk : " + repr(data[:self.to_receive]))
            user.transport.write(data[:self.to_receive])
        if len(data) >= self.to_receive:
            logging.info("Switching to line mode")
            self.setLineMode(extra=data[self.to_receive:])
        else:
            self.to_receive -= len(data)

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
    reactor.listenTCP(constants.PORT, BrokerFactory())
    reactor.run()

'''
Created on Nov 17, 2012

@author: David Stevens
'''

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys
import constants


class Connection(LineReceiver):

    def __init__(self, users):
        self.users = users

    def connectionMade(self):
        self.users.add(self)
        self.addr = self.transport.getHost().host
        self.peer = self.transport.getPeer().host
        print('Connected to {}\n'.format(self.peer))
    
    def connectionLost(self, reason):
        if self in self.users:
            self.users.remove(self)
            print('Disconnected from {}\n'.format(self.peer))

    def lineReceived(self, line):
        print('Received: {} from {}\n'.format(repr(line), self.peer))
        msg = line.strip().split(constants.DELIMITER)
        self.name, self.flag = msg[0], int(msg[1])
        if self.flag == constants.ADD_FILE:
            self.to_receive = int(msg[2])
            self.sent = 0
            self.setRawMode()
            print('Recieving {} from {} and sending to peers\n'.format(self.name, self.addr, self.peer))
        # figure some stuff out here
        if self.flag == constants.REQUEST:
            print('Sending {} to {}\n'.format(line, self.peer))
            self.sendLine(line)
        else:
            for user in self.users - set([self]):
                print('Sending {} to {}\n'.format(repr(line), user.transport.getHost().host))
                user.sendLine(line)
    def rawDataReceived(self, data):
        for user in self.users - set([self]):
            user.transport.write(data[:self.to_receive])
        if len(data) >= self.to_receive:
            self.setLineMode(extra=data[self.to_receive:])
            print("File sent!")
        else:
            self.to_receive -= len(data)

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

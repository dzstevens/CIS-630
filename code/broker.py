'''
Created on Nov 17, 2012

@author: David Stevens
'''

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys
import constants

class Chat(LineReceiver):

    def __init__(self, users):
        self.users = users
        self.users.add(self)
        self.state = 'GET_FILENAME'

    def connectionMade(self):
        print('Connected to {}'.format(self.transport.getHost().host))
        self.sendLine('Welcome!')

    def connectionLost(self, reason):
        if self.name in self.users:
            self.users.remove(self)
            print('Disconnected from {}'.format(self.transport.getHost().host))

    def lineReceived(self, line):
        msg = line.strip().split('\n')
        self.name, self.flag = msg[0], int[msg[1]]
        if flag | constants.MOVE_FILE:
            self.dest = msg[2]
        elif flag == constants.ADD_FILE:
            self.to_receive = int(msg[2])
            self.sent = 0
            self.setRawMode()
        # figure some stuff out here
        if flag == constants.REQUEST:
            self.sendline(line)
        else:
            for users in users - self:
                user.sendline(line)

    def rawDataRecieved(self, data):
        for user in self.users - self:
            user.transport.write(data[:self.to_receive])
        if len(data) >= self.to_recieve:
            self.setLineMode(extra=data[self.to_receive:])
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


reactor.listenTCP(5555, BrokerFactory())
reactor.run()
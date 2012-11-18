'''
Created on Nov 17, 2012

@author: David Stevens
'''

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor


class Chat(LineReceiver):

    def __init__(self, users):
        self.users = users
        self.users.add(self)

    def connectionMade(self):
        self.sendLine("Welcome!")

    def connectionLost(self, reason):
        if self.users.has_key(self.name):
            self.users.remove(self)

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)

    def handle_GETNAME(self, name):
        if self.users.has_key(name):
            self.sendLine("Name taken, please choose another.")
            return
        self.sendLine("Welcome, %s!" % (name,))
        self.name = name
        self.users[name] = self
        self.state = "CHAT"

    def handle_CHAT(self, message):
        message = "<%s> %s" % (self.name, message)
        for name, protocol in self.users.iteritems():
            if protocol != self:
                protocol.sendLine(message)


class BrokerFactory(Factory):
    def __init__(self):
        self.users = set()

    def buildProtocol(self, addr):
        return Connection(self.users)


reactor.listenTCP(5555, BrokerFactory())
reactor.run()

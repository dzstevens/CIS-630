'''
Created on Nov 17, 2012

@author: David Stevens
'''

import logging, random, sys
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import constants


class Connection(LineReceiver):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.users[self] = self.factory.next_id()
        self.id = self.factory.users[self]
        logging.info("Connected to user {}".format(self.id))
        logging.debug("Users : {}".format(self.factory.users.values()))
        self.policy = self.receive_line

    def connectionLost(self, reason):
        logging.warning("User {} has disconnected".format(self.id))
        if self in self.factory.users:
            del self.factory.users[self]
            logging.info("Removed user {} from users".format(self.id))
            logging.debug("Users : {}".format(self.factory.users.values()))

    def lineReceived(self, line):
        logging.info("Received Line from user {}".format(self.id))
        self.policy(line)

    def receive_line(self, line):
        msg = line.strip().split(constants.DELIMITER)
        msg[1] = int(msg[1])
        name, flag = msg[:2] # need reserved name for batch request
        logging.info("Received Message "
                     "with flag {}".format(constants.FLAG_TO_NAME[flag]))
        logging.debug("Data : {}".format(repr(msg)))
        if flag == constants.BATCH:
            self.batch_count = int(msg[2])
            logging.debug("Batch Count : {}".format(self.batch_count))
            
            self.time_stamps_copy = self.factory.time_stamps.copy()
            logging.debug("Time stamp dict copy: "
                          "{}".format(self.time_stamps_copy))
            if self.batch_count == 0:
                for file_name in self.time_stamps_copy:
                     self.fetch_change(file_name)
            else:
                logging.debug("Switching to batch mode")
                self.policy = self.batch_receive
        elif flag == constants.REQUEST:
            logging.debug("Sending back line '{}' "
                          "to user {}".format(repr(line), self.id))
            self.sendLine(line)
        else:
            self.send_change(line, msg, flag)

    def batch_receive(self, line):
        msg = line.strip().split(constants.DELIMITER)
        msg[1] = int(msg[1])
        name, flag = msg[:2]
        logging.info("Received Message "
                     "with flag {}".format(constants.FLAG_TO_NAME[flag]))
        logging.debug("Data : {}".format(repr(msg)))
        time_stamp = int(msg[2])
        logging.debug("Time stamp for incoming file "
                      "'{}': {}".format(name,time_stamp))
        if flag == constants.REQUEST:
            current = self.time_stamps_copy.get(name)
            if current is not None:
               logging.debug("Current time stamp for file "
                             "'{}': {}".format(name, current))
               if current > time_stamp:
                   self.fetch_change(name)
               elif current < time_stamp:
                   self.sendLine(line)
               logging.debug("Deleting {} from time stamps copy".format(name))
               del self.time_stamps_copy[name]
               logging.debug("Time stamp dict copy: "
                             "{}".format(self.time_stamps_copy))
            else:
                logging.debug("'{}' is new, requesting change".format(name))
                self.sendLine(line)
            self.batch_count -= 1
            logging.debug("Batch Count : {}".format(self.batch_count))
            if self.batch_count == 0:
                for file_name in self.time_stamps_copy:
                     self.fetch_change(file_name)
                logging.debug("Switching back to default receive mode")
                self.policy = self.receive_line

    def fetch_change(self, file_name):
        user = random.choice(set(self.factory.users) - set([self]))
        logging.info("Fetching change for file "
                     "{} from user {}".format(file_name, user.id))
        msg = [file_name, str(constants.REQUEST),
               str(self.factory.time_stamps[file_name]), str(user.id)]
        logging.debug("Sending message: "
                      "'{}'}".format(repr(constants.DELIMITER.join(msg))))
        user.sendLine(constants.DELIMITER.join(msg))
    
    def send_change(self, line, msg, flag):
        if flag == constants.ADD_FILE and len(msg) == 5:
            self.recipients = [self.factory.users[int(msg[4])]]
            msg = msg[:-1]
        elif flag != constants.ADD_FILE and len(msg) == 4:
            self.recipients = [self.factory.users[int(msg[3])]]
            msg = msg[:-1]
        else:
            self.recipients = set(self.factory.users) - set([self])
        logging.debug("Sending '{}' to users: "
                      "{}".format(repr(line), [user.id for user in
                                               self.recipients]))
        for user in self.recipients:
            user.sendLine(line)
        logging.debug("Updating time stamp for "
                      "'{}' to {}".format(msg[0], msg[2]))
        self.factory.time_stamps[msg[0]] = int(msg[2])
        if flag == constants.ADD_FILE:
            self.setRawMode()
            logging.info("Switching to raw mode")
            self.to_receive = int(msg[3])
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
            for user in self.recipients:
                logging.info("Sending chunk of size {} "
                             "to user {}".format(len(packet), user.id))
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
        logging.info("Sending Line to user {}".format(self.id))
        logging.debug("Line : {}".format(repr(line)))
        LineReceiver.sendLine(self, line)


class BrokerFactory(Factory):
    def __init__(self):
        self.users = dict()
        self.time_stamps = dict()
        self.counter = 0

    def buildProtocol(self, addr):
        return Connection(self)
    
    def next_id(self):
        self.counter += 1
        return self.counter - 1

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

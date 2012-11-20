'''
Created on Nov 17, 2012

@author: David Stevens
'''

import asynchat
import asyncore
import errno
import logging
import os
import re
import shutil
import socket
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import constants


class LocalFilesEventHandler(FileSystemEventHandler):
    '''Handles events in the file system and passes it to the channel'''

    def __init__(self, dirname):
        FileSystemEventHandler.__init__(self)
        self.dirname = dirname
        self.changes = {}
        self.just_changed = {}
        self.valid = re.compile(r'^(.+/)*[^\./][^/]*$')

    def handle_change(self, filename, change):
        filename = os.path.relpath(filename, self.dirname)
        if self.valid.match(filename):
            logging.info("Change happened to " + repr(filename))
            logging.debug("Data : " +
                          constants.DIRECTORY_FLAG_TO_NAME[change])
            if not self.just_changed.get(filename):
                if filename not in self.changes:
                    self.channel.push(filename + constants.DELIMITER +
                                      str(constants.REQUEST) +
                                      constants.TERMINATOR)
                self.changes[filename] = change
            else:
                logging.info("Unmark " + repr(filename) +
                             " as being just changed")
                self.just_changed[filename] = False
        else:
            logging.info("Ignoring change to " + repr(filename))
            logging.debug("Data : " +
                          constants.DIRECTORY_FLAG_TO_NAME[change])

    def on_created(self, event):
        self.handle_change(event.src_path, (constants.ADD_FILE |
                                            event.is_directory))

    def on_deleted(self, event):
        self.handle_change(event.src_path, (constants.DELETE_FILE |
                                            event.is_directory))

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_change(event.src_path, (constants.ADD_FILE))

    def on_moved(self, event):
        self.handle_change(event.src_path, (constants.DELETE_FILE |
                                            event.is_directory))
        self.handle_change(event.dest_path, (constants.ADD_FILE |
                                             event.is_directory))

    def take_change(self, filename):
        if filename in self.changes:
            change = self.changes[filename]
            del self.changes[filename]
            return (change,)
        else:
            logging.warning(repr(filename) + " was never set to change")
            if os.path.exists(self.dirname + filename):
                if os.path.isdir(self.dirname + filename):
                    logging.warning("Spoofing ADD_FOLDER")
                    return (constants.ADD_FOLDER,)
                else:
                    logging.warning("Spoofing ADD_FILE")
                    return (constants.ADD_FILE,)
            else:
                logging.warning(repr(filename) + " does not exist")
                logging.warning("Spoofing DELETE_FILE")
                logging.warning("Spoofing DELETE_FOLDER")
                return (constants.DELETE_FILE, constants.DELETE_FOLDER)
            


class BrokerChannel(asynchat.async_chat):
    '''The channel that deals with sending and receiving to the broker.'''

    def __init__(self, dirname, host, port):
        asynchat.async_chat.__init__(self)
        self.dirname = dirname
        self.process_data = self.process_message
        self.received_data = []
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.set_terminator(constants.TERMINATOR)

    def push(self, data):
        logging.info("Pushed Data")
        logging.debug("Data : " + repr(data))
        asynchat.async_chat.push(self, data)

    def push_with_producer(self, producer):
        logging.info("Pushed Producer ")
        logging.debug("Data : " + repr(producer))
        asynchat.async_chat.push_with_producer(self, producer)

    def collect_incoming_data(self, data):
        logging.info("Received Data")
        logging.debug("Data : " + repr(data))
        self.received_data.append(data)

    def found_terminator(self):
        logging.info("Processing Data")
        self.process_data()

    def process_message(self):
        token = self.get_token()
        msg = token.split(constants.DELIMITER)
        msg[1] = int(msg[1])
        filename, flag = msg[:2]
        logging.info("Recieved Message with flag " +
                     constants.DIRECTORY_FLAG_TO_NAME[flag])
        logging.debug("Data : " + repr(msg))
        if flag == constants.REQUEST:
            self.handle_push_change(filename)
        else:
            self.handle_receive_change(msg)

    def process_file(self):
        token = self.get_token()
        logging.info("Receiving File Data" + repr(self.file.name) +
                     " with size " + str(len(token)))
        logging.debug("Data : " + repr(token))
        self.file.write(token)
        self.remaining_size -= len(token)
        if self.remaining_size > 0:
            self.set_terminator(min(self.remaining_size, constants.CHUNK_SIZE))
        else:
            logging.info("Closing " + repr(self.file.name))
            self.file.close()
            self.set_terminator(constants.TERMINATOR)
            self.process_data = self.process_message

    def get_token(self):
        token = ''.join(self.received_data)
        self.received_data = []
        return token

    def handle_close(self):
        logging.warning("Disconnected")
        self.close()

    def handle_connect(self):
        logging.info("Connected")

    def handle_push_change(self, filename):
        flags = self.event_handler.take_change(filename)
        for flag in flags:
            self.push(filename + constants.DELIMITER + str(flag))
            if flag == constants.ADD_FILE:
                self.push(constants.DELIMITER +
                          str(os.stat(self.dirname + filename).st_size) +
                          constants.TERMINATOR)
                self.push_with_producer(FileProducer(self.dirname + filename))
            else:
                self.push(constants.TERMINATOR)

    def handle_receive_change(self, msg):
        flag = msg[1]
        if flag & constants.ADD_FILE:
            self.handle_receive_add(msg)
        elif flag & constants.DELETE_FILE:
            self.handle_receive_delete(msg)

    def handle_receive_add(self, msg):
        filename, flag = msg[:2]
        logging.info("Getting Add " + repr(filename))
        try:
            if flag & constants.FOLDER:
                logging.info("Mark " + repr(filename) +
                             " as being just changed")
                self.event_handler.just_changed[filename] = True
                os.mkdir(self.dirname + filename)
            else:
                logging.info("Opening " + repr(filename))
                self.file = open(self.dirname + filename, 'w')
                logging.info("Mark " + repr(filename) +
                             " as being just changed")
                self.event_handler.just_changed[filename] = True
                self.remaining_size = int(msg[2])
                self.process_data = self.process_file
                self.set_terminator(min(self.remaining_size,
                                        constants.CHUNK_SIZE))
        except OSError as e:
            if e.errno == errno.EEXIST:
                logging.warning(str(e))
                logging.debug("Exception : " + repr(e))
            else:
                logging.error(str(e))
                logging.debug("Exception : " + repr(e))
                raise
        except Exception as e:
            logging.error(str(e))
            logging.debug("Exception : " + repr(e))
            raise

    def handle_receive_delete(self, msg):
        filename, flag = msg[:2]
        logging.info("Getting Delete " + repr(filename))
        try:
            if flag & constants.FOLDER:
                logging.info("Mark " + repr(filename) +
                             " as being just changed")
                self.event_handler.just_changed[filename] = True
                shutil.rmtree(self.dirname + filename)
            else:
                logging.info("Mark " + repr(filename) +
                             " as being just changed")
                self.event_handler.just_changed[filename] = True
                os.remove(self.dirname + filename)
        except OSError as e:
            if e.errno == errno.ENOENT:
                logging.warning(str(e))
                logging.debug("Exception : " + repr(e))
            else:
                logging.error(str(e))
                logging.debug("Exception : " + repr(e))
                raise
        except Exception as e:
            logging.error(str(e))
            logging.debug("Exception : " + repr(e))
            raise


class FileProducer:
    '''This produces a file in chunks.'''

    def __init__(self, name):
        logging.info("Opening Producer's File")
        self.file = open(name)

    def more(self):
        if self.file:
            try:
                data = self.file.read(constants.CHUNK_SIZE)
                if data:
                    logging.info("Produced with size " + str(len(data)))
                    logging.debug("Producer : " + repr(self))
                    logging.debug("Data : " + repr(data))
                    return data
                logging.info("Closing Producer's File")
                self.file.close()
                self.file = None
            except IOError as e:
                logging.warning(str(e))
                logging.debug("Exception : " + repr(e))
                self.file.close()
            except Exception as e:
                logging.error(str(e))
                logging.debug("Exception : " + repr(e))
                self.file.close()
                raise
        logging.info("Produced with size 0")
        logging.debug("Producer : " + repr(self))
        logging.debug("Data : " + repr(""))
        return ""


if __name__ == "__main__":
    import getopt
    import sys
    dirname = './'
    host = constants.HOST
    port = constants.PORT
    loglevel = logging.INFO
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:h:p:l:v:',
                                   ['dir=', 'host=', 'port=', 'logging=',
                                    'verbose='])
    except getopt.GetoptError:
        logging.warning("The system arguments are incorrect")
        logging.debug("Arguments : " + repr(opts))
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-d', '--dir'):
            dirname = arg
        elif opt in ('-h', '--host'):
            host = arg
        elif opt in ('-p', '--port'):
            port = int(arg)
        elif opt in ('-v', '-l', '--logging'):
            loglevel = 10 * (6 - int(arg))

    if not dirname.endswith('/'):
        dirname += '/'

    logging.basicConfig(format=constants.LOG_FORMAT, level=loglevel)

    observer = Observer()
    event_handler = LocalFilesEventHandler(dirname)
    channel = BrokerChannel(dirname, host, port)

    event_handler.channel = channel
    channel.event_handler = event_handler
    observer.schedule(event_handler, dirname, True)

    observer.start()
    asyncore.loop()

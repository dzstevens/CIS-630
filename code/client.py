import asynchat
import asyncore
import errno
import os
import shutil
import socket

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import constants


class LocalFilesEventHandler(FileSystemEventHandler):
    def __init__(self, dirname):
        FileSystemEventHandler.__init__(self)
        self.dirname = dirname
        self.changes = {}

    def handle_change(self, filename, change):
        filename = os.path.relpath(filename, self.dirname)
        if filename not in self.changes:
            self.channel.push(filename + constants.DELIMITER +
                              str(constants.REQUEST) + constants.TERMINATOR)
        self.changes[filename] = change

    def on_created(self, event):
        self.handle_change(event.src_path, (constants.ADD_FILE |
                                            event.is_directory,))

    def on_deleted(self, event):
        self.handle_change(event.src_path, (constants.DELETE_FILE |
                                            event.is_directory,))

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_change(event.src_path, (constants.ADD_FILE,))

    def on_moved(self, event):
        self.handle_change(event.src_path, (constants.DELETE_FILE |
                                            event.is_directory,))
        self.handle_change(event.dest_path, (constants.ADD_FILE |
                                             event.is_directory,))

    def take_change(self, filename):
        change = self.changes[filename]
        del self.changes[filename]
        return change


class BrokerChannel(asynchat.async_chat):
    def __init__(self, dirname, host, port):
        asynchat.async_chat.__init__(self)
        self.dirname = dirname
        self.process_data = self.process_message
        self.received_data = []
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.set_terminator(constants.TERMINATOR)

    def collect_incoming_data(self, data):
        self.received_data.append(data)

    def found_terminator(self):
        self.process_data()

    def process_message(self):
        token = self.get_token()
        msg = token.split(constants.DELIMITER)
        msg[1] = int(msg[1])
        filename, flag = msg[:2]
        if flag == constants.REQUEST:
            self.handle_push_change(filename)
        else:
            self.handle_receive_change(msg)

    def process_file(self):
        token = self.get_token()
        self.file.write(token)
        self.remaining_size -= len(token)
        if self.remaining_size > 0:
            self.set_terminator(min(self.remaining_size, constants.CHUNK_SIZE))
        else:
            self.file.close()
            self.set_terminator(constants.TERMINATOR)
            self.process_data = self.process_message

    def get_token(self):
        token = ''.join(self.received_data)
        self.received_data = []
        return token

    def handle_close(self):
        self.close()

    def handle_connect(self):
        pass

    def handle_push_change(self, filename):
        change = self.event_handler.take_change(filename)
        flag = change[0]
        self.push(filename + constants.DELIMITER + str(flag))
        if flag == constants.ADD_FILE:
            self.push(constants.DELIMITER + str(os.stat(self.dirname + filename).st_size)
                      + constants.TERMINATOR)
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
        try:
            if flag & constants.FOLDER:
                os.mkdir(self.dirname + filename)
            else:
                self.file = open(self.dirname + filename)
                self.remaining_size = int(msg[2])
                self.process_data = self.process_file
                self.set_terminator(min(self.remaining_size,
                                        constants.CHUNK_SIZE))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def handle_receive_delete(self, msg):
        filename, flag = msg[:2]
        try:
            if flag & constants.FOLDER:
                shutil.rmtree(self.dirname + filename)
            else:
                os.remove(self.dirname + filename)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


class FileProducer:
    def __init__(self, name):
        self.file = open(name)

    def more(self):
        if self.file:
            try:
                data = self.file.read(constants.CHUNK_SIZE)
                if data:
                    return data
                self.file.close()
                self.file = None
            except:
                self.file.close()
        return ""


if __name__ == "__main__":
    import sys

    dirname = sys.argv[1] if len(sys.argv) >= 2 else '.'
    host = sys.argv[2] if len(sys.argv) >= 3 else constants.HOST
    port = int(sys.argv[3]) if len(sys.argv) >= 4 else constants.PORT

    if not dirname.endswith('/'):
        dirname += '/'

    observer = Observer()
    event_handler = LocalFilesEventHandler(dirname)
    channel = BrokerChannel(dirname, host, port)

    event_handler.channel = channel
    channel.event_handler = event_handler
    observer.schedule(event_handler, dirname, True)

    observer.start()
    asyncore.loop()

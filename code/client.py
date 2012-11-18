import asynchat
import asyncore
import socket
from fcntl import lockf, LOCK_EX, LOCK_NB
from os import path, stat

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import constants


class LocalFilesEventHandler(FileSystemEventHandler):
    def __init__(self, dirname):
        FileSystemEventHandler.__init__(self)
        self.dirname = dirname
        self.changes = {}

    def handle_change(self, filename, change):
        filename = path.relpath(filename, self.dirname)
        if filename not in self.changes:
            self.channel.push(filename + constants.DELIMITER)
            self.channel.push(str(constants.REQUEST) + constants.DELIMITER)
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
        self.handle_change(event.src_path, (constants.MOVE_FILE |
                                            event.is_directory,
                                            event.destination))

    def take_change(self, filename):
        change = self.changes[filename]
        del self.changes[filename]
        return change


class BrokerChannel(asynchat.async_chat):
    def __init__(self, host, port):
        asynchat.async_chat.__init__(self)
        self.process_data = self._state_start
        self.received_data = []
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.set_terminator(constants.DELIMITER)

    def handle_connect(self):
        pass

    def collect_incoming_data(self, data):
        self.received_data.append(data)

    def found_terminator(self):
        self.process_data()

    def get_token(self):
        token = ''.join(self.received_data)
        self.received_data = []
        return token

    def handle_close(self):
        self.close()

    def _state_start(self):
        self.filename = self.get_token()
        self.process_data = self._state_have_filename

    def _state_have_filename(self):
        self.flag = int(self.get_token())
        if self.flag == constants.REQUEST:
            self._push_change()
        else:
            self._handle_receive_change()

    def _push_change(self):
        change = self.event_handler.take_change(self.filename)
        self.flag = change[0]
        self.push(self.filename + constants.DELIMITER)
        self.push(str(self.flag) + constants.DELIMITER)
        if self.flag & constants.MOVE_FILE:
            self.push(change[1] + constants.DELIMITER)
        elif self.flag == constants.ADD_FILE:
            self.push(str(stat(self.filename).st_size) + constants.DELIMITER)
            self.push_with_producer(FileProducer(self.filename))
        del self.flag
        del self.filename
        self.process_data = self._state_start
    
    def _handle_receive_change(self):
        del self.flag
        del self.filename
        self.process_data = self._state_start


class FileProducer:
    def __init__(self, name):
        self.file = open(name)

    def more(self):
        if self.file:
            data = self.file.read(constants.CHUNK_SIZE)
            if data:
                return data
            self.file.close()
            self.file = None
        return ""


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        dirname = sys.argv[1]
    else:
        dirname = '.'

    observer = Observer()
    event_handler = LocalFilesEventHandler(dirname)
    channel = BrokerChannel(constants.HOST, constants.PORT)

    event_handler.channel = channel
    channel.event_handler = event_handler
    observer.schedule(event_handler, dirname, True)

    observer.start()
    asyncore.loop()

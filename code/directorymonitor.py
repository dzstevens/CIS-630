from os import path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import EventDispatcher
import constants


class LocalFilesObserver(Observer):
    def __init__(self, dirname):
        Observer.__init__(self)
        event_handler = LocalFilesEventHandler(dirname)
        self.schedule(event_handler, path=filename, recursive=True)


class LocalFilesEventHandler(FileSystemEventHandler):
    def __init__(self, dirname):
        self.__dirname = dirname

    def on_created(self, event):
        self.handle_change(event.src_path, (constants.ADD_FILE_FLAG |
                                            event.is_directory))

    def on_deleted(self, event):
        self.handle_change(event.src_path, (constants.DELETE_FILE_FLAG |
                                            event.is_directory))

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_change(event.src_path, constants.ADD_FILE_FLAG)

    def on_moved(self, event):
        self.handle_change(event.src_path, (constants.MOVE_FILE_FLAG |
                                            event.is_directory,
                                            event.dest_path))

    def handle_change(self, filename, flag, destination=None):
        filename = path.relpath(filename, self.__dirname)
        if destination is None:
            print filename, flag
        else:
            destination = path.relpath(destination, self.__dirname)
            print filename, flag, destination

if __name__ == "__main__":
    import sys
    import time
    if len(sys.argv) >= 2:
        dirname = sys.argv[1]
    else:
        dirname = '.'
    observer = LocalFilesObserver(dirname)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print

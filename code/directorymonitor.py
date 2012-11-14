import os
from threading import Thread, Lock, Event
class DirectoryMonitorThread(Thread):
  def __init__(self,monitored_directory,client_to_broker_thread):
    Thread.__init__(self)
    self.monitored_directory = monitored_directory
    self.client_to_broker_thread = client_to_broker_thread # RENAME?

  def run(self):
    initiated = False
    while not initiated:
      try:
        current_files = dict([(file,os.stat(self.monitored_directory + file)) for file in os.listdir(self.monitored_directory)])
        initiated = True
      except os.error:
        continue
    while True: #continually pull in new view of directory and handle changes from previous view
      try:
        new_files = dict([(file,os.stat(self.monitored_directory + file)) for file in os.listdir(self.monitored_directory)])
      except os.error:
        continue #catch funkiness with os.stat
      deleted_files = set(current_files) - set(new_files)
      for file in deleted_files:
        self.client_to_broker_thread.write_deletion(file)
      for file,last_modified in new_files.items():
        try:
          if last_modified > current_files[file]:
            self.client_to_broker_thread.write_modification(file) #file changed
        except KeyError:
          self.client_to_broker_thread.write_addition(file)
      current_files = new_files


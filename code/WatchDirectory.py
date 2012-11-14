import os
from threading import Thread, Lock, Event
class WatchDirectoryThread(Thread):
  def __init__(self,watch_directory,client_write_thread):
    self.watch_directory = watch_directory
    self.client_write_thread = client_write_thread # RENAME?

  def run(self):
    initiated = False
    while not initiated:
      try:
        current_file_dict = dict([(file,os.stat(self.watch_directory + file)) for file in os.listdir(self.watch_directory)])
        initiated = True
      except os.error:
        continue
    while True: #continually pull in new view of directory and handle changes from previous view
      try:
        new_file_dict = dict([(file,os.stat(self.watch_directory + file)) for file in os.listdir(self.watch_directory)])
      except os.error:
        continue #catch funkiness with os.stat
      for file,last_modified in new_file_dict.items():
        if file in current_file_dict.keys() and last_modified > current_file_dict[file]:
          self.client_write_thread.write_modification(file) #file changed
        elif file not in current_file_dict.keys(): 
          self.client_write_thread.write_new_file(file) #new file
        try:
          del current_file_dict[file]
        except KeyError:
          pass
      for deleted_file in current_file_dict.keys(): #deleted files
        self.client_write_thread.write_deleted_file(deleted_file)
      current_file_dict = new_file_dict


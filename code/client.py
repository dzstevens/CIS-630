#Code for the client nodes.
#needs to have an init => promptly pull and push

import os

class Client:

  def __init__(self,broker,local_dir):
    #self.write_socket
    #initiate connection to broker
    self.local_directory = local_dir

  def watch_directory(self):
    current_file_dict = dict([(file,os.stat(self.local_directory + file)) for file in os.listdir(self.local_directory)])
    print "current", current_file_dict
    while True:
      try:
        new_file_dict = dict([(file,os.stat(self.local_directory + file)) for file in os.listdir(self.local_directory)])
      except os.error:
        continue
      if new_file_dict.keys() != current_file_dict.keys():
        print "addition or deletion"
      for file,last_modified in new_file_dict.items():
        if file in current_file_dict.keys() and last_modified > current_file_dict[file]:
          print file, " was modified"
      current_file_dict = new_file_dict

x= Client('broker','/Users/krazkorean/Desktop/cis630/test/')
x.watch_directory()

#Code for the client nodes.
#needs to have an init => promptly pull and push

import os
from WatchDirectory import WatchDirectoryThread
import socket
from threading import Thread, Lock, Event

class WriteThread(Thread):
  def __init(self,broker,sock=None):
    if sock is None:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
      self.sock = sock
    self.broker = broker

  def run(self):
    print("Write thread is running")
#send request to broker
#block until response=ok
#send thing
#block until good
  
  def connect(self, host, port):
    self.sock.connect((broker.host,broker.port))

  def write_modification(self,modified_file):
    print(modified_file," was modified")
  def write_new_file(self,new_file):
    print("New file: ", new_file)
  def write_deleted_file(self,deleted_file):
    print("Deleted file: ", deleted_file)

class Client:

  def __init__(self,local_dir,broker = None):

    #initiate connection to broker
    self.local_directory = local_dir
    self.write_thread = WriteThread()
    self.write_thread.run()
    #self.read_thread

    self.watch_directory_thread = WatchDirectoryThread(self.local_directory,self.write_thread)
    self.watch_directory_thread.run()

x= Client('/Users/krazkorean/Desktop/cis630/test/')

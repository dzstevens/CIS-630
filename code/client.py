#Code for the client nodes.
#needs to have an init => promptly pull and push

import os
from WatchDirectory import WatchDirectoryThread
import socket
from threading import Thread, Lock, Event

class ClientToBrokerThread(Thread):
  def __init__(self,broker,client_id,sock=None):
    if sock is None:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
      self.sock = sock
    self.broker = broker
    self.client_id = client_id
  
  def run(self):
    self.output("Client to broker thread is running")
  
  def connect(self):
    self.sock.connect((self.broker.host,self.broker.port))

  def write_modification(self,modified_file):
    self.output(str(modified_file) + " was modified")
    self.connect()
    #send modification to broker

  def write_new_file(self,new_file):
    self.output("New file: " + str(new_file))
    self.connect()
    #send new file to broker

  def write_deleted_file(self,deleted_file):
    self.output("Deleted file: " + str(deleted_file))
    self.connect()
    #send deleted to broker

  def read(self):
    self.output("Attempting to read updates")
  
  def output(self,message):
    print("#",self.client_id,"# ",message)

class BrokerToClientThread(Thread):
  def __init__(self,local_directory,sock=None):
    self.local_directory = local_directory
    if sock is None:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
      self.sock = sock
    self.port = 8000 #how to check if ok?

  def run(self):
    print("Broker to client thread is running")
    while True:
      self.sock.bind(('127.0.0.1',self.port))
      self.sock.listen(5)
      print("Waiting for connection..")
      connection, address = self.sock.accept()
      while True:
        data = connection.recv(1024)
        if not data: break
      connection.close()

class Client:

  def __init__(self,client_id,local_dir,broker = None):

    #initiate connection to broker
    #broker exists already, just need to connect to it
    self.client_id = client_id

    self.local_directory = local_dir
    self.client_to_broker_thread = ClientToBrokerThread(broker,self.client_id)
    self.client_to_broker_thread.setDaemon()
    self.client_to_broker_thread.run()

    self.watch_directory_thread = WatchDirectoryThread(self.local_directory,self.client_to_broker_thread)
    self.watch_directory_thread.run()
    self.broker_to_client_thread = BrokerToClientThread(local_directory)
    self.broker_to_client_thread.run()


x= Client(1,'/Users/krazkorean/Desktop/cis630/test/')

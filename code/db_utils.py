import sqlite3
import constants
import logging
import sys
import os

class ClientRecord:
  '''Handles all transactions between client and local record'''

  def __init__(self,record_source,loglevel = 1):
    '''Create DB, connection, table'''
    logging.basicConfig(format=constants.LOG_FORMAT, level=loglevel)
    try:
      self.conn = sqlite3.connect(constants.CLIENT_RECORD_DIR + record_source)
      self.cursor = self.conn.cursor()
      self.cursor.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL UNIQUE, sequencenum INTEGER NOT NULL, timestamp DEFAULT CURRENT_TIMESTAMP);")
      #PE filename: on conflict replace? or handle in code?
    except sqlite3.Error, e:
      logging.warning('Unable to connect to local record: {}'.format(constants.CLIENT_RECORD_DIR + record_source))
      logging.debug(e.message)
      sys.exit(2)
    logging.info('Client connected to local record: {}'.format(constants.CLIENT_RECORD_DIR + record_source))

  def get_sequencenum(self,filename):
    '''Retrieve the sequence number of the given file, return -1 on failure'''
    logging.debug("getting seqnum for: {}".format(filename))
    try:
      sequence_num = self.cursor.execute("SELECT sequencenum FROM records WHERE filename='{}';".format(filename)).fetchone()
    except sqlite3.Error, e:
      logging.warning('Failed to retrieve sequencenum for: {}'.format(filename))
      logging.debug(e.message)
      return -1
    
    if sequence_num: 
      return sequence_num[0]
    else:
      logging.debug("{} not in records, creating".format(filename))
      return self.create_record(filename)

  def update_sequencenum(self, filename, new_sequencenum=None):
    '''Update the sequence number of the given record, return 0 on success, -1 on fail'''
    logging.debug("updating sequencenum for {}, using {}".format(filename,new_sequencenum))
    try:
      sequencenum = self.cursor.execute("SELECT sequencenum FROM records WHERE filename='{}';".format(filename)).fetchone()
    except sqlite3.Error, e:
      logging.warning('Something went wrong')
      logging.debug(e.message)
      return -1
    if sequencenum:
      try:
        logging.debug("record exists, updating seqnum")
        sequencenum = new_sequencenum if new_sequencenum else sequencenum[0]+1 #either update to new sequence number or increment
        self.cursor.execute("UPDATE records SET sequencenum={} WHERE filename='{}';".format(sequencenum,filename))
        self.conn.commit()
        return 0
      except sqlite3.Error, e:
        logging.warning('Failed to update sequencenum')
        logging.debug(e.message)
        return -1
    else:
      logging.debug("{} not in records, creating with seqnum: {}".format(filename,sequencenum))
      return self.create_record(filename,new_sequencenum)

  def create_record(self, filename, sequencenum=0):
    '''Create a new record, return 0 on success, -1 on failure'''
    logging.debug("creating record for {}".format(filename))
    try:
      self.cursor.execute("INSERT INTO records(filename,sequencenum) VALUES('{}',{});".format(filename,sequencenum))
      self.conn.commit()
      return 0
    except sqlite3.Error, e:
      logging.warning('Failed to create record: {}'.format(filename))
      logging.debug(e.message)
      return -1

  def delete_directory_records(self,filename):
    '''Deletes an entire directory's records, return 0 on success, -1 on failure'''
    logging.debug("deleting directory: {}".format(filename))
    directory_to_delete = filename.split('/')[0] + '/%'
    try:
      self.cursor.execute("DELETE FROM records WHERE filename='{}' or filename LIKE '{}';".format(filename,directory_to_delete))
      self.conn.commit()
      return 0
    except sqlite3.Error, e:
      logging.warning('Failed to delete directory record: {}'.format(filename))
      logging.debug(e.message)
      return -1

  def delete_record(self,filename):
    '''Deletes a record, return 0 on success, -1 on failure'''
    logging.debug("deleting record: {}".format(filename))
    try:
      self.cursor.execute("DELETE FROM records WHERE filename='{}';".format(filename))
      self.conn.commit()
      return 0
    except sqlite3.Error, e:
      logging.warning('Failed to delete record: {}'.format(filename))
      logging.debug(e.message)
      return -1

if __name__ == '__main__':
  import sys
  if len(sys.argv) < 2:
    print "USAGE: python db_utils.py <record>"
    sys.exit(1)
  record_source = sys.argv[1]
  test_client_record = ClientRecord(record_source,10)
  input = ""
  while input != "EXIT":
    input = raw_input("Enter 'C' to create, 'DD' to delete dir, 'D' to delete, 'G' to get seqnum, 'U' to update seqnum, 'EXIT' to quit: ")
    if input == 'C':
      filename = raw_input("Enter filename to create: ")
      test_client_record.create_record(filename)
    if input == 'DD':
      filename = raw_input("Enter directory to delete: ")
      test_client_record.delete_directory_records(filename)
    if input == 'D':
      filename = raw_input("Enter filename to delete: ")
      test_client_record.delete_record(filename)
    if input == 'G':
      filename = raw_input("Enter filename to retrieve: ")
      print "Retrieved: ", test_client_record.get_sequencenum(filename)
    if input == 'U':
      filename = raw_input("Enter filename to update: ")
      sequencenum = raw_input("Enter optional seqnum, or None: ")
      if sequencenum == "None":
        test_client_record.update_sequencenum(filename)
      else:
        test_client_record.update_sequencenum(filename,int(sequencenum))
    if input == 'EXIT':
      print "QUITTING"
      sys.exit(0)
    

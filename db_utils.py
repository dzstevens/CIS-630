'''
Created on Nov 26, 2012

@author: Paul Elliott
'''

import sqlite3
import logging
import sys
import os
from datetime import datetime

import constants

class ClientRecord:
    '''Handles all transactions between client and local record'''

    def __init__(self,record_source,loglevel = 1):
        '''Create DB, connection, table'''
        logging.basicConfig(format=constants.LOG_FORMAT, level=loglevel)
        if not os.path.isdir(constants.CLIENT_RECORD_DIR):
            os.mkdir(constants.CLIENT_RECORD_DIR)
        try:
            self.conn = sqlite3.connect(constants.CLIENT_RECORD_DIR + record_source)
            self.cursor = self.conn.cursor()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL UNIQUE, sequencenum INTEGER NOT NULL, timestamp DEFAULT CURRENT_TIMESTAMP);")
        except sqlite3.Error, e:
            logging.warning('Record : Unable to connect to local record: {}'.format(constants.CLIENT_RECORD_DIR + record_source))
            logging.debug(e.message)
            sys.exit(2)
        logging.debug('Record : Client connected to local record: {}'.format(constants.CLIENT_RECORD_DIR + record_source))


    def get_sequencenum(self,filename):
        '''Retrieve the sequence number of the given file, return -1 on failure'''
        logging.debug('Record({}) : Getting seqnum'.format(filename))
        try:
            sequence_num = self.cursor.execute("SELECT sequencenum FROM records WHERE filename='{}';".format(filename)).fetchone()
        except sqlite3.Error, e:
            logging.warning('Record : Something went wrong')
            logging.debug(e.message)
            return -1
    
        if sequence_num: 
            return sequence_num[0]
        else:
            return 0
            #logging.debug('Record : {} not in records, creating'.format(filename))
            #return self.create_record(filename)

    def update_sequencenum_or_create(self, filename, new_sequencenum=None):
        '''Update the sequence number of the given record, return updated seqnum on success, -1 on fail'''
        try:
            sequencenum = self.cursor.execute("SELECT sequencenum FROM records WHERE filename='{}';".format(filename)).fetchone()
        except sqlite3.Error, e:
            logging.warning('Record : Something went wrong')
            logging.debug(e.message)
            return -1
        if sequencenum:
            try:
                sequencenum = new_sequencenum if new_sequencenum else sequencenum[0]+1 #either update to new sequence number or increment
                logging.debug('Record({}) : Updating seqnum to {}'.format(filename,sequencenum))
                self.cursor.execute("UPDATE records SET sequencenum={}, timestamp='{}' WHERE filename='{}';".format(sequencenum,datetime.utcnow().isoformat(' '),filename))
                self.conn.commit()
                return sequencenum
            except sqlite3.Error, e:
                logging.warning('Record : Failed to update sequencenum')
                logging.debug(e.message)
                return -1
        else:
            if not new_sequencenum: new_sequencenum = 1 #PE creating record on push..sequencenum should be 1
            return self.create_record(filename,new_sequencenum)

    def create_record(self, filename, sequencenum=0):
        '''Create a new record, return 0 on success, -1 on failure'''
        logging.debug('Record({}) : Creating record with seqnum {}'.format(filename,sequencenum))
        try:
            self.cursor.execute("INSERT INTO records(filename,sequencenum) VALUES('{}',{});".format(filename,sequencenum))
            self.conn.commit()
            return sequencenum
        except sqlite3.Error, e:
            logging.warning('Record : Failed to create record')
            logging.debug(e.message)
            return -1

    def fetch_current_records(self):
        '''Fetches all current records'''
        try:
            return self.cursor.execute("SELECT filename,sequencenum,timestamp FROM records").fetchall()
        except sqlite3.Error, e:
            logging.warning('Record : Failed to fetch records')
            logging.debug(e.message)
            return []

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "USAGE: python db_utils.py <record>"
        sys.exit(1)
    record_source = sys.argv[1]
    test_client_record = ClientRecord(record_source,10)
    input = ""
    while input != "EXIT":
        input = raw_input("Enter 'C/DD/D/G/U/UR/EXIT' to create/delete dir/delete/get seqnum/update seqnum/update record/quit: ")
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
                test_client_record.update_sequencenum_or_create(filename)
            else:
                test_client_record.update_sequencenum_or_create(filename,int(sequencenum))
        if input == 'UR':
            filename = raw_input("Enter filename to update: ")
            flags = {'REQUEST':constants.REQUEST,'ADD_FILE':constants.ADD_FILE,'DELETE_FILE':constants.DELETE_FILE,'ADD_FOLDER':constants.ADD_FOLDER,'DELETE_FOLDER':constants.DELETE_FOLDER}
            flag = raw_input("Enter flag: ")
            try:
                test_client_record.update_record(filename,flags[flag])
            except:
                print "invalid flag"
        if input == 'EXIT':
            print "QUITTING"
            sys.exit(0)

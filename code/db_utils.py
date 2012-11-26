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
        try:
            self.conn = sqlite3.connect(constants.CLIENT_RECORD_DIR + record_source)
            self.cursor = self.conn.cursor()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL UNIQUE, sequencenum INTEGER NOT NULL, timestamp DEFAULT CURRENT_TIMESTAMP);")
            #PE filename: on conflict replace? or handle in code?
        except sqlite3.Error, e:
            logging.warning('Record : Unable to connect to local record: {}'.format(constants.CLIENT_RECORD_DIR + record_source))
            logging.debug(e.message)
            sys.exit(2)
        logging.debug('Record : Client connected to local record: {}'.format(constants.CLIENT_RECORD_DIR + record_source))

    def get_sequencenum(self,filename):
        '''Retrieve the sequence number of the given file, return -1 on failure'''
        logging.debug('Record : Getting seqnum for: {}'.format(filename))
        try:
            sequence_num = self.cursor.execute("SELECT sequencenum FROM records WHERE filename='{}';".format(filename)).fetchone()
        except sqlite3.Error, e:
            logging.warning('Record : Failed to retrieve sequencenum for: {}'.format(filename))
            logging.debug(e.message)
            return -1
    
        if sequence_num: 
            return sequence_num[0]
        else:
            logging.debug('Record : {} not in records, creating'.format(filename))
            return self.create_record(filename)

    def update_sequencenum_or_create(self, filename, new_sequencenum=None):
        '''Update the sequence number of the given record, return 0 on success, -1 on fail'''
        logging.debug('Record : Updating sequencenum for {}, using seqnum {}'.format(filename,new_sequencenum))
        try:
            sequencenum = self.cursor.execute("SELECT sequencenum FROM records WHERE filename='{}';".format(filename)).fetchone()
        except sqlite3.Error, e:
            logging.warning('Record : Something went wrong')
            logging.debug(e.message)
            return -1
        if sequencenum:
            try:
                logging.debug('Record : Record exists, updating seqnum')
                sequencenum = new_sequencenum if new_sequencenum else sequencenum[0]+1 #either update to new sequence number or increment
                self.cursor.execute("UPDATE records SET sequencenum={}, timestamp='{}' WHERE filename='{}';".format(sequencenum,datetime.utcnow().isoformat(' '),filename))
                self.conn.commit()
                return 0
            except sqlite3.Error, e:
                logging.warning('Record : Failed to update sequencenum')
                logging.debug(e.message)
                return -1
        else:
            logging.debug('Record : {} not in records, creating with seqnum: {}'.format(filename,sequencenum))
            return self.create_record(filename,new_sequencenum)

    def create_record(self, filename, sequencenum=None):
        '''Create a new record, return 0 on success, -1 on failure'''
        logging.debug('Record : Creating record for {}'.format(filename))
        if not sequencenum:
            sequencenum = 0
        try:
            self.cursor.execute("INSERT INTO records(filename,sequencenum) VALUES('{}',{});".format(filename,sequencenum))
            self.conn.commit()
            return 0
        except sqlite3.Error, e:
            logging.warning('Record : Failed to create record: {}'.format(filename))
            logging.debug(e.message)
            return -1

    def delete_directory_records(self,filename):
        '''Deletes an entire directory's records, return 0 on success, -1 on failure'''
        logging.debug('Record : Deleting directory: {}'.format(filename))
        directory_to_delete = filename.split('/')[0] + '/%'
        try:
            self.cursor.execute("DELETE FROM records WHERE filename='{}' or filename LIKE '{}';".format(filename,directory_to_delete))
            self.conn.commit()
            return 0
        except sqlite3.Error, e:
            logging.warning('Record : Failed to delete directory record: {}'.format(filename))
            logging.debug(e.message)
            return -1

    def delete_record(self,filename):
        '''Deletes a record, return 0 on success, -1 on failure'''
        logging.debug('Record : Deleting record: {}'.format(filename))
        try:
            self.cursor.execute("DELETE FROM records WHERE filename='{}';".format(filename))
            self.conn.commit()
            return 0
        except sqlite3.Error, e:
            logging.warning('Record : Failed to delete record: {}'.format(filename))
            logging.debug(e.message)
            return -1

    def update_record(self, filename, flag):
        '''Handles updating a record based on flag'''
        if flag == constants.ADD_FILE or flag == constants.ADD_FOLDER:
            retval = self.update_sequencenum_or_create(filename)
        elif flag == constants.DELETE_FILE:
            retval = self.delete_record(filename)
        elif flag == constants.DELETE_FOLDER:
            retval = self.delete_directory_records(filename)
        return retval

    def fetch_current_records(self):
        '''Fetches all current records'''
        try:
            return self.cursor.execute("SELECT filename,sequencenum,timestamp FROM records").fetchall()
        except sqlite3.Error, e:
            logging.warning('Failed to fetch records')
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


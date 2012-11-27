'''
Created on Nov 17, 2012

@author: David Stevens

Modified by: Paul Elliott (PE) Nov 26, 2012
    Added get_datetime helper, LocalFilesEventHandler.initial_update_and_push
    Modified to use record keeping (see db_utils.py)
    Modified to run initial check for offline changes and push those changes
'''

import asynchat, asyncore, errno, logging, os, re, shutil, socket
from datetime import datetime

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import constants
from db_utils import ClientRecord

def get_datetime(timestamp):
    '''Converts a UTC timestamp to a datetime object and returns'''
    (year,month,day),(hour,minute,second) = timestamp.split(' ')[0].split('-'),timestamp.split(' ')[1].split(':') #PE string splits FTW
    if second.find('.') > -1:
        second,microsecond = second.split('.')
    else:
        microsecond = 0
    return datetime(int(year),int(month),int(day),int(hour),int(minute),int(second),int(microsecond))

class LocalFilesEventHandler(FileSystemEventHandler):
    '''Handles events in the file system and passes it to the channel'''

    def __init__(self, dirname, record_source, loglevel):
        FileSystemEventHandler.__init__(self)
        self.dirname = dirname
        self.changes = {}
        self.just_changed = {}
        self.valid = re.compile(r'^(.+/)*[^\./][^/~]*$')
        self.record_source = record_source
        self.loglevel = loglevel

    def initial_update_and_push(self):
        '''Checks for any updates since last snapshot of records, pushes all updates'''
        ADD=0
        DELETE=1 #PE local flags

        record = ClientRecord(record_source,loglevel)
        current_records = dict([ (filename,(sequencenum,get_datetime(timestamp))) for filename,sequencenum,timestamp in record.fetch_current_records() ])
        logging.info('Checking initial records')
        logging.debug('Current records: {}'.format(current_records))
        
        initial_changes = []
        directory_walker = os.walk(self.dirname)
        cur_directory,cur_subdirectories,cur_files = directory_walker.next()
        while(True): #PE walk entire directory, add necessary changes to initial_changes
            cur_directory = cur_directory if cur_directory.endswith('/') else cur_directory + '/'
            logging.debug('Checking {}'.format(cur_directory))
            for filename in cur_subdirectories + cur_files:
                filename = os.path.relpath(cur_directory + filename, self.dirname)
                modified_time = datetime.utcfromtimestamp(os.path.getmtime(self.dirname+filename))
                logging.debug('  Evaluating {} modified on {}'.format(filename, modified_time.isoformat(' ')))
                if filename in current_records:
                    discard,record_timestamp = current_records.pop(filename)
                    if modified_time > record_timestamp: #PE file/folder updated
                        initial_changes.append((filename, ADD))
                else: #PE file/folder added
                    initial_changes.append((filename, ADD))
            try:
                cur_directory,cur_subdirectories,cur_files = directory_walker.next()
            except StopIteration:
                break
        for filename in current_records: #PE file/folder deleted
            initial_changes.append((filename, DELETE))

        logging.info('Updating records and pushing initial changes')
        logging.debug('Changes to push: {}'.format(initial_changes))
        for filename,flag in initial_changes:
            #print self.dirname+filename," is file? ",os.path.isfile(self.dirname+filename)
            if record.update_sequencenum_or_create(filename) == -1:
                logging.warning('Something went wrong.')
            if flag == ADD:
                change = constants.ADD_FILE if os.path.isfile(self.dirname+filename) else constants.ADD_FOLDER 
            else:
                change = constants.DELETE_FILE if os.path.isfile(self.dirname+filename) else constants.DELETE_FOLDER 
            self.handle_change(self.dirname+filename, change)

    def handle_change(self, filename, change):
        record = ClientRecord(record_source,loglevel)
        filename = os.path.relpath(filename, self.dirname)
        if self.valid.match(filename):
            logging.info('Change happened to {}'.format(filename))
            logging.debug('Data : {}'
                          ''.format(constants.FLAG_TO_NAME[change]))
            #PE Q could we leverage local records here to prevent duplicate updates?
            if not self.just_changed.get(filename):
                if filename not in self.changes:
                    sequencenum = record.get_sequencenum(filename)
                    logging.debug('{} sequencenum: {}'.format(filename,sequencenum))
                    if sequencenum == -1:
                      logging.warning('Aborting change')
                      return
                    self.channel.push(filename + constants.DELIMITER +
                                      str(constants.REQUEST) +
                                      constants.TERMINATOR)
                    #PE TODO must push sequencenum to broker (modify this and push)
                    logging.debug('Pushing: {} {}'.format(filename,
                                                          constants.REQUEST))
                self.changes[filename] = change
            elif self.just_changed[filename] != 'Adding':
                logging.info('Unmark {} as being '
                             'just changed'.format(filename))
                self.just_changed[filename] = False
            else:
                logging.debug('Ignoring change to {} '
                              'while it is being written'.format(filename))
        else:
            logging.info('Ignoring change to {}'.format(filename))
            logging.debug('Data : {}'
                          ''.format(constants.FLAG_TO_NAME[change]))

    def on_created(self, event):
        self.handle_change(event.src_path, (constants.ADD_FILE |
                                            event.is_directory))

    def on_deleted(self, event):
        self.handle_change(event.src_path, (constants.DELETE_FILE |
                                            event.is_directory))

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_change(event.src_path, (constants.ADD_FILE))

    def on_moved(self, event):
        #Or (|) logic handles whether file or folder
        self.handle_change(event.src_path, (constants.DELETE_FILE |
                                            event.is_directory))
        self.handle_change(event.dest_path, (constants.ADD_FILE |
                                             event.is_directory))

    def take_change(self, filename):
        '''Dequeues a change from the change queue'''
        if filename in self.changes:
            change = self.changes[filename]
            del self.changes[filename]
            return (change,)
        else:
            logging.warning('{} was never set to change'.format(filename))
            if os.path.exists(self.dirname + filename):
                if os.path.isdir(self.dirname + filename):
                    logging.warning('Spoofing ADD_FOLDER')
                    return (constants.ADD_FOLDER,)
                else:
                    logging.warning('Spoofing ADD_FILE')
                    return (constants.ADD_FILE,)
            else:
                logging.warning(repr(filename) + ' does not exist')
                logging.warning('Spoofing DELETE_FILE')
                logging.warning('Spoofing DELETE_FOLDER')
                return (constants.DELETE_FILE, constants.DELETE_FOLDER)
            


class BrokerChannel(asynchat.async_chat):
    '''The channel that deals with sending and receiving to the broker.'''

    def __init__(self, dirname, record_source, host, port, loglevel):
        asynchat.async_chat.__init__(self)
        self.dirname = dirname
        self.process_data = self.process_message #input stream handler
        self.received_data = [] #buffer
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.set_terminator(constants.TERMINATOR)
        self.record = ClientRecord(record_source,loglevel) #PE connect to record and pass to event_handler and channel

    def push(self, data):
        logging.info('Pushed Data')
        logging.debug('Data : {}'.format(repr(data)))
        asynchat.async_chat.push(self, data)

    def push_with_producer(self, producer):
        logging.info('Pushed Producer')
        asynchat.async_chat.push_with_producer(self, producer)

    def collect_incoming_data(self, data):
        logging.info('Received Data')
        self.received_data.append(data)

    def found_terminator(self):
        logging.info('Processing Data')
        self.process_data()

    def process_message(self):
        token = self.get_token()
        msg = token.split(constants.DELIMITER)
        logging.debug('Data : {}'.format(repr(token)))
        msg[1] = int(msg[1])
        filename, flag = msg[:2]
        logging.info('Received Message with '
                     'flag {}'.format(constants.FLAG_TO_NAME[flag]))
        logging.debug('Data : {}'.format(repr(msg)))
        if flag == constants.REQUEST: #broker responded with an ACK to push request
            self.handle_push_change(filename)
        else:
            self.handle_receive_change(msg) #broker sending change

    def process_file(self):
        token = self.get_token()
        logging.info('Receiving File Data {} '
                     'with size {}'.format(self.file.name,
                                           len(token)))
        logging.debug('Received chunk of size {}'.format(len(token)))
        self.file.write(token)
        self.remaining_size -= len(token)
        if self.remaining_size > 0:
            self.set_terminator(min(self.remaining_size, constants.CHUNK_SIZE))
        else:
            logging.info('Closing {}'.format(self.file.name))
            logging.info('Mark {} as being done being '
                         'changed'.format(self.file.name))
            self.event_handler.just_changed[self.file.name] = 'Done'
            self.file.close()
            self.set_terminator(constants.TERMINATOR)
            self.process_data = self.process_message

    def get_token(self):
        token = ''.join(self.received_data)
        self.received_data = []
        return token

    def handle_close(self):
        logging.warning('Disconnected')
        self.close()

    def handle_connect(self):
        logging.info('Connected')

    def handle_push_change(self, filename):
        '''dequeues a change and pushes it to the broker'''
        #flags = self.event_handler.take_change(filename)
        flags = self.event_handler.take_change(filename) #pull next change from file handler
        for flag in flags:
            retval = self.record.update_record(filename,flag) #PE increment the sequence number for this file
            if retval == -1:
              logging.warning('Something went wrong, could not update record: {}'.format(filename))
            self.push(filename + constants.DELIMITER + str(flag))
            if flag == constants.ADD_FILE: #push size as well for files
                self.push(constants.DELIMITER +
                          str(os.stat(self.dirname + filename).st_size) +
                          constants.TERMINATOR)
                self.push_with_producer(FileProducer(self.dirname + filename))
            else:
                self.push(constants.TERMINATOR)

    def handle_receive_change(self, msg):
        flag = msg[1]
        if flag & constants.ADD_FILE:
            self.handle_receive_add(msg)
        elif flag & constants.DELETE_FILE:
            self.handle_receive_delete(msg)

    def handle_receive_add(self, msg):
        filename, flag = msg[:2]
        logging.info('Getting Add {}'.format(filename))
        try:
            if flag & constants.FOLDER:
                logging.info('Mark {} as being just '
                             'changed'.format(filename))
                self.event_handler.just_changed[filename] = 'Done'
                os.mkdir(self.dirname + filename)

            else:
                logging.info('Opening {}'.format(filename))
                self.file = open(self.dirname + filename, 'w')
                logging.info('Mark {} as being just '
                             'changed'.format(filename))
                self.event_handler.just_changed[filename] = 'Adding'
                self.remaining_size = int(msg[2])
                if self.remaining_size == 0: #PE handle empty files, which will otherwise hang badly
                  logging.debug('Empty file, closing {} and marking done being changed'.format(filename))
                  self.event_handler.just_changed[filename] = 'Done'
                  self.file.close()
                else:
                  self.process_data = self.process_file
                  self.set_terminator(min(self.remaining_size,
                                          constants.CHUNK_SIZE))
            retval = self.record.update_sequencenum_or_create(filename) #PE modify: updates seqnum for record, add: creates new record for the added file/folder
            logging.debug('updated record, returned {}'.format(retval))
            if retval == -1:
              logging.warning('Error updating records')
            #PE TODO retrieve sequencenum and use to update
        except OSError as e:
            if e.errno == errno.EEXIST:
                logging.warning(str(e))
                logging.debug('Exception : {}'.format(repr(e)))
            else:
                logging.error(str(e))
                logging.debug('Exception : {}'.format(repr(e)))
                raise
        except Exception as e:
            logging.error(str(e))
            logging.debug('Exception : {}'.format(repr(e)))
            raise

    def handle_receive_delete(self, msg):
        filename, flag = msg[:2]
        logging.info('Getting Delete ' + repr(filename))
        try:
            if flag & constants.FOLDER:
                logging.info('Mark {} as being just '
                             'changed'.format(filename))
                self.event_handler.just_changed[filename] = 'Done'
                shutil.rmtree(self.dirname + filename)
                retval = self.record.delete_directory_records(filename) #PE delete directory from records
                if retval == -1:
                  logging.warning('Error updating records')
            else:
                logging.info('Mark {} as being just '
                             'changed'.format(filename))
                self.event_handler.just_changed[filename] = 'Done'
                os.remove(self.dirname + filename)
                retval = self.record.delete_record(filename) #PE delete file from records
                if retval == -1:
                  logging.warning('Error updating records')
        except OSError as e:
            if e.errno == errno.ENOENT:
                logging.warning(str(e))
                logging.debug('Exception : {}'.format(repr(e)))
            else:
                logging.error(str(e))
                logging.debug('Exception : {}'.format(repr(e)))
                raise
        except Exception as e:
            logging.error(str(e))
            logging.debug('Exception : {}'.format(repr(e)))
            raise


class FileProducer:
    '''This produces a file in chunks.'''

    def __init__(self, name):
        logging.info('Opening Producer\'s File')
        self.file = open(name)

    def more(self):
        if self.file:
            try:
                data = self.file.read(constants.CHUNK_SIZE)
                if data:
                    logging.info('Produced with size ' + str(len(data)))
                    logging.debug('Producer : ' + repr(self))
                    logging.debug('Data : ' + repr(data))
                    return data
                logging.info('Closing Producer\'s File')
                self.file.close()
                self.file = None
            except IOError as e:
                logging.warning(str(e))
                logging.debug('Exception : ' + repr(e))
                self.file.close()
            except Exception as e:
                logging.error(str(e))
                logging.debug('Exception : ' + repr(e))
                self.file.close()
                raise
        logging.info('Produced with size 0')
        logging.debug('Producer : ' + repr(self))
        logging.debug('Data : ' + repr(''))
        return ''


if __name__ == '__main__':
    import getopt
    import sys
    dirname = './'
    host = constants.HOST
    port = constants.PORT
    loglevel = logging.INFO
    record_source = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:h:p:l:v:r:',
                                   ['dir=', 'host=', 'port=', 'logging=',
                                    'verbose=','record=']) #PE added a -r/--record arg
    except getopt.GetoptError:
        logging.warning('The system arguments are incorrect')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-d', '--dir'):
            dirname = arg
            if not os.path.exists(dirname):
                logging.info('Makinge directory \'{}\''.format(dirname))
                os.mkdir(dirname)
        elif opt in ('-h', '--host'):
            host = arg
        elif opt in ('-p', '--port'):
            port = int(arg)
        elif opt in ('-v', '-l', '--logging'):
            loglevel = 10 * (6 - int(arg))
        elif opt in ('-r', '--record'): #PE handle record arg
            record_source = arg

    if not dirname.endswith('/'):
        dirname += '/'
    if not record_source: #PE create random record source if none provided
      import random
      record_source='defaultclient{}'.format(random.randint(1,1000))
    logging.basicConfig(format=constants.LOG_FORMAT, level=loglevel)
    observer = Observer()
    event_handler = LocalFilesEventHandler(dirname, record_source, loglevel)
    channel = BrokerChannel(dirname, record_source, host, port, loglevel) #PE pass record_source to both..can't pass sqlite conn between threads
    event_handler.channel = channel
    channel.event_handler = event_handler
    event_handler.initial_update_and_push() #PE check for offline changes and push all
    observer.schedule(event_handler, dirname, True)
    observer.start()
    asyncore.loop() 

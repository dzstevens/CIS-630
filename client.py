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

def valid_filename(filename):
    '''Returns True on valid filename, False otherwise'''
    if filename[-1] == '~': return False
    folders_and_file = filename.split('/')
    for name in folders_and_file:
        try:
            if name[0] == '.': return False
        except IndexError:
            pass
    return True

def get_datetime(timestamp):
    '''Converts a UTC timestamp to a datetime object and returns'''
    (year,month,day),(hour,minute,second) = timestamp.split(' ')[0].split('-'),timestamp.split(' ')[1].split(':') 
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
        if not os.path.isdir(self.dirname + constants.TMP_FOLDER): 
            os.mkdir(self.dirname + constants.TMP_FOLDER)
        self.changes = {}
        self.just_changed = {}
        self.valid = re.compile(r'^(\./)?([^/]+/)*(?!\.)[^/]*[^~]$') #PE test this, should work
        #self.valid = re.compile(r'^(.+/)*[^\./][^/~]*$')
        self.record_source = record_source
        self.loglevel = loglevel

    def initial_update_and_push(self):
        '''
        Checks for any updates since last snapshot of records,
        pushes all updates
        '''
        ADD = 0
        DELETE = 1
        UPDATE = 2
        CREATE = 3
        IGNORE = 4
        record = ClientRecord(record_source,loglevel)
        logging.debug('CONNECTED')
        current_records = dict([(filename,(sequencenum,
                                           get_datetime(timestamp)))
                                for filename, sequencenum, timestamp in
                                record.fetch_current_records()])
        logging.debug('Checking initial records')
        logging.debug('Current records: {}'.format(current_records))
        
        initial_pushes = []
        
        directory_walker = os.walk(self.dirname)
        cur_directory, cur_subdirectories,cur_files = directory_walker.next()
        # PE walk entire directory, add necessary changes to initial_pushes
        while(True):
            cur_directory = (cur_directory if cur_directory.endswith('/') else
                             cur_directory + '/')
            for filename in cur_subdirectories + cur_files:
                filename = os.path.relpath(cur_directory + filename,
                                           self.dirname)
                if not valid_filename(filename):
                    logging.debug('Ignoring {}'.format(filename))
                    continue
                modified_time = datetime.utcfromtimestamp(
                    os.path.getmtime(self.dirname+filename))
                logging.debug('Evaluating {} modified on {}'.format(
                    filename,
                    modified_time.isoformat(' ')))
                if filename in current_records:
                    discard, record_timestamp = current_records.pop(filename)
                    # PE file/folder updated
                    if modified_time > record_timestamp:
                        initial_pushes.append((filename, ADD, UPDATE))
                    # PE file/folder unchanged..still push
                    else:
                        initial_pushes.append((filename, ADD, IGNORE))
                # PE file/folder added
                else:
                    initial_pushes.append((filename, ADD, CREATE))
            try:
                cur_directory, cur_subdirectories, cur_files = directory_walker.next()
            except StopIteration:
                break
        for filename in current_records: #PE file/folder deleted
            initial_pushes.append((str(filename), DELETE, UPDATE))

        logging.debug('Changes to push: {}'.format(initial_pushes))
        self.channel.push(constants.DELIMITER.join(
            [constants.BATCH_FILENAME,
             str(constants.BATCH),
             str(len(initial_pushes))]) + constants.TERMINATOR)
        for filename, change, update_flag in initial_pushes:
            if update_flag == CREATE:
                if record.create_record(filename) == -1:
                    logging.warning('Something went wrong.')
            if change == ADD:
                change = (constants.ADD_FILE if
                          os.path.isfile(self.dirname+filename) else
                          constants.ADD_FOLDER)
            else:
                change = constants.DELETE
            if update_flag == IGNORE:
                self.handle_change(''.join([self.dirname,filename]), change, True)
            else:
                self.handle_change(''.join([self.dirname,filename]), change)

    def handle_change(self, filename, change, no_change=False):
        '''Handler for any changes to the workspace directory'''
        record = ClientRecord(record_source,loglevel)
        filename = os.path.relpath(filename, self.dirname)
        if valid_filename(filename):
            logging.debug('Change happened to {}'.format(filename))
            logging.debug('Data : {}'
                          ''.format(constants.FLAG_TO_NAME[change]))
            if not self.just_changed.get(filename):
                if filename not in self.changes:
                    sequencenum = record.get_sequencenum(filename)
                    if sequencenum == -1:
                        logging.error('Aborting change')
                        return
                    elif no_change:
                        sequencenum -= 1
                    logging.debug('Pushing REQUEST for {}, seqnum {}'.format(filename,sequencenum))
                    msg = constants.DELIMITER.join(
                        [filename,
                         str(constants.REQUEST),
                         str(sequencenum)]) + constants.TERMINATOR
                    logging.debug('Pushing: {}'.format(repr(msg)))
                    self.channel.push(msg)
                    self.changes[filename] = (change,sequencenum)
            else:
                logging.debug('Unmark {} as being '
                             'just changed'.format(filename))
                del self.just_changed[filename]
        else:
            logging.debug('Ignoring change to {}'.format(filename))
            logging.debug('Data : {}'
                          ''.format(constants.FLAG_TO_NAME[change]))

    '''Workspace directory events'''
    def on_created(self, event):
        self.handle_change(event.src_path, (constants.ADD_FILE |
                                            event.is_directory))
    def on_deleted(self, event):
        self.handle_change(event.src_path, (constants.DELETE))
    def on_modified(self, event):
        logging.debug("File '{}' modified'".format(event.src_path))
        if not event.is_directory:
            self.handle_change(event.src_path, (constants.ADD_FILE))
    def on_moved(self, event):
        logging.debug("File '{}' renamed to '{}'".format(event.src_path, event.dest_path))
        self.handle_change(event.src_path, (constants.DELETE))
        # Or (|) logic handles whether file or folder
        self.handle_change(event.dest_path, (constants.ADD_FILE |
                                             event.is_directory))

    def take_change(self, filename):
        '''Dequeues a change from the change queue'''
        if filename in self.changes:
            change = self.changes[filename][0]
            del self.changes[filename]
            return change #PE updated change queue to include sequencenum
        else: 
            logging.warning('{} was never set to change'.format(filename))
            if os.path.exists(self.dirname + filename):
                if os.path.isdir(self.dirname + filename):
                    logging.warning('Spoofing ADD_FOLDER')
                    return constants.ADD_FOLDER
                else:
                    logging.warning('Spoofing ADD_FILE')
                    return constants.ADD_FILE
            else:
                logging.warning(repr(filename) + ' does not exist')
                logging.warning('Spoofing DELETE')
                return constants.DELETE

    def remove_change(self,filename,sequencenum):
        '''If filename change is in the queue, compare sequencenums and remove older changes'''
        if filename in self.changes and sequencenum > self.changes[filename][1]:
            del self.changes[filename]

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
        self.record = ClientRecord(record_source,loglevel) 

    def push(self, data):
        '''Send messages'''
        logging.debug('Pushed Data')
        logging.debug('Data : {}'.format(repr(data)))
        asynchat.async_chat.push(self, data)

    def push_with_producer(self, producer):
        '''Send data'''
        logging.debug('Pushed Producer')
        asynchat.async_chat.push_with_producer(self, producer)

    def collect_incoming_data(self, data):
        self.received_data.append(data)

    def found_terminator(self):
        logging.debug('Processing Data')
        self.process_data()

    def process_message(self):
        '''Process a message received from the broker, and handle'''
        token = self.get_token()
        msg = token.split(constants.DELIMITER)
        logging.debug('Data : {}'.format(repr(token)))
        msg[1] = int(msg[1])
        filename, flag = msg[:2]
        logging.debug('Received Message with '
                     'flag {}'.format(constants.FLAG_TO_NAME[flag]))
        logging.debug('Data : {}'.format(repr(msg)))
        if flag == constants.REQUEST: 
            if len(msg) == 4: #PE broker pulled change
                client_num = msg[3]
                self.handle_broker_pull(filename,client_num)
            else: #PE broker responded with ACK, push change
                self.handle_push_change(filename)
        else:
            self.handle_receive_change(msg) #PE broker pushed change

    def process_file(self):
        '''Process incoming file data, and write to workspace directory'''
        token = self.get_token()
        logging.debug('Receiving File Data {} '
                      'with size {}'.format(self.file.name,
                                            len(token)))
        logging.debug('Received chunk of size {}'.format(len(token)))
        self.file.write(token)
        self.remaining_size -= len(token)
        if self.remaining_size > 0:
            self.set_terminator(min(self.remaining_size, constants.CHUNK_SIZE))
        else:
            logging.debug('Closing {}'.format(self.file.name))
            logging.debug('Mark {} as being done being '
                         'changed'.format(self.filename))
            self.event_handler.just_changed[self.filename] = True
            self.file.close()
            shutil.move(self.file.name,self.dirname + self.filename)
            logging.info('Received file \'{}\''.format(self.filename)) 
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
        self.event_handler.initial_update_and_push() #PE check for offline changes and push all

    def get_flag(self, filename):
        '''Returns proper flag depending on existence of given file/folder'''
        if os.path.exists(self.dirname + filename):
            if os.path.isdir(self.dirname + filename):
                return constants.ADD_FOLDER
            else:
                return constants.ADD_FILE
        else:
            return constants.DELETE

    def handle_broker_pull(self, filename, client_num):
        '''Respond to broker pull with requested change'''
        sequencenum = self.record.get_sequencenum(filename)
        if sequencenum == -1: 
            logging.error('Something went wrong, could not update record: {}'.format(filename))
            return
        flag = self.get_flag(filename)
        logging.info('Sending change: {} \'{}\''.format(constants.FLAG_TO_NAME[flag], filename))
        self.push(filename + constants.DELIMITER + str(flag) + constants.DELIMITER + str(sequencenum))
        if flag == constants.ADD_FILE: 
            self.push(constants.DELIMITER +
                      str(os.stat(self.dirname + filename).st_size) + 
                      constants.DELIMITER +
                      str(client_num) +
                      constants.TERMINATOR)
            self.push_with_producer(FileProducer(self.dirname + filename))
        else:
            self.push(constants.DELIMITER + str(client_num) + constants.TERMINATOR)

    def handle_push_change(self, filename):
        '''dequeues a change and pushes it to the broker'''
        logging.debug("Pushing change for {}".format(filename))
        flag = self.event_handler.take_change(filename) #pull next change from file handler
        sequencenum = self.record.update_sequencenum_or_create(filename)
        if sequencenum == -1: 
            logging.error('Something went wrong, could not update record: {}'.format(filename))
            return
        logging.info('Sending change: {} \'{}\''.format(constants.FLAG_TO_NAME[flag], filename))
        self.push(filename + constants.DELIMITER + str(flag) + constants.DELIMITER + str(sequencenum))
        if flag == constants.ADD_FILE: 
            self.push(constants.DELIMITER +
                      str(os.stat(self.dirname + filename).st_size) +
                      constants.TERMINATOR)
            self.push_with_producer(FileProducer(self.dirname + filename))
        else:
            self.push(constants.TERMINATOR)

    def handle_receive_change(self, msg):
        '''Handle a change pushed from the broker'''
        filename, flag, sequencenum = msg[:3]
        self.event_handler.remove_change(filename,sequencenum) 
        if self.record.update_sequencenum_or_create(filename,sequencenum) == -1:
            logging.warning('Error updating records')
        if flag & constants.ADD_FILE:
            self.handle_receive_add(msg)
        elif flag == constants.DELETE:
            self.handle_receive_delete(msg[0])

    def handle_receive_add(self, msg):
        '''Write incoming add to workspace directory'''
        filename, flag, sequencenum = msg[:3]
        logging.debug('Getting Add {}'.format(filename))
        try:
            if flag & constants.FOLDER:
                logging.debug('Mark {} as being just '
                             'changed'.format(filename))
                self.event_handler.just_changed[filename] = True
                os.makedirs(self.dirname + filename) 
                logging.info('Added directory {}'.format(filename)) 
            else:
                logging.debug('Opening {}'.format(filename))
                dir, file = os.path.split(filename)
                if dir != '': os.makedirs(dir) 
                self.filename = filename
                self.file = open(self.dirname + constants.TMP_FOLDER + file, 'w')
                logging.debug('Mark {} as being just '
                             'changed'.format(filename))
                self.remaining_size = int(msg[3])
                if self.remaining_size == 0: #PE handle empty files
                    logging.debug('Empty file, closing {} and marking done being changed'.format(filename))
                    self.event_handler.just_changed[self.filename] = True
                    self.file.close()
                    shutil.move(self.file.name,self.dirname + self.filename)
                    logging.info('Received file \'{}\''.format(self.filename)) 
                else:
                    self.process_data = self.process_file
                    self.set_terminator(min(self.remaining_size,
                                            constants.CHUNK_SIZE))
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

    def handle_receive_delete(self, filename):
        '''Delete indicated file from workspace directory'''
        logging.debug('Getting Delete ' + repr(filename))
        try:
            logging.debug('Mark {} as being just '
                         'changed'.format(filename))
            self.event_handler.just_changed[filename] = True
            shutil.rmtree(self.dirname + filename)
            logging.info('Deleted directory {}'.format(filename))    
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                os.remove(self.dirname + filename)
                logging.info('Deleted file {}'.format(filename))    
            elif e.errno == errno.ENOENT:
                logging.warning(str(e))
                logging.debug('Exception : {}'.format(repr(e)))
            else:
                logging.error(str(e))
                logging.debug('Exception : {}'.format(repr(e)))
                raise


class FileProducer:
    '''This produces a file in chunks.'''

    def __init__(self, name):
        logging.debug('Opening Producer\'s File')
        self.file = open(name)

    def more(self):
        if self.file:
            try:
                data = self.file.read(constants.CHUNK_SIZE)
                if data:
                    logging.debug('Produced with size ' + str(len(data)))
                    return data
                logging.debug('Closing Producer\'s File')
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
        logging.debug('Produced with size 0')
        return ''


if __name__ == '__main__':
    import getopt
    import sys
    import random
    dirname = './'
    host = constants.HOST
    port = constants.PORT
    loglevel = logging.INFO
    record_source = None
    logfile = 'sender.log'
    box = 'default'
    TEST_MODE = False  
    log_directory = 'test' + str(random.randint(1,1000))
    '''
    Get command line args:
        d = local workspace directory
        h = broker hostname
        p = broker port
        v = verbosity level
        r = record source
        (for testing)
        l = log directory
        b = box
    '''
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:h:p:l:v:r:b:t',
                                   ['dir=', 'host=', 'port=', 'logging=',
                                    'verbose=','record=','box=', 'test']) 
    except getopt.GetoptError:
        raise
    for opt, arg in opts:
        if opt in ('-d', '--dir'):
            dirname = arg
            if not os.path.exists(dirname):
                logging.info('Making directory \'{}\''.format(dirname))
                os.mkdir(dirname)
        elif opt in ('-h', '--host'):
            host = arg
        elif opt in ('-p', '--port'):
            port = int(arg)
        elif opt in ('-v', '--verbose'):
            loglevel = 10 * (6 - int(arg))
        elif opt in ('-l', '--logging'):
            log_directory = arg
            if log_directory[-1] != '/':
                log_directory = log_directory + '/'
        elif opt in ('-r', '--record'): 
            record_source = arg
        elif opt in ('-b', '--box'):
            box = arg
            logfile = '{}_receiver{}.log'.format(box,dirname.split('_')[1])
        elif opt in ('-t', '--test'):
            TEST_MODE = True
    if not dirname.endswith('/'):
        dirname += '/'
    if not record_source: 
        record_source='defaultclient{}'.format(random.randint(1,1000))
    #PE for testing, log everything to a given logfile
    if TEST_MODE:
        logging.basicConfig(format=constants.LOG_FORMAT, filename=log_directory + logfile, level=loglevel)
    else:
        logging.basicConfig(format=constants.LOG_FORMAT, level=loglevel)
    '''
    Initialize the client:
        1. Init the observer for the local workspace directory
        2. Init the event handler for workspace changes
        3. Init the channel to the broker
        4. Link the observer with the event handler
        5. Start the observer
        6. Begin a continuous select loop on the broker channel
    '''
    observer = Observer()
    event_handler = LocalFilesEventHandler(dirname, record_source, loglevel)
    channel = BrokerChannel(dirname, record_source, host, port, loglevel) 
    event_handler.channel = channel
    channel.event_handler = event_handler
    observer.schedule(event_handler, dirname, True)
    observer.start()
    asyncore.loop()
    

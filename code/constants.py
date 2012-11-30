import os

CHUNK_SIZE = 2**20
DELIMITER  = '\n'
TERMINATOR = '\r\n'
HOST       = ''
PORT       = 55555

# DIRECTORY HANDLER CONSTANTS
REQUEST       = 0
ADD_FILE      = 0b010
DELETE   = 0b100
FOLDER        = 0b001
ADD_FOLDER    = FOLDER | ADD_FILE

BATCH         = 0b111


FLAG_TO_NAME = {REQUEST       : 'REQUEST',
                ADD_FILE      : 'ADD_FILE',
                DELETE        : 'DELETE',
                ADD_FOLDER    : 'ADD_FOLDER',
                BATCH         : 'BATCH',
               }


# Logging
LOG_FORMAT = '%(asctime)s - %(levelname)7s : %(message)s'
RECORD_DEBUGGING = True

# Misc
CLIENT_RECORD_DIR = 'client_records/'
BATCH_FILENAME = 'BATCH'
TMP_FOLDER = '.TMP/'

# Results
WAN='WAN'
LAN='LAN'
RESULTS_DIR = 'RESULTS/'
DATA_DIR = 'test_files/'
try:
  os.mkdir(DATA_DIR)
except OSError:
  pass
PERFORMANCE_FILES = os.listdir(DATA_DIR)
 
CLOCK_DRIFT = {'PAUL':0,'david.stevens':0,'david':0,'default':0}
TEST_MODE = True

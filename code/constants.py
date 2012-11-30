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
PLOT_DIR = 'PLOTS/'
DATA_DIR = 'test_files/'
try:
  os.mkdir(DATA_DIR)
except OSError:
  pass
files = ['data_file_1B', 'data_file_2B', 'data_file_4B',
         'data_file_16B', 'data_file_32B', 'data_file_64B',
         'data_file_128B', 'data_file_256B', 'data_file_512B',
         'data_file_1K', 'data_file_2K', 'data_file_4K',
         'data_file_16K', 'data_file_32K', 'data_file_64K',
         'data_file_128K', 'data_file_256K', 'data_file_512K',
         'data_file_1M', 'data_file_2M', 'data_file_4M',
         'data_file_16M', 'data_file_32M', 'data_file_64M',
         'data_file_128M', 'data_file_256M', 'data_file_512M',
         'data_file_1G']

PERFORMANCE_FILES = [DATA_DIR+f for f in files]

CLOCK_DRIFT = {'PAUL':0,'david.stevens':0,'david':0,'default':0}
TEST_MODE = True

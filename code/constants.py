CHUNK_SIZE = 1024
DELIMITER  = '\n'
TERMINATOR = '\r\n'
HOST       = ''
PORT       = 55555

# DIRECTORY HANDLER CONSTANTS
REQUEST       = 0
ADD_FILE      = 0b010
DELETE_FILE   = 0b100
FOLDER        = 0b001
ADD_FOLDER    = FOLDER | ADD_FILE
DELETE_FOLDER = FOLDER | DELETE_FILE

DIRECTORY_FLAG_TO_NAME = {REQUEST       : 'REQUEST',
                          ADD_FILE      : 'ADD_FILE',
                          DELETE_FILE   : 'DELETE_FILE',
                          ADD_FOLDER    : 'ADD_FOLDER',
                          DELETE_FOLDER : 'DELETE_FOLDER'}

# Logging
LOG_FORMAT = '%(asctime)s - %(levelname)7s : %(message)s'

CHUNK_SIZE = 1024
DELIMITER  = '\n'
TERMINATOR = '\r\n'
HOST       = ''
PORT       = 55555

# DIRECTORY HANDLER CONSTANTS
REQUEST       = 0
ADD_FILE      = 0b0010
DELETE_FILE   = 0b0100
MOVE_FILE     = 0b1000
FOLDER        = 0b0001
ADD_FOLDER    = FOLDER | ADD_FILE
DELETE_FOLDER = FOLDER | DELETE_FILE
MOVE_FOLDER   = FOLDER | MOVE_FILE

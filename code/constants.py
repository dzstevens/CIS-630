CHUNK_SIZE = 1024
DELIMITER  = '\n'
HOST       = ''
PORT       = 55555

# DIRECTORY HANDLER CONSTANTS
REQUEST       = 0
ADD_FILE      = 0b010
DELETE_FILE   = 0b100
MOVE_FILE     = 0b110
FOLDER        = 0b001
ADD_FOLDER    = FOLDER | ADD_FILE
DELETE_FOLDER = FOLDER | DELETE_FILE
MOVE_FOLDER   = FOLDER | MOVE_FILE
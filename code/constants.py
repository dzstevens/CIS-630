CHUNK_SIZE = 1024
DELIMITER  = '\n'
HOST       = ''
PORT       = 55555

# DIRECTORY HANDLER CONSTANTS
REQUEST_FLAG       = 0
ADD_FILE_FLAG      = 0b010
DELETE_FILE_FLAG   = 0b100
MOVE_FILE_FLAG     = 0b110
FOLDER_FLAG        = 0b001
ADD_FOLDER_FLAG    = FOLDER_FLAG | ADD_FILE_FLAG
DELETE_FOLDER_FLAG = FOLDER_FLAG | DELETE_FILE_FLAG
MOVE_FOLDER_FLAG   = FOLDER_FLAG | MOVE_FILE_FLAG

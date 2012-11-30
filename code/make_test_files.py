import os
import constants
CHUNK = '0'*(2**20)

def get_name(dr, size):
  d = {0:'B', 1:'K', 2:'M', 3:'G'}
  return '{}/data_file_{}{}'.format(dr, 2**(size % 10), d[size//10])
if not os.listdir(constants.DATA_DIR):
    for i in range(31):
    #  with open('test_files/test_file_{}'.format())
      name = get_name('test_files', i)
      with open(name, 'w') as f:
        if name[-1] in ['B', 'K']:
          f.write(CHUNK[:2**i])
        else:
          for x in range(2**(i-20)):
            f.write(CHUNK)
      print('Wrote file {}'.format(name))


import os
import constants
CHUNK = '0'*(2**20)

def get_name(dr, size):
  d = {2:'M', 3:'G'}
  return '{}/data_file_{}{}'.format(dr, 2**(size % 10), d[size//10])

try:
  os.mkdir(constants.DATA_DIR)
except OSError:
  pass

for i in range(20, 31):
  name = get_name('test_files', i)
  if os.path.isfile(name):
      continue
  with open(name, 'w') as f:
      for x in range(2**(i-20)):
          f.write(CHUNK)
      print('Wrote file {}'.format(name))


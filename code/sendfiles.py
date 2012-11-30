import os
import shutil
import sys
for file in os.listdir('test_files'):
    print 'sending {}'.format(file)
    shutil.move('test_files/'+file,'sender_dir/')
    x = raw_input('CONTINUE?')

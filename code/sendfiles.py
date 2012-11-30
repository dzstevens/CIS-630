import os
import shutil
import sys
import constants

for f in constants.PERFORMANCE_FILES:
    print 'sending {}'.format(f)
    shutil.move('test_files/'+f,'sender_dir/')
    x = raw_input('CONTINUE?')

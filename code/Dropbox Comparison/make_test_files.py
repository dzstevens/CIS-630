import sys, os, binascii

for i in range(11):
    size = 2**i
    choice = raw_input('Write next file ({} MB) ? '.format(size))
    if choice.lower() == 'q':
        break
    elif choice.lower() == 'n':
        continue
    else:
        with open('test_data_{}MB'.format(size), 'w') as f:
            for x in range(2**i):
                f.write(binascii.b2a_hex(os.urandom(2**20)))
            print('Wrote file \'test_data_{}MB\''.format(size))
    if raw_input('Delete file (y/n)? ').lower() != 'n':
        os.remove('test_data_{}MB'.format(size))

from datetime import datetime, time

with open('send.log') as f:

    s = dict((int(l[1].strip()), datetime.strptime(l[0], '%H:%M:%S')) for l in [line.split() for line in f])

with open('receive.log') as f:
    r = dict((int(l[1].strip()), datetime.strptime(l[0], '%H:%M:%S')) for l in [line.split() for line in f])

with open('drop_data', 'w') as f:
     for k in sorted(s):
         f.write('{}\t{}\n'.format(k, (r[k] - s[k]).total_seconds()))

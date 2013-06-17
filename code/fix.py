import os

for fname in os.listdir('.'):
    if 'data' in fname:
        n = []
        with open(fname) as f:
            for line in f:
                l = line.split()
                if int(l[0]) >= 20:
                    l[0] = str(2**(int(l[0])-20))
                    n.append('\t'.join(l))
        with open(fname, 'w') as f:
            f.write('\n'.join(n))

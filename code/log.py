import time

def log(what, *data):
    if len(data):
        t = time.localtime()
        print('{}:{}:{}: \'{}\':').format(t.tm_hour, t.tm_min, t.tm_sec, what)
        for datum in data:
            print '\t'+repr(datum)
        print
    else:
        print what

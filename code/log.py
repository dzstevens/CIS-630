import time

def log(what, *data):
    if len(data):
        print time.localtime(), what,  "{"
        for datum in data:
            print repr(datum)
        print "}"
    else:
        print what

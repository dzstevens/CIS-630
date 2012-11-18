import socket, os, asyncore, asynchat
CHUNK = 1024
class Test(asynchat.async_chat):
    def __init__(self, host, port):
        asynchat.async_chat.__init__(self)
        self.received_data = []
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.set_terminator('\n')
        
    def handle_connect(self):
        op = raw_input('Add(a) Delete(d) or Quit(q): ').lower()[0]
        if op == 'q':
            self.close()
            return
        op = 'ADD' if op == 'a' else 'DEL'
        name = raw_input('File name: ') 
        size = os.path.getsize(name) if op == 'ADD' else -1
        self.push("{}\t{}\t{}\n".format(name, op, size))
        if op == 'ADD':
            self.push_with_producer(FileProducer(name))

    def collect_incoming_data(self, data):
        self.received_data.append(data)

    def found_terminator(self):
        print(''.join(self.received_data))
        self.received_data = []
        op = raw_input('Add(a) Delete(d) or Quit(q): ').lower()[0]
        if op == 'q':
            self.close()
            return
        op = 'ADD' if op == 'a' else 'DEL'
        name = raw_input('File name: ') 
        size = os.path.getsize(name) if op == 'ADD' else -1
        self.push("{}\t{}\t{}\n".format(name, op, size))
        if op == 'ADD':
            self.push_with_producer(FileProducer(name))
        
    def handle_close(self):
        self.close()
        
class FileProducer:
    # a producer which reads data from a file object
    def __init__(self, name):
        self.file = open(name)

    def more(self):
        if self.file:
            data = self.file.read(CHUNK)
            if data:
                return data
            self.file.close()
            self.file = None
        return ""

def main():
    t = Test('', 55555)
    asyncore.loop()
    
if __name__ == '__main__':
    main()
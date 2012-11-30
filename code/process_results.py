import logging 
import constants 
import os
from Queue import Queue


def measure_performance(RESULTS_SUBDIRECTORY, type='Online', network=constants.LAN):
    data_filename = constants.DATA_DIR + "{}-{}_performance.plot".format(network,type)

    PROCESS_QUEUE = Queue()
    for test_dir in os.listdir(RESULTS_SUBDIRECTORY):
        num_receives = len(os.listdir(RESULTS_SUBDIRECTORY + test_dir) - 1) #-1 for send
        PROCESS_QUEUE.push((num_receives,test_dir))
    PROCESS_LIST = []
    with open(data_filename, 'w') as graphfile:
        graphfile.write("reset\n")
        graphfile.write("set term postscript eps color enhanced \"Helvetica\" 25\n")
        graphfile.write("set ylabel \"Latency (in milliseconds)\"\n")
        graphfile.write("set xlabel \"File size (in kilabytes)\"\n")
        graphfile.write("#set yrange\n")
        graphfile.write("set output \"{}-{}_performance.eps\"\n".format(network,type))
        graphfile.write("set title \"{} Online Performance\"\n".format(type))
        while not PROCESS_QUEUE.empty():
            num_receives,test_dir = PROCESS_QUEUE.get()
            graphfile.write("plot \"-\" using 1:2 title \"{} clients\" with lines lw 3\n".format(num_receives))
            PROCESS_LIST.append(test_dir)
    logging.debug("Test directories to process ({}): {}".format(len(PROCESS_LIST),PROCESS_LIST))
    for test_dir in PROCESS_LIST:
        if type == 'Online':
            append_online_data(test_dir,data_filename)
        else:
            append_offline_data(test_dir,data_filename)
    with open(data_filename, 'a') as graphfile:
        graphfile.write("e\n")

def append_online_data(test_dir,data_filename):
    with open(data_filename, 'a') as graphfile:
        graphfile.write("e\n")
    receive_files = []
    for file in os.listdir(RESULTS_SUBDIRECTORY + test_dir):
        if file.name == 'send.log':
            send_file = RESULTS_SUBDIRECTORY + test_dir + file
        else: # (box)_receive.log
            receive_files.append(RESULTS_SUBDIRECTORY + test_dir + file)

    logging.info("Opened send log and {} receive logs".format(len(receive_files)))
    for per_file in constants.PERFORMANCE_FILES:
        logging.debug("Searching for 'send {}'".format(per_file))
        send_timestamp = search_send(per_file,send_file) #datetime, no update of clock drift
        if send_timestamp == -1:
            logging.warning("Couldn't find {} in send log: skipping".format(per_file))
            continue
        logging.debug("Master sent {} at {}".format(per_file,send_timestamp.isoformat(' ')))
        rcv_timestamps = []
        for receive_file in receive_files:
            rcv_timestamp = search_rcv(per_file,receive_file) #datetime, should update based on clock drift too
            if rcv_timestamp == -1:
                logging.warning("Couldn't find {} in receive log: ignoring for now".format(per_file))
            else:
                rcv_timestamps.append(rcv_timestamp)
        last_rcv_timestamp = max(rcv_timestamps)
        logging.debug("Last receive received {} at {}".format(per_file,last_rcv_timestamp.isoformat(' ')))
        
        #calculate latency
        latency = (last_rcv_timestamp-send_timestamp).total_seconds() #seconds.milli
        logging.info("It took {} seconds to send {}".format(latency,per_file))
        with open(data_filename, 'a') as graphfile:
            graphfile.write("{}\t{}\n".format(per_file.split('_')[1],latency*1000))

def search_send(per_file,send_file):
    with open(send_file,'r') as logfile:
        line = logfile.readline()
        while line != '':
            if (line.find("Sending") > 0 and line.find("'{}'".format(per_file)) > 0):
                raw_timestamp = line.split(' -')[0]
                logging.debug("Pulled {} from line: {}".format(raw_timestamp,line))
                (year,month,day),(hour,min,second),(msecond) = ((raw_timestamp.split(' ')[0].split('-')),
                                                                (raw_timestamp.split(' ')[1].split(',')[0].split(':')),
                                                                (raw_timestamp.split(',')[1]))
                return datetime.datetime(year,month,day,hour,min,second,msecond)
    return -1 #did not find correct line

def search_rcv(per_file,rcv_file):
    box = rcv_file.split('_')[0]
    with open(send_file,'r') as logfile:
        line = logfile.readline()
        while line != '':
            if (line.find("Received") > 0 and line.find("'{}'".format(per_file)) > 0):
                raw_timestamp = line.split(' -')[0]
                logging.debug("Pulled {} from line: {}".format(raw_timestamp,line))
                (year,month,day),(hour,min,second),(msecond) = ((raw_timestamp.split(' ')[0].split('-')),
                                                                (raw_timestamp.split(' ')[1].split(',')[0].split(':')),
                                                                (raw_timestamp.split(',')[1]))
                return datetime.datetime(year,month,day,hour,min,second,msecond) + datetime.timedelta(seconds = constants.CLOCK_DRIFT[box])
    return -1 #did not find correct line

if __name__ == '__main__':
    import getopt
    import sys
    type=None
    network=None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:n:s:',
                                   ['type=', 'network=', 'subdir='])
    except getopt.GetoptError:
        logging.error('The system arguments are incorrect')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-t', '--type'):
            type = arg
        elif opt in ('-n', '--network'):
            network = arg
        elif opt in ('-s', '--subdir'):
            arg = arg if arg[-1] == '/' else arg + '/'
            RESULTS_SUBDIRECTORY = constants.RESULTS_DIR + arg
    logging.basicConfig(format=constants.LOG_FORMAT,level=10)
    measure_performance(RESULTS_SUBDIRECTORY,type,network)
    

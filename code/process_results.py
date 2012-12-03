import logging, math, os, datetime
import constants 

from Queue import Queue

def get_size(size):
    
    if size[-1] == 'G':
        return 1024
    return int(size[:-1])

def measure_performance(t='Online', network=constants.LAN):
    data_filename = constants.PLOT_DIR + "{}-{}_performance.plot".format(network,t)

    PROCESS_QUEUE = Queue()
    for test_dir in os.listdir(constants.RESULTS_DIR):
        num_receives = len(os.listdir(constants.RESULTS_DIR + test_dir)) - 1 #-1 for send
        PROCESS_QUEUE.put((num_receives,test_dir + '/'))
    PROCESS_LIST = []
    with open(data_filename, 'w') as graphfile:
        graphfile.write("reset\n")
        graphfile.write("set term postscript eps color enhanced \"Helvetica\" 25\n")
        graphfile.write("set ylabel \"Latency (s)\"\n")
        graphfile.write("set xlabel \"File Size (MB)\"\n")
        graphfile.write("set output \"{}-{}_performance.eps\"\n".format(network,t))
        graphfile.write("set title \"{} - {} Performance\"\n".format(network, t))
        i = 1
        while not PROCESS_QUEUE.empty():
            num_receives,test_dir = PROCESS_QUEUE.get()
            if i == 1:
               graphfile.write("plot ")
            else:
               graphfile.write(", \\\n");
            graphfile.write("\"data{}\" using 1:2 title \"{} clients\" with lines lw 3".format(i, 1 + num_receives))
            PROCESS_LIST.append(test_dir)
            i += 1
    logging.debug("Test directories to process ({}): {}".format(len(PROCESS_LIST),PROCESS_LIST))
    i = 1
    for test_dir in PROCESS_LIST:
        with open(constants.PLOT_DIR + 'data' + str(i), 'w') as graphfile:
            if t == 'Online':
                    append_online_data(test_dir, graphfile)
           #  else:
#                 append_offline_data(test_dir, graphfile)
        i += 1

def append_online_data(test_dir, graphfile):
    logging.info('###{}'.format(test_dir))
    receive_files = []
    for f in os.listdir(constants.RESULTS_DIR + test_dir):
        if f == 'sender.log':
            send_file = constants.RESULTS_DIR + test_dir + f
        else: # (box)_receive.log
            receive_files.append(constants.RESULTS_DIR + test_dir + f)

    logging.info("Opened send log and {} receive logs".format(len(receive_files)))
    for per_file in constants.PERFORMANCE_FILES:
#        logging.debug("Searching for 'send {}'".format(per_file))
        send_timestamp = search_send(per_file,send_file) #datetime, no update of clock drift
        if send_timestamp == -1:
            logging.warning("Couldn't find {} in send log: skipping".format(per_file))
            continue
#        logging.debug("Master sent {} at {}".format(per_file,send_timestamp.isoformat(' ')))
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
        graphfile.write("{}\t{}\n".format(get_size(per_file.split('_')[-1]), latency))

def search_send(per_file,send_file):
    with open(send_file,'r') as logfile:
        for line in logfile:
            if (line.find("Sending") >= 0 and line.find("{}".format(per_file)) > 0):
                raw_timestamp = line.split(' -')[0]
            #    logging.debug("Pulled {} from line: {}".format(raw_timestamp,line))
                (year,month,day),(hour,m,second),(msecond) = ((raw_timestamp.split(' ')[0].split('-')),
                                                                (raw_timestamp.split(' ')[1].split(',')[0].split(':')),
                                                                (raw_timestamp.split(',')[1]))
                return datetime.datetime(int(year), int(month), int(day),
                                         int(hour), int(m), int(second), int(msecond))
    return -1 #did not find correct line

def search_rcv(per_file,rcv_file):
    box = rcv_file.split('_')[0]
    with open(rcv_file, 'r') as logfile:
        for line in logfile:
            if (line.find("Received") >= 0 and line.find("{}".format(per_file)) > 0):
                raw_timestamp = line.split(' -')[0]
             #   logging.debug("Pulled {} from line: {}".format(raw_timestamp,line))
                (year,month,day),(hour,m,second),(msecond) = ((raw_timestamp.split(' ')[0].split('-')),
                                                                (raw_timestamp.split(' ')[1].split(',')[0].split(':')),
                                                                (raw_timestamp.split(',')[1]))
                return datetime.datetime(int(year), int(month), int(day),
                                         int(hour), int(m), int(second), int(msecond))
    return -1 #did not find correct line

if __name__ == '__main__':
    import getopt
    import sys
    t='Online'
    network=constants.LAN
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:n:',
                                   ['t=', 'network='])
    except getopt.GetoptError:
        logging.error('The system arguments are incorrect')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-t', '--t'):
            t = arg
        elif opt in ('-n', '--network'):
            network = arg
    logging.basicConfig(format=constants.LOG_FORMAT,level=1)
    if not os.path.isdir(constants.PLOT_DIR): os.mkdir(constants.PLOT_DIR)
    measure_performance(t,network)
    

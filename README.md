CIS-630 Project: DSync
======================

DSync is a tool to sync a file directory accross multiple systems,
similar to Dropbox and Google Drive, but without requiring an 
external server.

Main components
----------------

* broker.py
    This file contains the broker
* client.py
    This file contains the client
* db\_utils.py
    This file contains the interface
    allowing the client to connect to its
    local record (an SQLite database).
* constants.py
    This file contains necessary constants
    for running the entire system.
(Everything else is miscellany for testing purposes)

Setup & Usage
--------------
1. The following are required to set up this project:
    * python 2.7.X
    * pip

1. Install dependencies:
    * pip install -r requirements.txt

2. Start a broker:  `python broker.py`
    * This will start a broker on port 55555.
      If this port will not work for you, change PORT in constants.py

3. Start clients:  `python client.py -d <workspace_directory>`
    * There are several command line arguments
      that could be helpful:  
      -h --host     : broker host to connect to, default is localhost  
      -p --port     : broker port to connect to, default is 55555  
      -r --record   : record source to connect to  
      -d --dir      : local workspace directory  
      -v --verbose  : verbosity level  
4. Make changes to any workspace directory, and watch the magic happen!

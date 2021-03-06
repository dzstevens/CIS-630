#!/bin/bash
if [ $# -lt 2 ] ; then
    echo "USAGE: ./init_test (test_dir) (num clients)"
    exit 1
fi
echo "cleaning records"
rm client_records/*
rm -rf sender_dir
rm -rf receiver*_dir
if [ ! -d test_files ] ; then
    mkdir test_files
fi
python make_test_files.py
TESTDIR=$1
BOX=$USER
if [ ! -d RESULTS ] ; then
    mkdir RESULTS
fi
if [ -d RESULTS/$TESTDIR ] ; then
    rm -rf RESULTS/$TESTDIR 
fi
mkdir RESULTS/$TESTDIR
mkdir sender_dir
echo "starting sender"
python client.py -v 4 -h $HOST -d sender_dir -r sender.db -l RESULTS/$TESTDIR -t &
for (( N=1; N<$2; N++ ))
do
    echo "making dir: receiver${N}_dir"
    mkdir receiver_${N}_dir
    echo "starting receiver"
    python client.py -v 4 -h $HOST -d receiver_${N}_dir -r receiver${N}.db -b $BOX -l RESULTS/$TESTDIR -t &
done

#!/bin/bash
echo "cleaning records"
rm client_records/*
rm test_files/*
rm -rf sender_dir
rm -rf receiver*_dir
if [ ! -d test_files ] ; then
    mkdir test_files
fi
python make_test_files.py
TESTDIR=$1
BOX=$2
if [ ! -d RESULTS ] ; then
    mkdir RESULTS
fi
mkdir RESULTS/$TESTDIR
mkdir sender_dir
echo "starting sender"
python client.py -v 4 -h $HOST -d sender_dir -r sender.db -l RESULTS/$TESTDIR &
for (( N=1; N<$3; N++ ))
do
    echo "making dir: receiver${N}_dir"
    mkdir receiver_${N}_dir
    echo "starting receiver"
    python client.py -v 4 -h $HOST -d receiver_${N}_dir -r receiver${N}.db -b $BOX -l RESULTS/$TESTDIR &
done
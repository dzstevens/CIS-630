#!/bin/bash
echo "cleaning records"
rm client_records/*
rm -rf sender_dir
rm -rf receiver*_dir
TESTDIR=$1
BOX=$2
mkdir RESULTS/$TESTDIR
mkdir sender_dir
echo "starting sender"
python client.py -v 4 -h $HOST -d sender/ -r sender.db &
for (( N=0; N<$3; N++ ))
do
    echo "making dir: receiver${N}_dir"
    mkdir receiver${N}_dir
    echo "starting receiver"
    python client.py -v 4 -h $HOST -d receiver${N}_dir -r receiver${N}.db -b $BOX &
done

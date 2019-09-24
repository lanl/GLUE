#!/bin/bash
python $(dirname $BASH_SOURCE)/initTables.py --db testDB.db
python $(dirname $BASH_SOURCE)/alInterface.py --db testDB.db -t DUMMY_TAG_42 -m 3 -r 0 4 &
$(dirname $BASH_SOURCE)/sniffTest_serial
if [ $? -eq 0 ]
then
  sleep 2
  rm ./testDB.db
  exit 0
else
  sleep 2
  rm ./testDB.db
  echo "Serial Sniff Test Failed"
  exit 1
fi
#!/bin/bash
python $(dirname $BASH_SOURCE)/initTables.py -i $(dirname $BASH_SOURCE)/jsonFiles/sniffTest_serial.json
python $(dirname $BASH_SOURCE)/alInterface.py -i $(dirname $BASH_SOURCE)/jsonFiles/sniffTest_serial.json &
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
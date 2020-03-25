#!/bin/bash
python $(dirname $BASH_SOURCE)/initTables.py -i $(dirname $BASH_SOURCE)/jsonFiles/sniffTest_fortranBGK.json
python $(dirname $BASH_SOURCE)/alInterface.py -i $(dirname $BASH_SOURCE)/jsonFiles/sniffTest_fortranBGK.json &
$(dirname $BASH_SOURCE)/sniffTest_fortranBGK
if [ $? -eq 0 ]
then
  sleep 2
  rm ./foo.db
  exit 0
else
  sleep 2
  rm ./foo.db
  echo "Fortran Sniff Test Failed"
  exit 1
fi
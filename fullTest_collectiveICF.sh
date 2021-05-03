#!/bin/bash
#TODO: Want to flux this
python $(dirname $BASH_SOURCE)/initTables.py -i $(dirname $BASH_SOURCE)/jsonFiles/fullTest_collectiveICF.json
python $(dirname $BASH_SOURCE)/alInterface.py -i $(dirname $BASH_SOURCE)/jsonFiles/fullTest_collectiveICF.json &
$(dirname $BASH_SOURCE)/fullTest_collectiveICF
if [ $? -eq 0 ]
then
  sleep 2
  #rm ./testDB.db
  exit 0
else
  sleep 2
  #rm ./testDB.db
  echo "Full Test Failed"
  exit 1
fi

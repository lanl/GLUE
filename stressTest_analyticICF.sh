#!/bin/bash
python $(dirname $BASH_SOURCE)/initTables.py -i $(dirname $BASH_SOURCE)/jsonFiles/bgkStressTest_analyitic.json
python $(dirname $BASH_SOURCE)/alInterface.py -i $(dirname $BASH_SOURCE)/jsonFiles/bgkStressTest_analyitic.json &
$(dirname $BASH_SOURCE)/stressTest_analyticICF
if [ $? -eq 0 ]
then
  sleep 2
  rm ./testDB.db
  exit 0
else
  sleep 2
  rm ./testDB.db
  echo "Analytic Stress Test Failed"
  exit 1
fi
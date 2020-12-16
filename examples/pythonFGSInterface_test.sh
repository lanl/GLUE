#!/bin/bash
python $(dirname $BASH_SOURCE)/../initTables.py -i $(dirname $BASH_SOURCE)/../jsonFiles/sniffTest_pythonInterface.json
python $(dirname $BASH_SOURCE)/../alInterface.py -i $(dirname $BASH_SOURCE)/../jsonFiles/sniffTest_pythonInterface.json &
$(dirname $BASH_SOURCE)/temporaryPythonWrapper.sh $(dirname $BASH_SOURCE)/testPythonFGSRequest.py
if [ $? -eq 0 ]
then
  sleep 2
  #rm ./testDB.db
  exit 0
else
  sleep 2
  #rm ./testDB.db
  echo "Python FGS Interface Test  Failed"
  exit 1
fi

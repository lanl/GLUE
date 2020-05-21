#!/bin/bash
python $(dirname $BASH_SOURCE)/initTables.py -i $(dirname $BASH_SOURCE)/jsonFiles/sniffTest_mpi.json
python $(dirname $BASH_SOURCE)/alInterface.py -i $(dirname $BASH_SOURCE)/jsonFiles/sniffTest_mpi.json &
mpirun -n 4 $(dirname $BASH_SOURCE)/sniffTest_serial
if [ $? -eq 0 ]
then
  sleep 2
  rm ./testDB.db
  exit 0
else
  sleep 2
  rm ./testDB.db
  echo "MPI Sniff Test Failed"
  exit 1
fi
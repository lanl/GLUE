#!/bin/bash
python ../initTables.py foo test.db
../batchReqs foo test.db >> cOut.txt &
python ../alInterface.py foo test.db >> pyOut.txt &

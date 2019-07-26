#!/bin/bash
python ../initTables.py --tag foo --db test.db
../individualReqs foo test.db >> cOut.txt &
python ../alInterface.py --tag foo --db test.db >> pyOut.txt &

#!/bin/bash
python ../initTables.py --db test.db
../individualReqs foo test.db >> cOut.txt &
python ../alInterface.py --tag foo --db test.db -m 3 >> pyOut.txt &

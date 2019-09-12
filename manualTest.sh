#!/bin/bash
python ../initTables.py --db testDB.db
../glueCode_sniffTest  >> cOut.txt &
python ../alInterface.py --db testDB.db -t DUMMY_TAG_42 -m 3 >> pyOut.txt &

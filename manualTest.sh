#!/bin/bash
python $(dirname $BASH_SOURCE)/initTables.py --db testDB.db
python $(dirname $BASH_SOURCE)/alInterface.py --db testDB.db -t DUMMY_TAG_42 -m 3 &
$(dirname $BASH_SOURCE)/glueCode_sniffTest

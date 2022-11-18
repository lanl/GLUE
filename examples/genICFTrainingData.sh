#!/bin/bash
PYTHON_SCRIPT_DIR=${PYTHON_SCRIPT_DIR:=$(dirname $BASH_SOURCE)/../GLUECode_Service}
python3 "${PYTHON_SCRIPT_DIR}/initTables.py" -i "$(dirname "$BASH_SOURCE")/../jsonFiles/icfTraining_example.sh"
python3 "${PYTHON_SCRIPT_DIR}/genTrainingData.py" -i "$(dirname "$BASH_SOURCE")/../jsonFiles/icfTraining_example.sh" &

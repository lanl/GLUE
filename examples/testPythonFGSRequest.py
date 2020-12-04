from glueCodeTypes import BGKInputs, SolverCode
from submitFGSJob import submitFGSJobs
from alInterface import getAllGNDData
import os
import numpy as np
import time

if __name__ == "__main__":
    # Really convoluted way to get some example inputs
    pythonScriptDir = os.path.dirname(os.path.realpath(__file__))
    repoDir = os.path.dirname(pythonScriptDir)
    trainingDir = os.path.join(repoDir, "training")
    csv = os.path.join(trainingDir, "bgk.csv")
    trainingEntries = np.loadtxt(csv)
    testList = []
    for row in trainingEntries[:20]:
        testList.append(BGKInputs(Temperature=row[0], Density=[row[1], row[2], 0.0, 0.0], Charges=[row[3], row[4], 0.0, 0.0]))
    # Now submit them
    submitFGSJobs(testList, "testDB.db", "DUMMY_TAG_42", -1)
    # And then spin until they are done
    keepSpinning = True
    gndCnt = 0
    while keepSpinning:
        time.sleep(20)
        print("GNDCnt currently " + str(gndCnt))
        gndCnt = len(getAllGNDData("testDB.db", SolverCode.BGK))
        if gndCnt < 20:
            keepSpinning = True
    print("Ran to completion")